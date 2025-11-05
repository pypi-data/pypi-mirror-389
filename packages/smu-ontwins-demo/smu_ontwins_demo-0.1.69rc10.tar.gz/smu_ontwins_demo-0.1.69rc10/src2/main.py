from typing import Optional, List, Dict, Any
from gql import gql
from datetime import datetime, timedelta
from IPython.display import display, HTML, clear_output
import ipywidgets as widgets

from .auth import DeviceFlowAuth, DeviceAuthConfig
from .gql import init_gql, execute_gql, update_token, _xdomain

# 전역 상태
_SSO_SERVER: Optional[str] = None
_API_SERVER: Optional[str] = None
_auth: Optional[DeviceFlowAuth] = None

# -----------------------------------------------------------------
# [최적화] GQL 쿼리들을 상단으로 이동 및 EntitiesTree 재귀적으로 수정
# -----------------------------------------------------------------

ENTITY_BASE_FRAGMENT = gql("""
fragment EntityBaseParts on Entity {
  id
  properties
  system_properties
  createdAt
  updatedAt
  deletedAt
}
""")

# [최적화] relatedToMe를 재귀적으로 조회하는 프래그먼트
ENTITY_TREE_FRAGMENT = gql("""
fragment EntityTreeParts on Entity {
  ...EntityBaseParts
  relatedToMe {
    ...EntityBaseParts
    relatedToMe {
      ...EntityBaseParts
      relatedToMe {
        ...EntityBaseParts
        relatedToMe {
          ...EntityBaseParts 
          # 재귀 깊이는 GQL 서버 스키마 한도에 맞춰 조절
        }
      }
    }
  }
}
""")

# relatedToMe 필터가 없으므로 get_projects 용도로만 사용
ENTITY_QUERY_FOR_PROJECTS = gql("""
query Entity($id: Int!, $filter: EntityFilterInput) {
    entity(id: $id) {
        id
        relatedToMe(filter: $filter) {
            ...EntityBaseParts
        }
    }
}
""")

# [최적화] N+1 쿼리 방지를 위해 ENTITY_TREE_FRAGMENT 사용
ENTITIES_TREE_QUERY = gql("""
query EntitiesTree($ids: [Int!]!) {
  entitiesTree(ids: $ids) {
    ...EntityTreeParts
  }
}
""", fragments=[ENTITY_BASE_FRAGMENT, ENTITY_TREE_FRAGMENT])


FIND_ENTITIES_BY_TAGS_QUERY = gql("""
query FindEntitiesByTags($tags: [String!]!) {
    findEntitiesByTags(input: { tags: $tags }) {
        ...EntityBaseParts
    }
}
""", fragments=[ENTITY_BASE_FRAGMENT])


# -----------------------------------------------------------------
# 인증 및 GQL 초기화
# -----------------------------------------------------------------

def init_auth(sso_server: str, api_server: str):
    global _SSO_SERVER, _API_SERVER, _auth
    _SSO_SERVER = sso_server
    _API_SERVER = api_server

    if not _auth:
        _auth = DeviceFlowAuth(
            DeviceAuthConfig(
                api_server_url=_API_SERVER,
                sso_server_url=_SSO_SERVER,
                client_id="sso-client",
            ),
        )

    authenticated = _auth.refresh_if_needed()
    if not authenticated: 
        _auth.login() # open_browser=True (기본값)

    _set_auth_for_gql()

def _set_auth_for_gql():
    global _API_SERVER, _auth
    # [최적화] init_auth에서 이미 갱신했으므로 중복 갱신 호출 제거
    # _auth.refresh_if_needed() # <- 제거

    token = _auth.get_access_token()
    if not token:
        raise RuntimeError("인증 토큰이 없습니다. init_auth()가 실패했을 수 있습니다.")

    init_gql(_API_SERVER, token)

def _exec_with_auto_refresh(doc, variables: Optional[dict] = None):
    """execute_gql 래퍼: 인증 실패(Exception) 시 토큰 리프레시 후 1회 재시도."""
    if _auth is None:
        raise RuntimeError("Auth 모듈이 초기화되지 않았습니다. init_auth()를 먼저 호출하세요.")

    try:
        return execute_gql(doc, variables or {})
    except Exception as e:
        # (네트워크 에러, GQL 구문 에러 등도 여기서 잡히지만, 원본 로직 유지)

        # 1. 토큰 리프레시 시도
        new_token_set = _auth.refresh_if_needed()
        if not new_token_set:
            raise e from None # 리프레시 실패 시 원본 에러 발생

        new_access_token = new_token_set.get("access_token")
        if not new_access_token:
            raise e from None # 갱신은 됐는데 토큰이 없음

        # 2. [최적화] GQL 클라이언트를 재생성(init_gql)하지 않고 토큰만 업데이트
        # _set_auth_for_gql() # <- 제거 (getDomains 쿼리 방지)
        update_token(new_access_token)

        # 3. 쿼리 재시도
        return execute_gql(doc, variables or {})

# -----------------------------------------------------------------
# 데이터 조회 함수 (최적화)
# -----------------------------------------------------------------

def get_projects(domainId):
    """도메인 ID 하위의 프로젝트 목록만 조회 (트리 순회 없음)"""
    data = _exec_with_auto_refresh(
        ENTITY_QUERY_FOR_PROJECTS,
        {"id": domainId, "filter": { "system_properties_match": { "type": "project" }}}
    )
    return data.get("entity", {}).get("relatedToMe", [])


# [최적화] _fetch_entity (N+1 유발) 함수 제거
# [최적화] flatten_components_iter (중복 순회) 함수 제거

def get_all_components(root_id: int | str) -> list[dict]:
    """
    [최적화] root_id를 시작으로 모든 자손을 1번의 GQL 호출로 가져온 후,
    'component' 타입 엔티티만 필터링합니다. (N+1 문제 해결)
    """
    # 1. 단 1번의 GQL 호출로 전체 트리(또는 정의된 깊이까지)를 가져옴
    tree_data = _exec_with_auto_refresh(ENTITIES_TREE_QUERY, {"ids": [root_id]})
    root_nodes = (tree_data.get("entitiesTree") or [])

    # 2. 메모리 안에서 트리를 순회하며 'component' 타입 필터링
    out = []
    seen = set()
    stack = list(root_nodes)[::-1] # 스택에 엔티티 딕셔너리 저장

    while stack:
        node = stack.pop()
        if not isinstance(node, dict):
            continue

        nid = node.get("id")
        if nid is None or nid in seen:
            continue
        seen.add(nid)

        # 현재 노드가 component면 포함
        if (node.get("system_properties") or {}).get("type") == "component":
            out.append(node)

        # 자식들을 스택에 추가
        children = node.get("relatedToMe") or []
        if isinstance(children, list):
            # 자식 노드(dict)를 스택에 추가
            stack.extend(children)

    return out

def get_twin_data():
    """[최적화] get_all_components의 결과를 재사용하여 GQL 호출 최소화"""

    # 1. [최적화] 1번의 GQL 호출로 프로젝트 하위 모든 컴포넌트 로드
    project_id = globals().get("SELECTED_PROJECT_ID")
    if not project_id:
        raise ValueError("SELECTED_PROJECT_ID가 설정되지 않았습니다. select_project()를 먼저 실행하세요.")

    all_components = get_all_components(project_id)
    component_map = {comp["id"]: comp for comp in all_components}

    # 2. [최적화] 1번의 GQL 호출로 "rack" 태그가 붙은 엔티티 조회
    tags = ["rack"]
    tagged_racks = _exec_with_auto_refresh(FIND_ENTITIES_BY_TAGS_QUERY, {"tags": tags}).get("findEntitiesByTags", [])

    # 3. [최적화] 네트워크 호출 없이 메모리에서 필터링
    # (tagged_racks 중 all_components에 포함된 것만 추림)

    racks = []
    for rack in tagged_racks:
        if rack["id"] in component_map:
            # component_map에서 이미 전체 데이터가 로드된 엔티티를 가져옴
            racks.append(component_map[rack["id"]])

    # [최적화] EntitiesTree 재호출 로직 완전 제거
    # ids = [rack["id"] for rack in tagged_racks]
    # ids = [id for id in ids if id in {comp["id"] for comp in components}]
    # racks = _exec_with_auto_refresh(EntitiesTree, {"ids": ids}).get("entitiesTree", []) # <- 제거

    # 4. 정렬
    sorted_racks = sorted(
        racks,
        key=lambda d: (
            (d.get("properties", {}).get("worldPosition") or [0, 0])[0], 
            (d.get("properties", {}).get("worldPosition") or [0, 0])[1]
        ),
        # worldPosition이 없는 경우를 대비하여 기본값 [0, 0] 추가
    )
    return sorted_racks


# -----------------------------------------------------------------
# UI 헬퍼 함수 (수정 없음)
# -----------------------------------------------------------------

def to_kst_label(item: Dict[str, Any]) -> str:
    name = item.get("properties", {}).get("name", "(이름없음)")
    created_at = item.get("createdAt")
    if not created_at:
        return name

    try:
        # '...Z' → UTC로 파싱 후 +9시간
        dt_utc = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        dt_kst = dt_utc + timedelta(hours=9)
        # 초는 생략하고 분까지만
        stamp = dt_kst.strftime("%Y-%m-%d %H:%M")
        return f"{name} ({stamp})"
    except (ValueError, TypeError):
        return f"{name} (날짜오류)"


def build_selector_options(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # make_selector가 기대하는 형식으로 변환: {'label': ..., 'value': ...}
    return [{"label": to_kst_label(it), "value": it["id"]} for it in items]


def make_selector(
    options: List[Dict[str, Any]],
    var_name: str = "SELECTED_ID",
    title: str = "프로젝트를 선택하세요",
    allow_multiple: bool = False,
    default=None,
):
    labels = [o["label"] for o in options]
    values = [o["value"] for o in options]
    if not labels:
        display(HTML(f"<h4 style='margin:4px 0'>{title}</h4><div style='color:red;'>선택할 수 있는 항목이 없습니다.</div>"))
        return

    label_to_value = dict(zip(labels, values))

    title_html = widgets.HTML(f"<h4 style='margin:4px 0'>{title}</h4>")
    selector = (
        widgets.SelectMultiple(options=labels, rows=min(10, max(4, len(labels))))
        if allow_multiple else
        widgets.Dropdown(options=labels)
    )

    # default(값 id)를 라벨로 매핑
    if default is not None:
        try:
            if allow_multiple:
                want = default if isinstance(default, (list, tuple)) else [default]
                selector.value = tuple([lbl for lbl, val in label_to_value.items() if val in want])
            else:
                for lbl, val in label_to_value.items():
                    if val == default:
                        selector.value = lbl
                        break
        except Exception:
            pass # 기본값 설정 실패 시 무시

    confirm_btn = widgets.Button(description="확인", button_style="primary")
    cancel_btn  = widgets.Button(description="취소")
    out = widgets.Output()

    def on_confirm(_):
        if allow_multiple:
            chosen_labels = list(selector.value)  # 라벨들
            selected = [label_to_value[lbl] for lbl in chosen_labels]  # id 리스트
            label_text = ", ".join(chosen_labels) if chosen_labels else "(선택 없음)"
        else:
            chosen_label = selector.value                      # 라벨
            selected = label_to_value.get(chosen_label, None) # id
            label_text = chosen_label or "(선택 없음)"

        globals()[var_name] = selected

        with out:
            clear_output(wait=True)
            display(HTML(
                f"<div style='padding:8px;border:1px solid #e0e0e0;border-radius:8px;background:#f9f9f9;'>"
                f"<b>선택됨 (<code>{var_name}</code>)</b>: {label_text}"
                f"</div>"
            ))

    def on_cancel(_):
        with out:
            clear_output(wait=True)
            display(HTML("<div style='color:#999'>취소되었습니다.</div>"))

    confirm_btn.on_click(on_confirm)
    cancel_btn.on_click(on_cancel)
    display(widgets.VBox([title_html, selector, widgets.HBox([confirm_btn, cancel_btn]), out]))

def select_project():
    if not _xdomain:
        raise RuntimeError("GQL이 초기화되지 않았거나 도메인 ID를 가져오지 못했습니다.")

    projects = get_projects(_xdomain)
    opts = build_selector_options(projects)
    make_selector(opts, var_name="SELECTED_PROJECT_ID", title="프로젝트 선택")

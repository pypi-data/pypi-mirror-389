from __future__ import annotations
from typing import Any, Optional, Mapping

try:
    from gql import gql, Client
    from gql.transport.requests import RequestsHTTPTransport
except Exception as e:
    raise ImportError(
        "GraphQL HTTP 클라이언트가 없습니다. "
        "pip install 'smu-ontwins-demo[http]' 또는 'gql[requests]' 를 설치하세요."
    ) from e

# 전역 상태
_client: Optional[Client] = None
_xdomain: Optional[str] = None

# Query
GET_DOMAINS = gql("""
query GetDomains {
  getDomains {
    id
    properties
  }
}
""")

def _make_client(base_url: str, token: str, extra_headers: Optional[Mapping[str, str]] = None) -> Client:
    headers = {"Authorization": f"Bearer {token}"}
    if extra_headers:
        headers.update(extra_headers)
        
    transport = RequestsHTTPTransport(
        url=f"{base_url.rstrip('/')}/graphql",
        headers=headers,
        timeout=30,
    )
    # 스키마 페치 생략으로 빠르게
    return Client(transport=transport, fetch_schema_from_transport=False)

def init_gql(base_url: str, token: str) -> str:
    """부트스트랩(무 X-Domain) → 도메인 조회 → X-Domain 헤더만 추가.
    [최적화] 클라이언트를 2번 생성하지 않고, 기존 클라이언트 헤더를 수정.
    
    반환값: 선택된 X-Domain ID
    """
    global _client, _xdomain

    # 1) 부트스트랩 클라이언트로 도메인 조회 (이 클라이언트를 계속 사용)
    _client = _make_client(base_url, token)
    data = _client.execute(GET_DOMAINS) or {}
    domains = data.get("getDomains") or []

    if not domains:
        raise RuntimeError("getDomains 결과가 비어있습니다. X-Domain을 설정할 수 없습니다.")
    
    _xdomain = domains[0].get("id")
    if not _xdomain:
        raise RuntimeError("도메인 객체에 id가 없습니다.")

    # 2) [최적화] X-Domain 헤더를 기존 클라이언트에 추가
    #    _client = _make_client(...) # <- 이 코드를 제거
    _client.transport.headers["X-Domain"] = str(_xdomain)
    
    return _xdomain

def update_token(new_token: str):
    """[최적화] GQL 클라이언트 재생성 없이 토큰만 갱신합니다."""
    if _client is None:
        raise RuntimeError("GraphQL 클라이언트가 초기화되지 않았습니다. init_gql(...)을 먼저 호출하세요.")
    
    if not _client.transport or not hasattr(_client.transport, 'headers'):
        raise RuntimeError("GQL Transport가 헤더를 지원하지 않는 방식입니다.")
        
    _client.transport.headers["Authorization"] = f"Bearer {new_token}"

def execute_gql(doc, variables: Optional[dict] = None) -> Any:
    """초기화된 클라이언트로 쿼리/뮤테이션 실행"""
    if _client is None:
        raise RuntimeError("GraphQL 클라이언트가 초기화되지 않았습니다. init_gql(...)을 먼저 호출하세요.")
    return _client.execute(doc, variable_values=(variables or {}))

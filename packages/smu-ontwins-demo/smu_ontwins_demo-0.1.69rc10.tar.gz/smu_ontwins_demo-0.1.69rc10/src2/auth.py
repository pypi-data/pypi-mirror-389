from __future__ import annotations
import sys
import os
import time
import json
import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any
from urllib.parse import urljoin
from IPython.display import HTML, display

def with_expires_at(payload: Dict[str, Any], skew: int = 30) -> Dict[str, Any]:
    """토큰 payload에 'expires_at' (만료 타임스탬프) 필드를 추가합니다."""
    d = dict(payload)
    exp = d.get("expires_in")
    if isinstance(exp, (int, float)):
        d["expires_at"] = int(time.time()) + int(exp) - skew
    return d

# ----------------- 설정 -----------------
@dataclass
class DeviceAuthConfig:
    """Device Flow 인증에 필요한 설정값"""
    # 예: https://api.example.com
    api_server_url: str
    # 예: https://auth.example.com/realms/myrealm
    sso_server_url: str
    client_id: str
    scope: str = "openid profile email"
    # 폴링 주기/타임아웃(초)
    poll_interval: int = 5
    poll_timeout: int = 300

# ----------------- 클라이언트 -----------------
class DeviceFlowAuth:
    """
    Keycloak Device Authorization Flow 클라이언트.
    Colab 환경에 최적화되었으며, 토큰을 로컬 파일에 저장하여 커널 재시작 시에도 인증을 유지합니다.
    """
    _TOKEN_FILE = ".device_tokens.json"

    def __init__(self, cfg: DeviceAuthConfig):
        self.cfg = cfg
        self.http = requests.Session()
        self._well_known = self._discover()

    def _show_login_button(self, url: str) -> None:
        """Colab/Jupyter 환경에서 클릭 가능한 로그인 버튼을 표시합니다."""
        btn_html = f"""
        <div style="padding:14px;border:1px solid #ddd;border-radius:8px;margin:8px 0;font-family:sans-serif;">
          <div style="margin-bottom:10px;font-weight:600;font-size:15px;">🔐 로그인 필요</div>
          <a href="{url}" target="_blank" rel="noopener"
             style="display:inline-block;background:#1a73e8;color:#fff;padding:10px 16px;
                    border-radius:6px;text-decoration:none;font-weight:600;font-size:14px;">
             인증 페이지 열기
          </a>
          <div style="margin-top:8px;font-size:12px;color:#666;">
            새 탭이 열리지 않으면 위 버튼을 클릭하세요.
          </div>
        </div>
        """
        display(HTML(btn_html))

    def _discover(self) -> Dict[str, Any]:
        """OIDC Discovery 문서를 가져와 엔드포인트 정보를 로드합니다."""
        base = self.cfg.sso_server_url.rstrip("/") + "/"
        well_known_url = urljoin(base, ".well-known/openid-configuration")
        try:
            r = self.http.get(well_known_url, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            raise RuntimeError(f"OIDC Discovery 실패: {e}") from e

    def _format(self, res: dict) -> Dict[str, Any]:
        """백엔드 응답(camelCase)을 표준(snake_case) 토큰 형식으로 변환합니다."""
        if "accessToken" in res or "expiresIn" in res:
            return {
                "access_token": res.get("accessToken"),
                "refresh_token": res.get("refreshToken"),
                "id_token": res.get("idToken"),
                "token_type": res.get("tokenType", "Bearer"),
                "expires_in": res.get("expiresIn"),
            }
        return res

    def login(self) -> Dict[str, Any]:
        """
        새로운 Device Flow 로그인을 시작합니다.
        브라우저 탭을 열고, 사용자가 인증을 완료할 때까지 폴링합니다.
        """
        device_data = self._start_device_authorization()
        verify_url = device_data.get("verification_uri_complete") or device_data["verification_uri"]

        self._show_login_button(verify_url)

        token = self._poll_token(device_data)
        token = self._exchange_via_backend(token)
        token = with_expires_at(token)
        self._save_token(token)

        print("✅ 인증에 성공했습니다.")
        return token

    def get_access_token(self) -> Optional[str]:
        """
        저장된 access token을 반환합니다.
        만료되었으면 자동으로 갱신을 시도합니다.
        """
        ts = self.refresh_if_needed()
        return ts.get("access_token") if ts else None

    def get_session(self) -> Dict[str, Any]:
        """현재 인증 상태와 토큰 정보를 반환합니다."""
        ts = self._load_token()
        if ts:
            return {"status": "authenticated", "tokenSet": ts}
        else:
            return {"status": "unauthenticated", "tokenSet": None}

    def _start_device_authorization(self) -> Dict[str, Any]:
        """Device Flow 시작을 요청합니다."""
        device_ep = self._well_known.get("device_authorization_endpoint")
        if not device_ep:
            raise RuntimeError("OIDC Discovery에 'device_authorization_endpoint'가 없습니다.")

        r = self.http.post(device_ep, data={
            "client_id": self.cfg.client_id,
            "scope": self.cfg.scope,
        }, timeout=10)

        if not r.ok:
            raise RuntimeError(f"Device authorization 실패: {r.status_code} {r.text}")
        return r.json()

    def _poll_token(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """사용자가 인증을 완료할 때까지 토큰 엔드포인트를 폴링합니다."""
        token_ep = self._well_known["token_endpoint"]
        interval = int(device_data.get("interval", self.cfg.poll_interval))
        deadline = int(time.time()) + self.cfg.poll_timeout

        while True:
            if int(time.time()) > deadline:
                raise TimeoutError("사용자 인증 대기 시간 초과.")

            time.sleep(interval)

            r = self.http.post(token_ep, data={
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_data["device_code"],
                "client_id": self.cfg.client_id,
            }, timeout=10)

            if r.status_code == 200:
                return r.json()

            try:
                err = r.json().get("error")
            except Exception:
                err = None

            if err == "slow_down":
                interval += 2 # 폴링 간격 증가
            elif err in ("authorization_pending"):
                continue # 계속 시도
            elif err in ("access_denied", "expired_token"):
                raise RuntimeError(f"Device flow 중단: {err}")
            else:
                raise RuntimeError(f"Token polling 실패: {r.status_code} {r.text}")

    def _exchange_via_backend(self, ts: Dict[str, Any]) -> Dict[str, Any]:
        """Keycloak에서 받은 토큰을 백엔드 API 서버의 토큰과 교환합니다."""
        exchange_endpoint = f"{self.cfg.api_server_url.rstrip('/')}/auth/exchange-token"
        refresh = ts.get("refresh_token")
        if not refresh:
            raise RuntimeError("Device flow에서 refresh_token을 받지 못했습니다.")

        form = {
            "grant_type": "refresh_token",
            "client_id": self.cfg.client_id,
            "refresh_token": refresh,
        }

        r = self.http.post(
            exchange_endpoint,
            data=form,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        if not r.ok:
            raise RuntimeError(f"백엔드 토큰 교환 실패: {r.status_code} {r.text}")

        payload = r.json()
        out = payload.get("tokens") if isinstance(payload, dict) else payload
        return self._format(out)

    def refresh_if_needed(self) -> Optional[Dict[str, Any]]:
        """토큰 만료 시 자동으로 갱신을 시도합니다."""
        ts = self._load_token()
        if not ts:
            return None # 로그인 필요

        # 만료되지 않음 (현재 시간 < 만료 시간)
        if ts.get("expires_at", 0) > int(time.time()):
            return ts

        # 만료됨. 리프레시 시도
        refresh_token = ts.get("refresh_token")
        if not refresh_token:
            self._remove_token() # 리프레시 토큰 없으면 세션 삭제
            return None

        refresh_endpoint = f"{self.cfg.api_server_url.rstrip('/')}/auth/refresh"
        try:
            r = self.http.post(refresh_endpoint,
                              json={"refreshToken": refresh_token},
                              timeout=15)
            r.raise_for_status() # 4xx, 5xx 에러 발생
        except requests.RequestException:
            self._remove_token() # 갱신 실패 시 세션 삭제
            return None

        # 갱신 성공
        out = self._format(r.json())

        # 새 access_token과 expires_at만 업데이트 (refresh_token은 유지)
        new_ts = {
            **ts,
            "access_token": out.get("access_token"),
            "expires_at": with_expires_at(out).get("expires_at"),
        }
        self._save_token(new_ts)
        return new_ts

    # ----- 파일 저장/로드 (클래스 내부에 통합) -----

    def _save_token(self, ts: Dict[str, Any]) -> None:
        """토큰을 로컬 파일에 안전하게 저장합니다 (Atomic write)."""
        tmp_path = self._TOKEN_FILE + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(ts, f)
            os.replace(tmp_path, self._TOKEN_FILE)
        except Exception as e:
            print(f"Warning: 토큰 저장 실패: {e}", file=sys.stderr)

    def _load_token(self) -> Optional[Dict[str, Any]]:
        """로컬 파일에서 토큰을 로드합니다."""
        try:
            with open(self._TOKEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _remove_token(self) -> None:
        """저장된 토큰 파일을 삭제합니다."""
        try:
            os.remove(self._TOKEN_FILE)
        except FileNotFoundError:
            pass
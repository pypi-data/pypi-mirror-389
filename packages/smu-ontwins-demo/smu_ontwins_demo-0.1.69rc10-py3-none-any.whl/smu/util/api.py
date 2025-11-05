# TODO: uv sync에 추가
import requests, json
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import numpy as np
from datetime import datetime

def format_ts_of(obj):
    return {
        k: (pd.Timestamp(v).tz_localize('Asia/Seoul').isoformat(timespec="milliseconds")
            if isinstance(v, (pd.Timestamp, np.datetime64, datetime)) else v)
        for k, v in obj.items()
        }

def send_to(server: str,
            event: dict,
            *,
            username: str = "unknown",
            bucket: str = "demo",
            headers: dict | None = None,
            timeout: int = 10,
            max_workers: int | None = None,
            tags: dict,
            ) -> list[dict]:
    """
    이벤트를 모두 바디로 만든 뒤 스레드풀로 병렬 POST.
    응답 요약 리스트를 요청 순서대로 반환.
    """
    url = server.rstrip("/") + "/data/insert"
    event = format_ts_of(event)

    # 0) 보낼 바디들 수집 -------------------------------------------------------
    bodies: list[dict] = []

    for prddef in event.get("product_definitions", []):
        bodies.append({
            "bucket": bucket,
            "measurement": "product_definitions",
            "tags": {
                "product": prddef.get("품명"),
                **tags,
            },
            "fields": {
                "unit_price": prddef.get("가격"),
            },
            "timestamp": event.get("datetime"),
        })

    # customer_order
    co = event.get("customer_order")
    if co:
        bodies.append({
            "bucket": bucket,
            "measurement": "customer_order_event",
            "tags": {
                "product": co.get("product"),
                **tags,
            },
            "fields": {
                "received": event.get("consumable"),
                "quantity": co.get("quantity"),
                "cost": co.get("cost"),
            },
            "timestamp": event.get("datetime"),
        })

    # stock_status
    st = event.get("stock_status")
    if st:
        bodies.append({
            "bucket": bucket,
            "measurement": "stock_status_event",
            "tags": {
                "product": st.get("product"),
                **tags,
            },
            "fields": {
                "quantity": st.get("total_quantity"),
            },
            "timestamp": event.get("datetime"),
        })

    # economic_status
    est = event.get("economic_status")
    if est:
        bodies.append({
            "bucket": bucket,
            "measurement": "economic_status",
            "tags": {
                "month": est.get("month"),
                "day": est.get("day"),
                **tags,
            },
            "fields": {
                "so_cost": est.get("so_cost"),
                "co_profit": est.get("co_profit"),
            },
            "timestamp": event.get("datetime"),
        })

    tc = event.get("time_cost")
    if tc:
        bodies.append({
            "bucket": bucket,
            "measurement": "time_cost",
            "tags": {
                **tags,
            },
            "fields": {
                "pick_minutes": tc.get("pick_minutes"),
            },
            "timestamp": event.get("datetime"),
        })

    for stc in event.get("stock_cost", []):
    # stc = event.get("stock_cost")
    # if stc:
        bodies.append({
            "bucket": bucket,
            "measurement": "stock_cost",
            "tags": {
                "product": stc.get("품명"),
                **tags,
            },
            "fields": {
                "stock_cost": stc.get("수량"),
            },
            "timestamp": event.get("datetime"),
        })

    # rack_status (여러 건)
    for rack in event.get("rack_status", []):
        rack = format_ts_of(rack)
        pos = rack.get("position")
        bodies.append({
            "bucket": bucket,
            "measurement": "rack_status_event",
            "tags": {
                "rack": rack.get("rack"),
                "level": rack.get("level"),
                "cell": rack.get("cell"),
                "product": rack.get("product"),
                **tags,
            },
            "fields": {
                "quantity": rack.get("qty"),
                "utilization": rack.get("utilization"),
                "mean_ts": rack.get("mean_ts"),
                "position": json.dumps(pos) if pos else None,
                "color": rack.get("color"),
            },
            "timestamp": event.get("datetime"),
        })

    if not bodies:
        return []

    # 1) 세션/어댑터 세팅 (커넥션 풀 + 재시도) -----------------------------------
    s = requests.Session()
    if headers:
        s.headers.update(headers)

    # 동시 연결 수만큼 풀 사이즈 확보
    workers = max_workers or min(8, len(bodies))
    adapter = HTTPAdapter(
        pool_connections=workers,
        pool_maxsize=workers,
        max_retries=Retry(
            total=2,
            backoff_factor=0.2,
            status_forcelist=[502, 503, 504],
            allowed_methods=["POST"],
        ),
    )
    s.mount("http://", adapter)
    s.mount("https://", adapter)

    # 2) 병렬 POST --------------------------------------------------------------
    def _post(idx: int, body: dict):
        r = s.post(url, json=body, timeout=timeout)
        try:
            payload = r.json()
        except Exception:
            payload = r.text
        return idx, {
            "ok": r.ok,
            "status": r.status_code,
            "request": body,
            "response": payload,
        }

    results = [None] * len(bodies)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_post, i, b) for i, b in enumerate(bodies)]
        for f in as_completed(futs):
            i, item = f.result()
            results[i] = item

    return results




def _build_bodies_from_event(event: dict, *, bucket: str, tags: dict) -> list[dict]:
    """단일 event에서 원래 send_to와 동일하게 bodies 생성"""
    event = format_ts_of(event)
    bodies: list[dict] = []

    for prddef in event.get("product_definitions", []):
        bodies.append({
            "bucket": bucket,
            "measurement": "product_definitions",
            "tags": {"product": prddef.get("품명"), **tags},
            "fields": {"unit_price": prddef.get("가격")},
            "timestamp": event.get("datetime"),
        })

    co = event.get("customer_order")
    if co:
        bodies.append({
            "bucket": bucket,
            "measurement": "customer_order_event",
            "tags": {"product": co.get("product"), **tags},
            "fields": {
                "received": event.get("consumable"),
                "quantity": co.get("quantity"),
                "cost": co.get("cost"),
            },
            "timestamp": event.get("datetime"),
        })

    st = event.get("stock_status")
    if st:
        bodies.append({
            "bucket": bucket,
            "measurement": "stock_status_event",
            "tags": {"product": st.get("product"), **tags},
            "fields": {"quantity": st.get("total_quantity")},
            "timestamp": event.get("datetime"),
        })

    est = event.get("economic_status")
    if est:
        bodies.append({
            "bucket": bucket,
            "measurement": "economic_status",
            "tags": {"month": est.get("month"), "day": est.get("day"), **tags},
            "fields": {"so_cost": est.get("so_cost"), "co_profit": est.get("co_profit")},
            "timestamp": event.get("datetime"),
        })

    tc = event.get("time_cost")
    if tc:
        bodies.append({
            "bucket": bucket,
            "measurement": "time_cost",
            "tags": {**tags},
            "fields": {"pick_minutes": tc.get("pick_minutes")},
            "timestamp": event.get("datetime"),
        })

    for stc in event.get("stock_cost", []):
        bodies.append({
            "bucket": bucket,
            "measurement": "stock_cost",
            "tags": {"product": stc.get("품명"), **tags},
            "fields": {"stock_cost": stc.get("수량")},
            "timestamp": event.get("datetime"),
        })

    for rack in event.get("rack_status", []):
        rack = format_ts_of(rack)
        pos = rack.get("position")
        bodies.append({
            "bucket": bucket,
            "measurement": "rack_status_event",
            "tags": {
                "rack": rack.get("rack"),
                "level": rack.get("level"),
                "cell": rack.get("cell"),
                "product": rack.get("product"),
                **tags,
            },
            "fields": {
                "quantity": rack.get("qty"),
                "utilization": rack.get("utilization"),
                "mean_ts": rack.get("mean_ts"),
                "position": json.dumps(pos) if pos else None,
                "color": rack.get("color"),
            },
            "timestamp": event.get("datetime"),
        })

    return bodies


def send_to_multi(
    server: str,
    event_multi: list[dict],
    *,
    username: str = "unknown",
    bucket: str = "demo",
    headers: dict | None = None,
    timeout: int = 10,
    max_workers: int | None = None,
    tags: dict,
) -> list[list[dict]]:
    """
    여러 event를 받아 각 event에서 만든 bodies를 모두 병렬 POST.
    반환은 이벤트별 결과 리스트(list[list[dict]])로, 각 이벤트 내 요청 순서를 보존.
    """
    url = server.rstrip("/") + "/data/insert"

    # 0) 이벤트별 bodies 구성
    bodies_per_event: list[list[dict]] = []
    for ev in event_multi:
        bodies_per_event.append(_build_bodies_from_event(ev, bucket=bucket, tags=tags))

    # 전송할 전체 바디를 (event_idx, body_idx, body)로 평탄화
    flat_jobs: list[tuple[int, int, dict]] = []
    for ei, bodies in enumerate(bodies_per_event):
        for bi, body in enumerate(bodies):
            flat_jobs.append((ei, bi, body))

    # 아무 것도 없으면 즉시 반환
    if not flat_jobs:
        return [[] for _ in bodies_per_event]

    # 1) 세션/어댑터 세팅 (원본과 동일한 느낌으로)
    s = requests.Session()
    if headers:
        s.headers.update(headers)

    # 동시 연결 수
    total_jobs = len(flat_jobs)
    workers = max_workers or min(64, max(8, total_jobs))

    adapter = HTTPAdapter(
        pool_connections=workers,
        pool_maxsize=workers,
        max_retries=Retry(
            total=2,
            backoff_factor=0.2,
            status_forcelist=[502, 503, 504],
            allowed_methods=["POST"],
        ),
    )
    s.mount("http://", adapter)
    s.mount("https://", adapter)

    # 2) 병렬 POST
    results_per_event: list[list[dict | None]] = [
        [None] * len(bodies) for bodies in bodies_per_event
    ]

    def _post(ei: int, bi: int, body: dict):
        r = s.post(url, json=body, timeout=timeout)
        try:
            payload = r.json()
        except Exception:
            payload = r.text
        return ei, bi, {
            "ok": r.ok,
            "status": r.status_code,
            "request": body,
            "response": payload,
        }

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_post, ei, bi, body) for (ei, bi, body) in flat_jobs]
        for f in as_completed(futs):
            ei, bi, item = f.result()
            results_per_event[ei][bi] = item

    # 타입 정리: None 없게 보장
    return [list(map(lambda x: x if x is not None else {}, ev_res)) for ev_res in results_per_event]

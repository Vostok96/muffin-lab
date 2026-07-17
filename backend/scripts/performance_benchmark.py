"""Performance benchmark for MUFFIN API endpoints.

Validates p95 targets:
  - Read endpoints: < 150 ms
  - Write endpoints: < 300 ms
"""

import json
import os
import statistics
import time
from typing import Any
from urllib.request import Request, urlopen

BASE_URL = os.getenv("MUFFIN_API_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
PASSWORD = os.getenv("DEV_SEED_PASSWORD", "")
WARMUP_ITERATIONS = 5
BENCHMARK_ITERATIONS = 30
P95_READ_MS = 150
P95_WRITE_MS = 300


class EndpointResult:
    def __init__(self, name: str, read: bool = True):
        self.name = name
        self.read = read
        self.latencies: list[float] = []


def data_request(path: str, method: str = "GET", payload: dict | None = None, token: str | None = None) -> Any:
    """Return parsed JSON data, without timing."""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = urlopen(Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method), timeout=10)
    content = response.read()
    return json.loads(content.decode("utf-8")) if content else None


def timed_request(path: str, method: str = "GET", payload: dict | None = None, token: str | None = None) -> float:
    """Return elapsed milliseconds for a single request."""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    start = time.perf_counter()
    urlopen(Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method), timeout=10)
    return (time.perf_counter() - start) * 1000


def login(username: str) -> str:
    return data_request("/auth/login", method="POST", payload={"username": username, "password": PASSWORD})["access_token"]


def benchmark(name: str, fn: callable, read: bool = True) -> EndpointResult:
    result = EndpointResult(name, read)
    for _ in range(WARMUP_ITERATIONS):
        fn()
    for _ in range(BENCHMARK_ITERATIONS):
        result.latencies.append(fn())
    return result


def print_result(result: EndpointResult) -> bool:
    p95 = sorted(result.latencies)[int(len(result.latencies) * 0.95) - 1]
    avg = statistics.mean(result.latencies)
    target = P95_READ_MS if result.read else P95_WRITE_MS
    passed = p95 < target
    status = "PASS" if passed else "FAIL"
    print(f"  {status:6s}  {result.name:<50s}  avg={avg:7.1f}ms  p95={p95:7.1f}ms  target=<{target}ms")
    return passed


def main() -> None:
    if len(PASSWORD) < 12:
        raise RuntimeError("DEV_SEED_PASSWORD must be set.")

    print("MUFFIN API Performance Benchmark")
    print(f"  iterations={BENCHMARK_ITERATIONS}  p95_read=<{P95_READ_MS}ms  p95_write=<{P95_WRITE_MS}ms")
    print()

    admin_token = login("dev-admin")
    processor_token = login("dev-processor")

    results: list[EndpointResult] = []

    def add(name: str, fn: callable, read: bool = True) -> None:
        results.append(benchmark(name, fn, read))

    # --- read benchmarks (p95 < 150 ms) ---

    add("GET  /health", lambda: timed_request("/health"))

    add("POST /auth/login", lambda: timed_request("/auth/login", method="POST", payload={"username": "dev-admin", "password": PASSWORD}), read=False)

    add("GET  /auth/me", lambda: timed_request("/auth/me", token=admin_token))

    add("GET  /patients (list)", lambda: timed_request("/patients?page_size=10", token=admin_token))

    add("GET  /orders (list)", lambda: timed_request("/orders?page_size=10", token=admin_token))

    add("GET  /catalogs/exams", lambda: timed_request("/catalogs/exams?page_size=10", token=admin_token))

    add("GET  /catalogs/organisms", lambda: timed_request("/catalogs/organisms?page_size=10", token=admin_token))

    add("GET  /catalogs/antibiotics", lambda: timed_request("/catalogs/antibiotics?page_size=10", token=admin_token))

    # --- write benchmarks (p95 < 300 ms) ---

    organism_counter = [0]

    def create_organism():
        organism_counter[0] += 1
        code = f"BENCH-{int(time.time() * 1000) % 100000:05d}-{organism_counter[0]:04d}"
        return timed_request(
            "/catalogs/organisms",
            method="POST",
            payload={"code": code, "name": f"Benchmark organism {organism_counter[0]}"},
            token=admin_token,
        )

    add("POST /catalogs/organisms", create_organism, read=False)

    print_counter = [0]

    def create_print_job():
        print_counter[0] += 1
        order = data_request("/orders?search=DEV-ORDER-0001", token=admin_token)["data"][0]
        detail = data_request(f"/orders/{order['id']}", token=admin_token)
        item_id = detail["items"][0]["id"]
        return timed_request(
            "/print-jobs",
            method="POST",
            payload={"order_item_id": item_id, "kind": "BARCODE"},
            token=admin_token,
        )

    add("POST /print-jobs", create_print_job, read=False)

    # First resolve order item and result for clinical writes
    order_data = data_request("/orders?search=DEV-ORDER-0001", token=processor_token)["data"][0]
    detail = data_request(f"/orders/{order_data['id']}", token=processor_token)
    item_id = detail["items"][0]["id"]
    result_data = data_request(f"/order-items/{item_id}/result", token=processor_token)
    result_id = result_data["id"]

    def get_result_form():
        return timed_request(f"/order-items/{item_id}/result", token=processor_token)

    add("GET  /result (form)", get_result_form)

    def update_isolate():
        isolates = data_request(f"/results/{result_id}/isolates", token=processor_token)
        if isolates:
            return timed_request(
                f"/results/{result_id}/isolates/{isolates[0]['id']}",
                method="PATCH",
                payload={"phenotype": f"Benchmark phenotype {int(time.time())}"},
                token=processor_token,
            )
        return 0

    add("PATCH /isolates", update_isolate, read=False)

    notif_counter = [0]

    def create_notification():
        notif_counter[0] += 1
        return timed_request(
            "/notifications",
            method="POST",
            payload={
                "order_item_id": item_id,
                "type": "CUSTOM",
                "recipient": f"bench-{notif_counter[0]}@example.invalid",
                "payload": {"benchmark_iteration": notif_counter[0]},
            },
            token=processor_token,
        )

    add("POST /notifications", create_notification, read=False)

    # --- summary ---

    print()
    all_passed = all(print_result(r) for r in results)
    print()

    read_results = [r for r in results if r.read]
    write_results = [r for r in results if not r.read]

    read_passed = sum(1 for r in read_results if sorted(r.latencies)[int(len(r.latencies) * 0.95) - 1] < P95_READ_MS)
    write_passed = sum(1 for r in write_results if sorted(r.latencies)[int(len(r.latencies) * 0.95) - 1] < P95_WRITE_MS)

    print(f"  Read:  {read_passed}/{len(read_results)} passed   (p95 target < {P95_READ_MS}ms)")
    print(f"  Write: {write_passed}/{len(write_results)} passed   (p95 target < {P95_WRITE_MS}ms)")

    if all_passed:
        print("\nPerformance benchmark passed.")
    else:
        print("\nPerformance benchmark FAILED — some endpoints exceed latency targets.")
        raise SystemExit(1)


if __name__ == "__main__":
    main()

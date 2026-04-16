import json
import sys
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from urllib.request import HTTPCookieProcessor, build_opener

BASE_URL = "http://127.0.0.1:8000/api/v1"
DEFAULT_EMAIL = "pilot.admin@example.com"
DEFAULT_PASSWORD = "ChangeMeNow!123"


def request_json(
    opener: urllib.request.OpenerDirector,
    *,
    method: str,
    path: str,
    payload: dict | None = None,
) -> tuple[int, dict | list | str]:
    url = f"{BASE_URL}{path}"
    data = None
    headers = {}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url=url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with opener.open(request) as response:
            body = response.read().decode("utf-8")
            if not body:
                return response.status, ""
            return response.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed = json.loads(body) if body else ""
        except json.JSONDecodeError:
            parsed = body
        return exc.code, parsed
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach backend at {url}: {exc}") from exc
    except http.client.RemoteDisconnected as exc:
        raise RuntimeError(f"Remote disconnected during {method} {path}") from exc


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def step(name: str) -> None:
    print(f"[verify] {name}")


def main() -> None:
    cookie_jar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookie_jar))

    step("GET /health")
    status, body = request_json(opener, method="GET", path="/health")
    expect(status == 200, f"/health returned {status}: {body}")
    expect(body == {"status": "ok"}, f"/health returned unexpected payload: {body}")

    step("GET /meta/enums")
    status, body = request_json(opener, method="GET", path="/meta/enums")
    expect(status == 200, f"/meta/enums returned {status}: {body}")
    expect(isinstance(body, dict), "/meta/enums did not return a JSON object.")
    expect("analysis_statuses" in body, "/meta/enums missing analysis_statuses.")
    expect("review_statuses" in body, "/meta/enums missing review_statuses.")

    step("GET /auth/me before login")
    status, body = request_json(opener, method="GET", path="/auth/me")
    expect(status == 401, f"/auth/me should return 401 before login, got {status}: {body}")

    step("POST /auth/login")
    status, body = request_json(
        opener,
        method="POST",
        path="/auth/login",
        payload={
            "email": DEFAULT_EMAIL,
            "password": DEFAULT_PASSWORD,
        },
    )
    expect(status == 200, f"/auth/login returned {status}: {body}")
    expect(isinstance(body, dict), "/auth/login did not return a JSON object.")
    expect(body.get("email") == DEFAULT_EMAIL, f"/auth/login returned unexpected email: {body}")
    expect(body.get("role") == "ADMIN", f"/auth/login returned unexpected role: {body}")

    step("GET /auth/me after login")
    status, body = request_json(opener, method="GET", path="/auth/me")
    expect(status == 200, f"/auth/me returned {status} after login: {body}")
    expect(isinstance(body, dict), "/auth/me did not return a JSON object after login.")
    expect(body.get("email") == DEFAULT_EMAIL, f"/auth/me returned unexpected email: {body}")
    expect(body.get("role") == "ADMIN", f"/auth/me returned unexpected role: {body}")

    step("GET /dashboard")
    status, body = request_json(opener, method="GET", path="/dashboard")
    expect(status == 200, f"/dashboard returned {status}: {body}")

    step("GET /observability/summary")
    status, body = request_json(opener, method="GET", path="/observability/summary")
    expect(status == 200, f"/observability/summary returned {status}: {body}")

    step("POST /auth/logout")
    status, body = request_json(opener, method="POST", path="/auth/logout", payload={})
    expect(status == 204, f"/auth/logout returned {status}: {body}")

    step("GET /auth/me after logout")
    status, body = request_json(opener, method="GET", path="/auth/me")
    expect(status == 401, f"/auth/me should return 401 after logout, got {status}: {body}")

    print("Pilot environment verification passed.")


if __name__ == "__main__":
    import http.client

    try:
        main()
    except Exception as exc:
        print(f"Pilot environment verification failed: {exc}", file=sys.stderr)
        sys.exit(1)
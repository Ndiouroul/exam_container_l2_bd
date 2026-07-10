import os
import httpx

BOOKS_SERVICE_URL = os.getenv("BOOKS_SERVICE_URL", "http://books-service:8001")
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://users-service:8002")


class ServiceUnavailable(Exception):
    pass


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def get_book(book_id: int, token: str) -> dict | None:
    try:
        resp = httpx.get(f"{BOOKS_SERVICE_URL}/books/{book_id}", headers=_auth_headers(token), timeout=5.0)
    except httpx.RequestError as exc:
        raise ServiceUnavailable(f"books-service injoignable: {exc}") from exc
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def get_user(user_id: int, token: str) -> dict | None:
    try:
        resp = httpx.get(f"{USERS_SERVICE_URL}/users/{user_id}", headers=_auth_headers(token), timeout=5.0)
    except httpx.RequestError as exc:
        raise ServiceUnavailable(f"users-service injoignable: {exc}") from exc
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def adjust_book_availability(book_id: int, delta: int, token: str) -> dict:
    try:
        resp = httpx.patch(
            f"{BOOKS_SERVICE_URL}/books/{book_id}/availability",
            json={"delta": delta},
            headers=_auth_headers(token),
            timeout=5.0,
        )
    except httpx.RequestError as exc:
        raise ServiceUnavailable(f"books-service injoignable: {exc}") from exc
    return {"status_code": resp.status_code, "body": resp.json() if resp.content else None}

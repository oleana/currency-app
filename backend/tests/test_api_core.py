from fastapi.testclient import TestClient
import httpx
import pytest

from backend import main


client = TestClient(main.app)


@pytest.fixture(autouse=True)
def clear_cache() -> None:
    main._cache.clear()


def _sample_rates_payload(country: str, base: str) -> dict:
    return {
        "country": country,
        "bank": "Test Bank",
        "base": base,
        "date": "2026-09-10",
        "rates": [{"code": "RUB", "name": "Российский рубль", "nominal": 1, "rate": 1.0, "previous": None}],
        "source": "https://example.com",
    }


def test_rates_ru_returns_data_from_russia_fetcher(monkeypatch) -> None:
    async def fake_fetch_russia():
        return _sample_rates_payload("ru", "RUB")

    monkeypatch.setattr(main, "fetch_russia", fake_fetch_russia)

    response = client.get("/api/rates/ru")

    assert response.status_code == 200
    payload = response.json()
    assert payload["country"] == "ru"
    assert payload["base"] == "RUB"


def test_rates_us_calls_er_api_with_expected_args(monkeypatch) -> None:
    calls = []

    async def fake_fetch_er_api(base: str, country: str, bank: str, source: str):
        calls.append((base, country, bank, source))
        return _sample_rates_payload(country, base)

    monkeypatch.setattr(main, "fetch_er_api", fake_fetch_er_api)

    response = client.get("/api/rates/us")

    assert response.status_code == 200
    assert response.json()["base"] == "USD"
    assert calls == [
        ("USD", "us", "Банки США (агрегированные рыночные курсы)", "https://www.exchangerate-api.com")
    ]


def test_rates_cn_calls_er_api_with_expected_args(monkeypatch) -> None:
    calls = []

    async def fake_fetch_er_api(base: str, country: str, bank: str, source: str):
        calls.append((base, country, bank, source))
        return _sample_rates_payload(country, base)

    monkeypatch.setattr(main, "fetch_er_api", fake_fetch_er_api)

    response = client.get("/api/rates/cn")

    assert response.status_code == 200
    assert response.json()["base"] == "CNY"
    assert calls == [
        ("CNY", "cn", "Банки Китая (агрегированные рыночные курсы)", "https://www.exchangerate-api.com")
    ]


def test_rates_unknown_country_returns_404() -> None:
    response = client.get("/api/rates/de")
    assert response.status_code == 404
    assert "Неизвестная страна" in response.json()["detail"]


def test_convert_returns_result_and_uses_cache(monkeypatch) -> None:
    fetch_calls = []

    async def fake_fetch_json(_client, _url: str):
        fetch_calls.append(_url)
        return {
            "result": "success",
            "time_last_update_utc": "Thu, 10 Sep 2026 00:00:00 +0000",
            "rates": {"RUB": 90.0, "EUR": 0.85},
        }

    monkeypatch.setattr(main, "_fetch_json", fake_fetch_json)

    first = client.get("/api/convert?amount=2&frm=USD&to=RUB")
    second = client.get("/api/convert?amount=3&frm=USD&to=RUB")

    assert first.status_code == 200
    assert first.json()["result"] == 180.0
    assert second.status_code == 200
    assert second.json()["result"] == 270.0
    assert len(fetch_calls) == 1


def test_convert_returns_404_for_unknown_target_currency(monkeypatch) -> None:
    async def fake_fetch_json(_client, _url: str):
        return {
            "result": "success",
            "time_last_update_utc": "Thu, 10 Sep 2026 00:00:00 +0000",
            "rates": {"RUB": 90.0},
        }

    monkeypatch.setattr(main, "_fetch_json", fake_fetch_json)

    response = client.get("/api/convert?amount=10&frm=USD&to=ZZZ")
    assert response.status_code == 404
    assert "не найдена" in response.json()["detail"].lower()


def test_convert_returns_502_if_upstream_failed(monkeypatch) -> None:
    async def fake_fetch_json(_client, _url: str):
        return {"result": "error"}

    monkeypatch.setattr(main, "_fetch_json", fake_fetch_json)

    response = client.get("/api/convert?amount=10&frm=USD&to=RUB")
    assert response.status_code == 502


@pytest.mark.parametrize("failure", ["timeout", "connection", "http_status"])
def test_convert_returns_502_for_upstream_http_errors(monkeypatch, failure: str) -> None:
    async def fake_fetch_json(_client, url: str):
        request = httpx.Request("GET", url)
        if failure == "timeout":
            raise httpx.ReadTimeout("Upstream timed out", request=request)
        if failure == "connection":
            raise httpx.ConnectError("Connection failed", request=request)
        response = httpx.Response(503, request=request)
        response.raise_for_status()

    monkeypatch.setattr(main, "_fetch_json", fake_fetch_json)

    response = client.get("/api/convert?amount=10&frm=USD&to=RUB")

    assert response.status_code == 502
    assert response.json() == {"detail": "Не удалось получить курс от внешнего API"}
    assert "conv:USD" not in main._cache

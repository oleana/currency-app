"""
Currency Rates API — курсы валют банков России, США и Китая.

Источники (публичные API, без ключей):
  * Россия — Центральный банк РФ (официальные курсы, JSON-зеркало cbr-xml-daily.ru,
    резервный источник — официальный XML www.cbr.ru)
  * США    — open.er-api.com, базовая валюта USD (агрегированные банковские/рыночные курсы)
  * Китай  — open.er-api.com, базовая валюта CNY

Запуск:  uvicorn main:app --reload --port 8000
"""

import math
import time
import xml.etree.ElementTree as ET
from typing import Annotated, Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Currency Rates API",
    description="Курсы валют центральных банков России, США и Китая (реальные данные из публичных API)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CACHE_TTL = 30 * 60  # 30 минут
_cache: dict[str, tuple[float, dict[str, Any]]] = {}

# Валюты, которые показываем для каждой страны
POPULAR = ["USD", "EUR", "CNY", "RUB", "GBP", "JPY", "CHF", "KZT", "TRY", "INR", "HKD", "AED"]

CURRENCY_NAMES = {
    "USD": "Доллар США", "EUR": "Евро", "CNY": "Китайский юань",
    "RUB": "Российский рубль", "GBP": "Фунт стерлингов", "JPY": "Японская иена",
    "CHF": "Швейцарский франк", "KZT": "Казахстанский тенге", "TRY": "Турецкая лира",
    "INR": "Индийская рупия", "HKD": "Гонконгский доллар", "AED": "Дирхам ОАЭ",
}


def _cache_get(key: str) -> dict[str, Any] | None:
    entry = _cache.get(key)
    if entry and time.time() - entry[0] < CACHE_TTL:
        return entry[1]
    return None


def _cache_set(key: str, value: dict[str, Any]) -> None:
    _cache[key] = (time.time(), value)


async def _fetch_json(client: httpx.AsyncClient, url: str) -> Any:
    resp = await client.get(url, timeout=15, follow_redirects=True)
    resp.raise_for_status()
    return resp.json()


# ----------------------------------------------------------------------------
# Россия — Центральный банк РФ
# ----------------------------------------------------------------------------
async def fetch_russia() -> dict[str, Any]:
    cached = _cache_get("ru")
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        try:
            data = await _fetch_json(client, "https://www.cbr-xml-daily.ru/daily_json.js")
            date = data.get("Date", "")[:10]
            valutes = data.get("Valute", {})
            rates = [
                {
                    "code": code,
                    "name": CURRENCY_NAMES.get(code, v.get("Name", code)),
                    "nominal": v.get("Nominal", 1),
                    "rate": round(v["Value"] / v.get("Nominal", 1), 4),
                    "previous": round(v.get("Previous", v["Value"]) / v.get("Nominal", 1), 4),
                }
                for code, v in valutes.items()
                if code in POPULAR
            ]
        except Exception:
            # Резерв: официальный XML ЦБ РФ
            resp = await client.get(
                "https://www.cbr.ru/scripts/XML_daily.asp", timeout=15, follow_redirects=True
            )
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            date = root.attrib.get("Date", "")
            rates = []
            for v in root.findall("Valute"):
                code = v.findtext("CharCode", "")
                if code not in POPULAR:
                    continue
                nominal = int(v.findtext("Nominal", "1"))
                value = float(v.findtext("Value", "0").replace(",", "."))
                rates.append({
                    "code": code,
                    "name": CURRENCY_NAMES.get(code, v.findtext("Name", code)),
                    "nominal": nominal,
                    "rate": round(value / nominal, 4),
                    "previous": None,
                })

    rates.sort(key=lambda r: POPULAR.index(r["code"]))
    result = {
        "country": "ru",
        "bank": "Центральный банк Российской Федерации",
        "base": "RUB",
        "date": date,
        "rates": rates,
        "source": "https://www.cbr.ru",
    }
    _cache_set("ru", result)
    return result


# ----------------------------------------------------------------------------
# США и Китай — open.er-api.com (публичный API, без ключа)
# ----------------------------------------------------------------------------
async def fetch_er_api(base: str, country: str, bank: str, source: str) -> dict[str, Any]:
    cached = _cache_get(country)
    if cached:
        return cached

    async with httpx.AsyncClient() as client:
        data = await _fetch_json(client, f"https://open.er-api.com/v6/latest/{base}")

    if data.get("result") != "success":
        raise HTTPException(502, f"Внешний API вернул ошибку для {base}")

    all_rates = data["rates"]
    date = data.get("time_last_update_utc", "")
    rates = []
    for code in POPULAR:
        if code == base or code not in all_rates:
            continue
        # all_rates[code] = сколько CODE за 1 BASE → инвертируем:
        # сколько BASE стоит 1 единица CODE
        rates.append({
            "code": code,
            "name": CURRENCY_NAMES.get(code, code),
            "nominal": 1,
            "rate": round(1 / all_rates[code], 4),
            "previous": None,
        })

    result = {
        "country": country,
        "bank": bank,
        "base": base,
        "date": date,
        "rates": rates,
        "source": source,
    }
    _cache_set(country, result)
    return result


# ----------------------------------------------------------------------------
# Эндпоинты
# ----------------------------------------------------------------------------
@app.get("/api/rates/{country}")
async def get_rates(country: str):
    """Курсы валют для страны: ru | us | cn"""
    try:
        if country == "ru":
            return await fetch_russia()
        if country == "us":
            return await fetch_er_api(
                "USD", "us", "Банки США (агрегированные рыночные курсы)",
                "https://www.exchangerate-api.com",
            )
        if country == "cn":
            return await fetch_er_api(
                "CNY", "cn", "Банки Китая (агрегированные рыночные курсы)",
                "https://www.exchangerate-api.com",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(502, f"Не удалось получить данные: {exc}")
    raise HTTPException(404, "Неизвестная страна. Доступно: ru, us, cn")


@app.get("/api/convert")
async def convert(
    amount: Annotated[float, Query(ge=0, allow_inf_nan=False)], frm: str, to: str
):
    """Конвертация валют по актуальному курсу (через open.er-api.com)."""
    frm, to = frm.upper(), to.upper()
    cached = _cache_get(f"conv:{frm}")
    if cached is None:
        try:
            async with httpx.AsyncClient() as client:
                data = await _fetch_json(client, f"https://open.er-api.com/v6/latest/{frm}")
        except httpx.HTTPError as exc:
            raise HTTPException(502, "Не удалось получить курс от внешнего API") from exc
        if data.get("result") != "success":
            raise HTTPException(502, "Внешний API вернул ошибку")
        cached = data
        _cache_set(f"conv:{frm}", data)

    rate = cached["rates"].get(to)
    if rate is None:
        raise HTTPException(404, f"Валюта {to} не найдена")
    result = amount * rate
    if not math.isfinite(result):
        raise HTTPException(422, "Сумма слишком велика для конвертации")
    return {
        "amount": amount,
        "from": frm,
        "to": to,
        "rate": rate,
        "result": round(result, 4),
        "date": cached.get("time_last_update_utc", ""),
    }


@app.get("/api/health")
async def health():
    return {"status": "ok"}

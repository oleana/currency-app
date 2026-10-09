# Курсы валют — Россия · США · Китай

Мобильное веб-приложение для проверки стоимости валют в банках России, США и Китая.
Реальные данные из публичных API, без ключей и регистрации.

## Архитектура

```
currency-app/
├── backend/         FastAPI (Python) — агрегирует публичные API курсов валют
│   ├── main.py
│   └── requirements.txt
└── frontend/        React + Vite, mobile-first интерфейс
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── api.js
        ├── styles.css
        └── components/
            ├── CountryTabs.jsx    вкладки Россия / США / Китай
            ├── RatesList.jsx      карточки курсов с динамикой ▲▼
            └── Converter.jsx      конвертер валют
```

## Источники данных

| Страна | Источник | API |
|---|---|---|
| 🇷🇺 Россия | Центральный банк РФ (официальные курсы) | `cbr-xml-daily.ru/daily_json.js`, резерв — `cbr.ru/scripts/XML_daily.asp` |
| 🇺🇸 США | Агрегированные банковские курсы, база USD | `open.er-api.com/v6/latest/USD` |
| 🇨🇳 Китай | Агрегированные банковские курсы, база CNY | `open.er-api.com/v6/latest/CNY` |

Все API публичные и бесплатные, ключи не требуются. Ответы кешируются
на бекенде 30 минут, чтобы не превышать лимиты.

## Запуск

### 1. Бекенд (Python 3.10+)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Проверка: http://localhost:8000/api/rates/ru
Swagger-документация: http://localhost:8000/docs

### 2. Фронтенд (Node 18+)

```bash
cd frontend
npm install
npm run dev
```

Откройте http://localhost:5173 — Vite проксирует запросы `/api/*` на бекенд
(настроено в `vite.config.js`).

## API бекенда

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/rates/{country}` | Курсы для страны: `ru`, `us`, `cn` |
| GET | `/api/convert?amount=100&frm=USD&to=RUB` | Конвертация по актуальному курсу |
| GET | `/api/health` | Проверка работоспособности |

Пример ответа `/api/rates/ru`:

```json
{
  "country": "ru",
  "bank": "Центральный банк Российской Федерации",
  "base": "RUB",
  "date": "2026-07-10",
  "rates": [
    {"code": "USD", "name": "Доллар США", "nominal": 1, "rate": 76.19, "previous": 76.45}
  ],
  "source": "https://www.cbr.ru"
}
```

## Возможности

- Вкладки по странам с курсами относительно национальной валюты (RUB / USD / CNY)
- Динамика курса к предыдущему дню (▲▼) — для данных ЦБ РФ
- Конвертер валют по актуальному курсу
- Кеширование на бекенде (30 мин) и резервный источник для ЦБ РФ
- Mobile-first интерфейс: тёмная тема, крупные карточки, безопасные зоны iOS

## Продакшен-сборка фронтенда

```bash
cd frontend
npm run build       # результат в frontend/dist
```

Статику из `dist/` можно раздавать любым веб-сервером; адрес бекенда
задаётся переменной `VITE_API_URL` при сборке, например:

```bash
VITE_API_URL=https://api.example.com npm run build
```

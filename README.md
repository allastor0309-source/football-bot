# ⚽ Football Predictor Bot

Telegram-бот для аналізу футбольних матчів на основі статистики.
Підтримує два API одночасно + демо-режим без ключів.

---

## 🚀 Деплой на Railway — покроково

### Крок 1 — Завантажте код на GitHub

1. Зайдіть **github.com** → "New repository" → назва `football-bot`
2. Натисніть "uploading an existing file"
3. Перетягніть всі 5 файлів: `bot.py`, `analyzer.py`, `requirements.txt`, `Procfile`, `runtime.txt`
4. "Commit changes"

### Крок 2 — Створіть проект на Railway

1. Зайдіть **railway.com** → "New Project"
2. "Deploy from GitHub repo" → підключіть GitHub → оберіть `football-bot`
3. Railway автоматично встановить залежності

### Крок 3 — Додайте змінні середовища

Variables → "+ New Variable":

| Змінна            | Значення              | Обов'язково |
|-------------------|-----------------------|-------------|
| TELEGRAM_TOKEN    | токен від @BotFather  | ✅ Так      |
| APISPORTS_KEY     | ключ api-football.com | Ні          |
| FOOTBALLDATA_KEY  | ключ football-data.org| Ні          |

### Крок 4 — Deploy

Settings → Start Command: `python bot.py` → Deploy
Logs покажуть: `🤖 Бот запущено!`

✅ Безкоштовно 500 год/місяць

---

## 🔑 Отримання API ключів

**api-football.com** — 100 запитів/день безкоштовно
1. api-football.com → "Get your API key" → реєстрація
2. Dashboard → "My account" → скопіювати API Key

**football-data.org** — 10 запитів/хв безкоштовно
1. football-data.org → "Get API key" → вказати email
2. Ключ приходить на пошту за 1 хвилину

---

## 🧮 Математична модель (Пуассон)

xG_home = scored_home×0.55 + conceded_away×0.45 + home_bonus
xG_away = scored_away×0.55 + conceded_home×0.45
P(i,j)  = Poisson(xG_h, i) × Poisson(xG_a, j)

Підсумовуємо 81 варіант рахунку (0:0 → 8:8) → отримуємо 1X2, Over 2.5, BTTS.

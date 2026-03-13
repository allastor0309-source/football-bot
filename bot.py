import os
import math
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from analyzer import FootballAnalyzer

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

analyzer = FootballAnalyzer()

# ─── КОМАНДИ ───────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚽ *Футбольний аналітик*\n\n"
        "Аналізую статистику попередніх матчів і розраховую ймовірність голів "
        "за математичною моделлю (розподіл Пуассона) — як Forebet.\n\n"
        "📋 *Команди:*\n"
        "/match — аналіз матчу (вибір ліги та команд)\n"
        "/today — матчі сьогодні з прогнозами\n"
        "/leagues — список доступних ліг\n"
        "/help — допомога"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔍 *Як користуватись ботом*\n\n"
        "1️⃣ Введіть /match\n"
        "2️⃣ Оберіть лігу\n"
        "3️⃣ Оберіть домашню команду\n"
        "4️⃣ Оберіть гостьову команду\n"
        "5️⃣ Отримайте детальний аналіз\n\n"
        "📊 *Що аналізується:*\n"
        "• Форма останніх 6 матчів\n"
        "• Середні голи (забиті / пропущені)\n"
        "• Очна статистика H2H\n"
        "• Очікувані голи (xG) за Пуассоном\n"
        "• Ймовірність: 1X2, тотал 2.5, BTTS\n\n"
        "⚙️ *Джерело даних:* API-Football (football-data.org)\n"
        "Встановіть ваш ключ у файлі .env"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def match_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    leagues = analyzer.get_leagues()
    keyboard = []
    for i in range(0, len(leagues), 2):
        row = [InlineKeyboardButton(leagues[i]["name"], callback_data=f"league_{leagues[i]['id']}")]
        if i + 1 < len(leagues):
            row.append(InlineKeyboardButton(leagues[i+1]["name"], callback_data=f"league_{leagues[i+1]['id']}"))
        keyboard.append(row)
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🏆 Оберіть лігу:", reply_markup=reply_markup)


async def today_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Завантажую матчі на сьогодні...")
    matches = analyzer.get_today_matches()
    if not matches:
        await update.message.reply_text("📭 Сьогодні матчів не знайдено.")
        return

    keyboard = []
    for m in matches[:10]:
        label = f"{m['home']} vs {m['away']} ({m['time']})"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"analyze_{m['home_id']}_{m['away_id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"📅 *Матчі сьогодні* ({len(matches)} знайдено):\nОберіть для аналізу:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def leagues_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    leagues = analyzer.get_leagues()
    text = "🏆 *Доступні ліги:*\n\n"
    for l in leagues:
        text += f"• {l['name']} ({l['country']})\n"
    await update.message.reply_text(text, parse_mode="Markdown")


# ─── CALLBACKS ─────────────────────────────────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("league_"):
        league_id = data.split("_")[1]
        teams = analyzer.get_teams(league_id)
        context.user_data["league_id"] = league_id
        context.user_data["teams"] = teams

        keyboard = []
        for i in range(0, min(len(teams), 20), 2):
            row = [InlineKeyboardButton(teams[i]["name"], callback_data=f"home_{teams[i]['id']}")]
            if i + 1 < len(teams):
                row.append(InlineKeyboardButton(teams[i+1]["name"], callback_data=f"home_{teams[i+1]['id']}"))
            keyboard.append(row)

        await query.edit_message_text(
            "🏠 Оберіть *домашню* команду:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("home_"):
        home_id = data.split("_")[1]
        teams = context.user_data.get("teams", [])
        home_team = next((t for t in teams if str(t["id"]) == home_id), None)
        context.user_data["home_id"] = home_id
        context.user_data["home_name"] = home_team["name"] if home_team else "Home"

        keyboard = []
        filtered = [t for t in teams if str(t["id"]) != home_id]
        for i in range(0, min(len(filtered), 20), 2):
            row = [InlineKeyboardButton(filtered[i]["name"], callback_data=f"away_{filtered[i]['id']}")]
            if i + 1 < len(filtered):
                row.append(InlineKeyboardButton(filtered[i+1]["name"], callback_data=f"away_{filtered[i+1]['id']}"))
            keyboard.append(row)

        await query.edit_message_text(
            f"✈️ Домашня: *{context.user_data['home_name']}*\nОберіть *гостьову* команду:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("away_") or data.startswith("analyze_"):
        if data.startswith("away_"):
            away_id = data.split("_")[1]
            home_id = context.user_data.get("home_id")
        else:
            parts = data.split("_")
            home_id, away_id = parts[1], parts[2]

        await query.edit_message_text("⏳ Аналізую статистику матчу...")

        try:
            result = analyzer.analyze_match(home_id, away_id)
            text = format_analysis(result)
            keyboard = [[
                InlineKeyboardButton("🔄 Новий матч", callback_data="new_match"),
                InlineKeyboardButton("📊 Детальніше ↗", callback_data=f"detail_{home_id}_{away_id}")
            ]]
            await query.edit_message_text(
                text, parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            await query.edit_message_text(
                "❌ Помилка аналізу. Перевірте API ключ або спробуйте іншу пару команд.\n"
                f"Деталі: {str(e)}"
            )

    elif data == "new_match":
        await match_cmd_from_callback(query)

    elif data.startswith("detail_"):
        parts = data.split("_")
        home_id, away_id = parts[1], parts[2]
        result = analyzer.analyze_match(home_id, away_id)
        text = format_detailed(result)
        await query.edit_message_text(text, parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад", callback_data=f"analyze_{home_id}_{away_id}")
            ]]))


async def match_cmd_from_callback(query):
    leagues = analyzer.get_leagues()
    keyboard = []
    for i in range(0, len(leagues), 2):
        row = [InlineKeyboardButton(leagues[i]["name"], callback_data=f"league_{leagues[i]['id']}")]
        if i + 1 < len(leagues):
            row.append(InlineKeyboardButton(leagues[i+1]["name"], callback_data=f"league_{leagues[i+1]['id']}"))
        keyboard.append(row)
    await query.edit_message_text("🏆 Оберіть лігу:", reply_markup=InlineKeyboardMarkup(keyboard))


# ─── ФОРМАТУВАННЯ ──────────────────────────────────────────────────────────────

def stars(pct: float) -> str:
    if pct >= 70: return "🟢"
    if pct >= 50: return "🟡"
    return "🔴"

def bar(pct: float, width: int = 10) -> str:
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)

def format_analysis(r: dict) -> str:
    h, a = r["home"], r["away"]
    p = r["predictions"]
    xg = r["xg"]
    form_h = r["form_home"]
    form_a = r["form_away"]

    winner_pct = max(p["home_win"], p["draw"], p["away_win"])
    if p["home_win"] == winner_pct:
        winner = f"1 ({h})"
    elif p["away_win"] == winner_pct:
        winner = f"2 ({a})"
    else:
        winner = "X (Нічия)"

    text = (
        f"⚽ *{h}* vs *{a}*\n"
        f"{'─' * 28}\n\n"
        f"📈 *Форма*\n"
        f"{h}: `{form_h}`\n"
        f"{a}: `{form_a}`\n\n"
        f"🎯 *Очікувані голи (xG)*\n"
        f"{h}: `{xg['home']:.2f}` | {a}: `{xg['away']:.2f}`\n"
        f"Загальний тотал: `{xg['total']:.2f}`\n\n"
        f"📊 *Прогноз результату*\n"
        f"1 ({h[:10]}): {stars(p['home_win'])} `{p['home_win']}%` {bar(p['home_win'])}\n"
        f"X  Нічия:       {stars(p['draw'])} `{p['draw']}%` {bar(p['draw'])}\n"
        f"2 ({a[:10]}): {stars(p['away_win'])} `{p['away_win']}%` {bar(p['away_win'])}\n\n"
        f"⚡ *Ринки*\n"
        f"Тотал більше 2.5: `{p['over25']}%` {stars(p['over25'])}\n"
        f"Тотал більше 1.5: `{p['over15']}%` {stars(p['over15'])}\n"
        f"Обидві забивають: `{p['btts']}%` {stars(p['btts'])}\n\n"
        f"✅ *Основний прогноз:* {winner} ({winner_pct}%)\n"
    )

    if r.get("avg"):
        avg = r["avg"]
        text += (
            f"\n📋 *Середня статистика*\n"
            f"{h}: {avg['home_scored']:.1f} г/м | {avg['home_conceded']:.1f} пр/м\n"
            f"{a}: {avg['away_scored']:.1f} г/м | {avg['away_conceded']:.1f} пр/м\n"
        )

    return text


def format_detailed(r: dict) -> str:
    h, a = r["home"], r["away"]
    h2h = r.get("h2h", [])

    text = f"🔬 *Детальний аналіз: {h} vs {a}*\n{'─'*28}\n\n"

    if h2h:
        text += "📖 *Очна статистика (H2H)*\n"
        hw = sum(1 for m in h2h if m.get("winner") == "home")
        aw = sum(1 for m in h2h if m.get("winner") == "away")
        draws = len(h2h) - hw - aw
        text += f"Зустрічей: {len(h2h)} | {h[:8]}: {hw}W | Нічиїх: {draws} | {a[:8]}: {aw}W\n\n"
        text += "Останні матчі:\n"
        for m in h2h[:5]:
            text += f"• {m.get('date','?')} {m.get('home','')} {m.get('score','')} {m.get('away','')}\n"
    else:
        text += "📖 H2H статистика недоступна\n"

    text += (
        f"\n⚙️ *Методологія (Пуассон)*\n"
        f"Розраховуємо xG як зважене середнє атаки домашньої команди та захисту гостьової. "
        f"Потім для кожного рахунку (0:0 → 8:8) обчислюємо P(i,j) = e^-λ₁·λ₁ⁱ/i! × e^-λ₂·λ₂ʲ/j! "
        f"та сумуємо для 1X2.\n"
    )
    return text


# ─── ЗАПУСК ────────────────────────────────────────────────────────────────────

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("❌ Встановіть TELEGRAM_TOKEN у файлі .env")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("match", match_cmd))
    app.add_handler(CommandHandler("today", today_cmd))
    app.add_handler(CommandHandler("leagues", leagues_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 Бот запущено!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

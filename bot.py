import os
import math
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
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
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Надіслати мій часовий пояс", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    text = (
        "⚽ *Футбольний аналітик*\n\n"
        "Аналізую статистику попередніх матчів і розраховую ймовірність голів "
        "за математичною моделлю (розподіл Пуассона) — як Forebet.\n\n"
        "📋 *Команди:*\n"
        "/anomaly — 🚨 аномальні матчі зараз\n"
        "/live — матчі які зараз грають\n"
        "/match — аналіз матчу (вибір ліги та команд)\n"
        "/today — матчі сьогодні з прогнозами\n"
        "/leagues — список доступних ліг\n"
        "/help — допомога\n\n"
        "📍 Поділіться геолокацією щоб бачити час матчів у *вашому* часовому поясі:"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔍 *Як користуватись ботом*\n\n"
        "1️⃣ Введіть /match\n"
        "2️⃣ Оберіть лігу\n"
        "3️⃣ Оберіть домашню команду\n"
        "4️⃣ Оберіть гостьову команду\n"
        "5️⃣ Отримайте детальний аналіз\n\n"
        "🔴 */live* — матчі що грають зараз (з рахунком та часом матчу)\n"
        "📅 */today* — всі матчі на сьогодні\n\n"
        "📊 *Що аналізується:*\n"
        "• Форма останніх 6 матчів\n"
        "• Середні голи (забиті / пропущені)\n"
        "• Очна статистика H2H\n"
        "• Очікувані голи (xG) за Пуассоном\n"
        "• Ймовірність: 1X2, тотал 2.5, BTTS\n\n"
        "🕐 *Часовий пояс:* надішліть /timezone щоб встановити свій час\n\n"
        "⚙️ *Джерело даних:* API-Football або football-data.org"
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
    tz_offset = context.user_data.get("tz_offset", 0)
    await update.message.reply_text("⏳ Завантажую матчі на сьогодні...")
    matches = analyzer.get_today_matches()
    if not matches:
        await update.message.reply_text("📭 Сьогодні матчів не знайдено.")
        return

    sign = "+" if tz_offset >= 0 else ""
    keyboard = []
    for m in matches[:10]:
        local_time = convert_time_to_user(m["time"], tz_offset)
        label = f"{m['home']} vs {m['away']} ({local_time})"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"analyze_{m['home_id']}_{m['away_id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"📅 *Матчі сьогодні* ({len(matches)} знайдено)\n"
        f"🕐 Час вашого поясу UTC{sign}{tz_offset} · /timezone щоб змінити\n"
        f"Оберіть для аналізу:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )


async def leagues_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    leagues = analyzer.get_leagues()
    text = "🏆 *Доступні ліги:*\n\n"
    for l in leagues:
        text += f"• {l['name']} ({l['country']})\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def live_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz_offset = context.user_data.get("tz_offset", 0)
    await update.message.reply_text("🔴 Шукаю матчі що зараз грають...")
    matches = analyzer.get_live_matches()

    if not matches:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📅 Матчі сьогодні", callback_data="show_today"),
            InlineKeyboardButton("🔄 Оновити", callback_data="refresh_live"),
        ]])
        await update.message.reply_text(
            "😴 Зараз немає матчів в прямому ефірі.\n"
            "Спробуйте /today щоб побачити розклад.",
            reply_markup=keyboard
        )
        return

    text = f"🔴 *Зараз грають* — {len(matches)} матч(ів)\n"
    text += f"🕐 Ваш час: {format_user_time(tz_offset)}\n"
    text += "─" * 28 + "\n\n"

    for m in matches:
        score_h = m.get("score_home", 0)
        score_a = m.get("score_away", 0)
        minute  = m.get("minute", "?")
        league  = m.get("league", "")
        status  = m.get("status", "LIVE")

        status_icon = "🔴" if status in ("1H", "2H", "LIVE") else "⏸" if status == "HT" else "🟡"
        min_str = f"{minute}'" if isinstance(minute, int) else str(minute)

        text += (
            f"{status_icon} *{m['home']}* {score_h}:{score_a} *{m['away']}*\n"
            f"   ⏱ {min_str} | {league}\n\n"
        )

    keyboard = []
    for m in matches[:8]:
        label = f"📊 {m['home'][:12]} vs {m['away'][:12]}"
        keyboard.append([InlineKeyboardButton(
            label, callback_data=f"analyze_{m['home_id']}_{m['away_id']}"
        )])
    keyboard.append([
        InlineKeyboardButton("🔄 Оновити", callback_data="refresh_live"),
        InlineKeyboardButton("📅 Сьогодні", callback_data="show_today"),
    ])

    await update.message.reply_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def anomaly_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tz_offset = context.user_data.get("tz_offset", 0)
    msg = await update.message.reply_text(
        "🔍 Сканую live матчі на аномалії...\n"
        "Шукаю: забивні команди без голів, xG >> фактичного тотал, топ-форма при порожньому матчі"
    )
    anomalies = analyzer.find_anomalies()

    if not anomalies:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Повторити скан", callback_data="rescan_anomaly"),
            InlineKeyboardButton("🔴 Live матчі", callback_data="refresh_live"),
        ]])
        await msg.edit_text(
            "✅ Аномалій не знайдено.\n"
            "Всі live матчі відповідають статистичним очікуванням.\n\n"
            "Спробуйте через 10-15 хвилин.",
            reply_markup=keyboard
        )
        return

    text = f"🚨 *Аномальні матчі* — {len(anomalies)} знайдено\n"
    text += f"🕐 {format_user_time(tz_offset)}\n"
    text += "─" * 28 + "\n\n"

    for i, a in enumerate(anomalies[:5], 1):
        bar_filled = round(a["anomaly_score"] / 10)
        bar_str    = "🟥" * bar_filled + "⬜" * (10 - bar_filled)
        text += (
            f"*{i}. {a['home']} {a['score']} {a['away']}*\n"
            f"⏱ {a['minute']}' | {a['league']}\n"
            f"💥 Сила аномалії: {bar_str} {a['anomaly_score']}/99\n"
            f"🎯 Ймовірність голу (залишок): *{a['prob_goal']}%*\n"
        )
        for sig in a["signals"]:
            text += f"  › {sig}\n"
        text += "\n"

    keyboard = []
    for a in anomalies[:5]:
        keyboard.append([InlineKeyboardButton(
            f"📊 Аналіз: {a['home'][:10]} vs {a['away'][:10]}",
            callback_data=f"analyze_{a['home_id']}_{a['away_id']}"
        )])
    keyboard.append([
        InlineKeyboardButton("🔄 Оновити", callback_data="rescan_anomaly"),
        InlineKeyboardButton("🔴 Всі live", callback_data="refresh_live"),
    ])

    await msg.edit_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Надіслати геолокацію", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.message.reply_text(
        "📍 Натисніть кнопку нижче щоб поділитись геолокацією.\n"
        "Бот визначить ваш часовий пояс і показуватиме час матчів у вашому місцевому часі.",
        reply_markup=keyboard
    )


async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отримує геолокацію і визначає UTC offset за довготою"""
    loc = update.message.location
    lng = loc.longitude
    # Груба оцінка UTC offset за довготою (±30 хв точність, без DST)
    tz_offset = round(lng / 15)
    tz_offset = max(-12, min(14, tz_offset))
    context.user_data["tz_offset"] = tz_offset

    sign = "+" if tz_offset >= 0 else ""
    await update.message.reply_text(
        f"✅ Часовий пояс встановлено: *UTC{sign}{tz_offset}*\n"
        f"Поточний час у вас: *{format_user_time(tz_offset)}*\n\n"
        f"Тепер /live та /today показуватимуть час у вашому місцевому часі.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )


def format_user_time(tz_offset: int) -> str:
    now_utc = datetime.now(timezone.utc)
    user_time = now_utc + timedelta(hours=tz_offset)
    sign = "+" if tz_offset >= 0 else ""
    return f"{user_time.strftime('%H:%M')} (UTC{sign}{tz_offset})"


def convert_time_to_user(utc_time_str: str, tz_offset: int) -> str:
    """Конвертує рядок часу HH:MM з UTC в локальний час користувача"""
    try:
        h, m = map(int, utc_time_str.split(":"))
        total = h * 60 + m + tz_offset * 60
        total %= 24 * 60
        return f"{total // 60:02d}:{total % 60:02d}"
    except Exception:
        return utc_time_str


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

    elif data == "rescan_anomaly":
        anomalies = analyzer.find_anomalies()
        tz_offset = context.user_data.get("tz_offset", 0)
        if not anomalies:
            await query.edit_message_text(
                "✅ Аномалій не знайдено — всі матчі в нормі.\nСпробуйте через 10-15 хвилин.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔄 Повторити", callback_data="rescan_anomaly"),
                    InlineKeyboardButton("🔴 Live", callback_data="refresh_live"),
                ]])
            )
            return
        text = f"🚨 *Аномальні матчі* — {len(anomalies)} знайдено\n"
        text += f"🕐 {format_user_time(tz_offset)}\n" + "─" * 28 + "\n\n"
        for i, a in enumerate(anomalies[:5], 1):
            bar_filled = round(a["anomaly_score"] / 10)
            bar_str = "🟥" * bar_filled + "⬜" * (10 - bar_filled)
            text += (
                f"*{i}. {a['home']} {a['score']} {a['away']}*\n"
                f"⏱ {a['minute']}' | {a['league']}\n"
                f"💥 Сила: {bar_str} {a['anomaly_score']}/99\n"
                f"🎯 Ймовірність голу: *{a['prob_goal']}%*\n"
            )
            for sig in a["signals"]:
                text += f"  › {sig}\n"
            text += "\n"
        keyboard = []
        for a in anomalies[:5]:
            keyboard.append([InlineKeyboardButton(
                f"📊 {a['home'][:10]} vs {a['away'][:10]}",
                callback_data=f"analyze_{a['home_id']}_{a['away_id']}"
            )])
        keyboard.append([
            InlineKeyboardButton("🔄 Оновити", callback_data="rescan_anomaly"),
            InlineKeyboardButton("🔴 Всі live", callback_data="refresh_live"),
        ])
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "refresh_live":
        tz_offset = context.user_data.get("tz_offset", 0)
        matches = analyzer.get_live_matches()
        if not matches:
            await query.edit_message_text(
                "😴 Зараз немає матчів в прямому ефірі.\n"
                "Спробуйте /today щоб побачити розклад.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📅 Матчі сьогодні", callback_data="show_today"),
                    InlineKeyboardButton("🔄 Оновити", callback_data="refresh_live"),
                ]])
            )
            return

        text = f"🔴 *Зараз грають* — {len(matches)} матч(ів)\n"
        text += f"🕐 Ваш час: {format_user_time(tz_offset)}\n"
        text += "─" * 28 + "\n\n"
        for m in matches:
            score_h = m.get("score_home", 0)
            score_a = m.get("score_away", 0)
            minute  = m.get("minute", "?")
            league  = m.get("league", "")
            status  = m.get("status", "LIVE")
            status_icon = "🔴" if status in ("1H", "2H", "LIVE") else "⏸" if status == "HT" else "🟡"
            min_str = f"{minute}'" if isinstance(minute, int) else str(minute)
            text += f"{status_icon} *{m['home']}* {score_h}:{score_a} *{m['away']}*\n   ⏱ {min_str} | {league}\n\n"

        keyboard = []
        for m in matches[:8]:
            keyboard.append([InlineKeyboardButton(
                f"📊 {m['home'][:12]} vs {m['away'][:12]}",
                callback_data=f"analyze_{m['home_id']}_{m['away_id']}"
            )])
        keyboard.append([
            InlineKeyboardButton("🔄 Оновити", callback_data="refresh_live"),
            InlineKeyboardButton("📅 Сьогодні", callback_data="show_today"),
        ])
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "show_today":
        tz_offset = context.user_data.get("tz_offset", 0)
        matches = analyzer.get_today_matches()
        sign = "+" if tz_offset >= 0 else ""
        if not matches:
            await query.edit_message_text("📭 Сьогодні матчів не знайдено.")
            return
        keyboard = []
        for m in matches[:10]:
            local_time = convert_time_to_user(m["time"], tz_offset)
            label = f"{m['home']} vs {m['away']} ({local_time})"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"analyze_{m['home_id']}_{m['away_id']}")])
        await query.edit_message_text(
            f"📅 *Матчі сьогодні* ({len(matches)} знайдено)\n"
            f"🕐 UTC{sign}{tz_offset} · Оберіть для аналізу:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

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
    app.add_handler(CommandHandler("live", live_cmd))
    app.add_handler(CommandHandler("anomaly", anomaly_cmd))
    app.add_handler(CommandHandler("timezone", timezone_cmd))
    app.add_handler(CommandHandler("leagues", leagues_cmd))
    app.add_handler(MessageHandler(filters.LOCATION, location_handler))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("🤖 Бот запущено!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

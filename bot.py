import os
import math
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

APISPORTS_KEY    = os.getenv("APISPORTS_KEY", "")
FOOTBALLDATA_KEY = os.getenv("FOOTBALLDATA_KEY", "")

DEMO_TEAMS = {
    "ukr": [
        {"id": "1001", "name": "Динамо Київ",     "avg_scored": 1.85, "avg_conceded": 0.72, "form": "WWDWLW", "home_bonus": 0.18},
        {"id": "1002", "name": "Шахтар Донецьк",  "avg_scored": 1.72, "avg_conceded": 0.85, "form": "WWWDWL", "home_bonus": 0.14},
        {"id": "1003", "name": "Ворскла Полтава",  "avg_scored": 1.10, "avg_conceded": 1.25, "form": "DLWLWD", "home_bonus": 0.08},
        {"id": "1004", "name": "Дніпро-1",         "avg_scored": 1.30, "avg_conceded": 1.10, "form": "WLDWDW", "home_bonus": 0.10},
        {"id": "1005", "name": "Зоря Луганськ",    "avg_scored": 1.20, "avg_conceded": 1.15, "form": "DWLLWD", "home_bonus": 0.07},
        {"id": "1006", "name": "Металіст 1925",    "avg_scored": 1.15, "avg_conceded": 1.20, "form": "WDLWDL", "home_bonus": 0.09},
        {"id": "1007", "name": "Рух Львів",        "avg_scored": 1.05, "avg_conceded": 1.35, "form": "LLWDLW", "home_bonus": 0.07},
        {"id": "1008", "name": "Олімпік Донецьк",  "avg_scored": 0.95, "avg_conceded": 1.45, "form": "LLDLWL", "home_bonus": 0.06},
    ],
    "epl": [
        {"id": "2001", "name": "Manchester City",   "avg_scored": 2.45, "avg_conceded": 0.68, "form": "WWWWDW", "home_bonus": 0.22},
        {"id": "2002", "name": "Arsenal",           "avg_scored": 2.20, "avg_conceded": 0.75, "form": "WWDWWL", "home_bonus": 0.20},
        {"id": "2003", "name": "Liverpool",         "avg_scored": 2.30, "avg_conceded": 0.82, "form": "WWWLWW", "home_bonus": 0.21},
        {"id": "2004", "name": "Chelsea",           "avg_scored": 1.80, "avg_conceded": 1.10, "form": "WDLWWD", "home_bonus": 0.15},
        {"id": "2005", "name": "Tottenham",         "avg_scored": 1.65, "avg_conceded": 1.20, "form": "DLWLWD", "home_bonus": 0.13},
        {"id": "2006", "name": "Man United",        "avg_scored": 1.50, "avg_conceded": 1.30, "form": "LWDWLL", "home_bonus": 0.12},
        {"id": "2007", "name": "Newcastle",         "avg_scored": 1.70, "avg_conceded": 1.05, "form": "WWDWDW", "home_bonus": 0.14},
        {"id": "2008", "name": "Aston Villa",       "avg_scored": 1.75, "avg_conceded": 1.00, "form": "WDWWLW", "home_bonus": 0.15},
    ],
    "esp": [
        {"id": "3001", "name": "Real Madrid",       "avg_scored": 2.50, "avg_conceded": 0.70, "form": "WWWWWL", "home_bonus": 0.23},
        {"id": "3002", "name": "Barcelona",         "avg_scored": 2.40, "avg_conceded": 0.80, "form": "WWDWWW", "home_bonus": 0.22},
        {"id": "3003", "name": "Atletico Madrid",   "avg_scored": 1.90, "avg_conceded": 0.75, "form": "WWWDLW", "home_bonus": 0.18},
        {"id": "3004", "name": "Sevilla",           "avg_scored": 1.40, "avg_conceded": 1.15, "form": "DLWDWL", "home_bonus": 0.11},
        {"id": "3005", "name": "Villarreal",        "avg_scored": 1.55, "avg_conceded": 1.10, "form": "WDWLWD", "home_bonus": 0.12},
        {"id": "3006", "name": "Real Sociedad",     "avg_scored": 1.60, "avg_conceded": 1.05, "form": "DWWLWD", "home_bonus": 0.13},
    ],
    "ger": [
        {"id": "4001", "name": "Bayern Munich",     "avg_scored": 2.80, "avg_conceded": 0.85, "form": "WWWWLW", "home_bonus": 0.25},
        {"id": "4002", "name": "Bayer Leverkusen",  "avg_scored": 2.30, "avg_conceded": 0.90, "form": "WWWDWW", "home_bonus": 0.20},
        {"id": "4003", "name": "Borussia Dortmund", "avg_scored": 2.10, "avg_conceded": 1.10, "form": "WDWWLW", "home_bonus": 0.18},
        {"id": "4004", "name": "RB Leipzig",        "avg_scored": 1.95, "avg_conceded": 0.95, "form": "WWLDWW", "home_bonus": 0.16},
        {"id": "4005", "name": "Eintracht",         "avg_scored": 1.55, "avg_conceded": 1.20, "form": "DWWLDD", "home_bonus": 0.12},
    ],
    "ita": [
        {"id": "5001", "name": "Inter Milan",       "avg_scored": 2.20, "avg_conceded": 0.75, "form": "WWWWDW", "home_bonus": 0.20},
        {"id": "5002", "name": "AC Milan",          "avg_scored": 1.80, "avg_conceded": 0.90, "form": "WWDLWW", "home_bonus": 0.17},
        {"id": "5003", "name": "Juventus",          "avg_scored": 1.70, "avg_conceded": 0.85, "form": "WDWWDL", "home_bonus": 0.15},
        {"id": "5004", "name": "Napoli",            "avg_scored": 1.90, "avg_conceded": 1.00, "form": "WWWLWD", "home_bonus": 0.17},
        {"id": "5005", "name": "Roma",              "avg_scored": 1.65, "avg_conceded": 1.10, "form": "DWWLWL", "home_bonus": 0.13},
        {"id": "5006", "name": "Lazio",             "avg_scored": 1.60, "avg_conceded": 1.05, "form": "WDLWWD", "home_bonus": 0.12},
    ],
}

LEAGUES = [
    {"id": "ukr", "name": "🇺🇦 ПЛ України",   "country": "Ukraine", "apisports_id": 333, "fd_code": "PPL"},
    {"id": "epl", "name": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 АПЛ",          "country": "England", "apisports_id": 39,  "fd_code": "PL"},
    {"id": "esp", "name": "🇪🇸 Ла Ліга",       "country": "Spain",   "apisports_id": 140, "fd_code": "PD"},
    {"id": "ger", "name": "🇩🇪 Бундесліга",    "country": "Germany", "apisports_id": 78,  "fd_code": "BL1"},
    {"id": "ita", "name": "🇮🇹 Серія А",       "country": "Italy",   "apisports_id": 135, "fd_code": "SA"},
    {"id": "fra", "name": "🇫🇷 Ліга 1",        "country": "France",  "apisports_id": 61,  "fd_code": "FL1"},
    {"id": "cl",  "name": "🏆 Ліга чемпіонів", "country": "Europe",  "apisports_id": 2,   "fd_code": "CL"},
]


class FootballAnalyzer:
    def __init__(self):
        self.has_apisports    = bool(APISPORTS_KEY)
        self.has_footballdata = bool(FOOTBALLDATA_KEY)
        self._team_cache: dict = {}
        if self.has_apisports:
            self._src = "apisports"
        elif self.has_footballdata:
            self._src = "footballdata"
        else:
            self._src = "demo"

    def source_label(self) -> str:
        return {"apisports": "api-football.com ✅",
                "footballdata": "football-data.org ✅",
                "demo": "ДЕМО режим"}.get(self._src, "?")

    # ── PUBLIC ──────────────────────────────────────────────────────────────────

    def get_leagues(self) -> list:
        return LEAGUES

    def get_teams(self, league_id: str) -> list:
        if self._src == "apisports":   return self._as_teams(league_id)
        if self._src == "footballdata": return self._fd_teams(league_id)
        teams = DEMO_TEAMS.get(league_id, DEMO_TEAMS["epl"])
        for t in teams:
            self._team_cache[t["id"]] = t
        return teams

    def get_live_matches(self) -> list:
        """Повертає матчі що зараз грають"""
        if self._src == "apisports":
            return self._as_live()
        elif self._src == "footballdata":
            return self._fd_live()
        else:
            return self._demo_live()

    def _as_live(self) -> list:
        try:
            data = self._as_req("fixtures", {"live": "all"})
            result = []
            for fix in data.get("response", [])[:20]:
                teams  = fix["teams"]
                goals  = fix["goals"]
                status = fix["fixture"]["status"]
                lg     = fix["league"]
                result.append({
                    "home":       teams["home"]["name"],
                    "away":       teams["away"]["name"],
                    "home_id":    str(teams["home"]["id"]),
                    "away_id":    str(teams["away"]["id"]),
                    "score_home": goals.get("home", 0) or 0,
                    "score_away": goals.get("away", 0) or 0,
                    "minute":     status.get("elapsed") or "?",
                    "status":     status.get("short", "LIVE"),
                    "league":     lg.get("name", ""),
                })
            return result
        except Exception:
            return []

    def _fd_live(self) -> list:
        try:
            data = self._fd_req("matches", {"status": "IN_PLAY,PAUSED,HALFTIME"})
            result = []
            for m in data.get("matches", [])[:20]:
                h  = m["homeTeam"]
                a  = m["awayTeam"]
                sc = m.get("score", {}).get("fullTime", {})
                hid = str(h["id"]); aid = str(a["id"])
                minute = m.get("minute")
                status_map = {"IN_PLAY": "LIVE", "PAUSED": "HT", "HALFTIME": "HT"}
                raw_status = m.get("status", "IN_PLAY")
                result.append({
                    "home":       h.get("shortName") or h["name"],
                    "away":       a.get("shortName") or a["name"],
                    "home_id":    hid,
                    "away_id":    aid,
                    "score_home": sc.get("home", 0) or 0,
                    "score_away": sc.get("away", 0) or 0,
                    "minute":     minute or "?",
                    "status":     status_map.get(raw_status, "LIVE"),
                    "league":     m.get("competition", {}).get("name", ""),
                })
            return result
        except Exception:
            return []

    def _demo_live(self) -> list:
        """Демо-дані для живих матчів — включають аномальні ситуації"""
        return [
            {"home": "Arsenal",        "away": "Chelsea",
             "home_id": "2002",        "away_id": "2004",
             "score_home": 0,          "score_away": 0,
             "minute": 63,             "status": "2H",   "league": "АПЛ"},
            {"home": "Real Madrid",    "away": "Atletico",
             "home_id": "3001",        "away_id": "3003",
             "score_home": 0,          "score_away": 0,
             "minute": 71,             "status": "2H",   "league": "Ла Ліга"},
            {"home": "Bayern Munich",  "away": "Dortmund",
             "home_id": "4001",        "away_id": "4003",
             "score_home": 1,          "score_away": 0,
             "minute": 58,             "status": "2H",   "league": "Бундесліга"},
            {"home": "Liverpool",      "away": "Man United",
             "home_id": "2003",        "away_id": "2006",
             "score_home": 0,          "score_away": 0,
             "minute": 44,             "status": "1H",   "league": "АПЛ"},
        ]

    def get_today_matches(self) -> list:
        if self._src == "apisports":    return self._as_today()
        if self._src == "footballdata": return self._fd_today()
        return [
            {"home": "Динамо Київ",    "away": "Шахтар Донецьк", "home_id": "1001", "away_id": "1002", "time": "19:00"},
            {"home": "Manchester City","away": "Arsenal",          "home_id": "2001", "away_id": "2002", "time": "21:00"},
            {"home": "Real Madrid",    "away": "Barcelona",        "home_id": "3001", "away_id": "3002", "time": "20:00"},
        ]

    def analyze_match(self, home_id: str, away_id: str) -> dict:
        if self._src == "apisports":    return self._as_analyze(home_id, away_id)
        if self._src == "footballdata": return self._fd_analyze(home_id, away_id)
        return self._demo_analyze(home_id, away_id)

    # ── API-FOOTBALL.COM ────────────────────────────────────────────────────────

    def _as_req(self, endpoint: str, params: dict) -> dict:
        r = requests.get(
            f"https://v3.football.api-sports.io/{endpoint}",
            headers={"x-apisports-key": APISPORTS_KEY},
            params=params, timeout=12)
        r.raise_for_status()
        return r.json()

    def _as_teams(self, league_id: str) -> list:
        lg = next((l for l in LEAGUES if l["id"] == league_id), None)
        if not lg:
            return []
        try:
            data = self._as_req("teams", {"league": lg["apisports_id"], "season": 2024})
            result = []
            for item in data.get("response", []):
                t = item["team"]
                e = {"id": str(t["id"]), "name": t["name"]}
                result.append(e)
                self._team_cache[str(t["id"])] = e
            return result or DEMO_TEAMS.get(league_id, [])
        except Exception:
            return DEMO_TEAMS.get(league_id, [])

    def _as_today(self) -> list:
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            data = self._as_req("fixtures", {"date": today})
            result = []
            for fix in data.get("response", [])[:12]:
                tm = fix["teams"]
                result.append({
                    "home": tm["home"]["name"], "away": tm["away"]["name"],
                    "home_id": str(tm["home"]["id"]), "away_id": str(tm["away"]["id"]),
                    "time": fix["fixture"]["date"][11:16],
                })
            return result
        except Exception:
            return []

    def _as_stats(self, team_id: str) -> dict:
        try:
            data = self._as_req("teams/statistics",
                                {"team": team_id, "season": 2024, "league": 39})
            d = data.get("response", {})
            g = d.get("goals", {})
            scored   = float(g.get("for",     {}).get("average", {}).get("total") or 1.2)
            conceded = float(g.get("against", {}).get("average", {}).get("total") or 1.1)
            fx = d.get("fixtures", {})
            played = max(fx.get("played", {}).get("total", 1) or 1, 1)
            clean  = d.get("clean_sheet", {}).get("total", 0) or 0
            form_raw = d.get("form") or "WWDLL"
            return {
                "name": self._team_cache.get(str(team_id), {}).get("name", f"T{team_id}"),
                "avg_scored": scored, "avg_conceded": conceded,
                "form": form_raw[-6:],
                "home_bonus": round(clean / played * 0.3, 2),
            }
        except Exception:
            return self._fallback(team_id)

    def _as_h2h(self, hid: str, aid: str) -> list:
        try:
            data = self._as_req("fixtures/headtohead", {"h2h": f"{hid}-{aid}", "last": 5})
            result = []
            for fix in data.get("response", []):
                g  = fix["goals"]
                hs = g.get("home", 0) or 0
                as_= g.get("away", 0) or 0
                result.append({
                    "home": fix["teams"]["home"]["name"],
                    "away": fix["teams"]["away"]["name"],
                    "score": f"{hs}:{as_}",
                    "winner": "home" if hs > as_ else "away" if as_ > hs else "draw",
                    "date": fix["fixture"]["date"][:10],
                })
            return result
        except Exception:
            return []

    def _as_analyze(self, hid: str, aid: str) -> dict:
        return self._build(self._as_stats(hid), self._as_stats(aid), self._as_h2h(hid, aid))

    # ── FOOTBALL-DATA.ORG ───────────────────────────────────────────────────────

    def _fd_req(self, endpoint: str, params: dict = None) -> dict:
        r = requests.get(
            f"https://api.football-data.org/v4/{endpoint}",
            headers={"X-Auth-Token": FOOTBALLDATA_KEY},
            params=params or {}, timeout=12)
        r.raise_for_status()
        return r.json()

    def _fd_teams(self, league_id: str) -> list:
        lg = next((l for l in LEAGUES if l["id"] == league_id), None)
        if not lg:
            return []
        try:
            data = self._fd_req(f"competitions/{lg['fd_code']}/teams")
            result = []
            for t in data.get("teams", []):
                e = {"id": str(t["id"]), "name": t.get("shortName") or t["name"]}
                result.append(e)
                self._team_cache[str(t["id"])] = e
            return result or DEMO_TEAMS.get(league_id, [])
        except Exception:
            return DEMO_TEAMS.get(league_id, [])

    def _fd_today(self) -> list:
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            data = self._fd_req("matches", {"dateFrom": today, "dateTo": today})
            result = []
            for m in data.get("matches", [])[:12]:
                h = m["homeTeam"]
                a = m["awayTeam"]
                hid = str(h["id"]); aid = str(a["id"])
                self._team_cache[hid] = {"id": hid, "name": h.get("shortName") or h["name"]}
                self._team_cache[aid] = {"id": aid, "name": a.get("shortName") or a["name"]}
                result.append({
                    "home": h.get("shortName") or h["name"],
                    "away": a.get("shortName") or a["name"],
                    "home_id": hid, "away_id": aid,
                    "time": m.get("utcDate", "")[11:16],
                })
            return result
        except Exception:
            return []

    def _fd_stats(self, team_id: str) -> dict:
        try:
            data = self._fd_req(f"teams/{team_id}/matches",
                                {"status": "FINISHED", "limit": 10})
            matches = data.get("matches", [])
            if not matches:
                return self._fallback(team_id)
            sc = cc = clean = 0
            form_chars = []
            for m in matches:
                is_home = str(m["homeTeam"]["id"]) == str(team_id)
                ft = m.get("score", {}).get("fullTime", {})
                hg = ft.get("home", 0) or 0
                ag = ft.get("away", 0) or 0
                mg = hg if is_home else ag
                og = ag if is_home else hg
                sc += mg; cc += og
                if og == 0: clean += 1
                form_chars.append("W" if mg > og else "D" if mg == og else "L")
            n = len(matches)
            t0 = matches[0]
            raw = t0["homeTeam"] if str(t0["homeTeam"]["id"]) == str(team_id) else t0["awayTeam"]
            name = self._team_cache.get(str(team_id), {}).get("name") or raw.get("shortName", f"T{team_id}")
            return {
                "name": name,
                "avg_scored":   round(sc / n, 2),
                "avg_conceded": round(cc / n, 2),
                "form": "".join(form_chars[-6:]),
                "home_bonus": round(clean / n * 0.3, 2),
            }
        except Exception:
            return self._fallback(team_id)

    def _fd_h2h(self, hid: str, aid: str) -> list:
        try:
            data = self._fd_req(f"teams/{hid}/matches",
                                {"status": "FINISHED", "limit": 20})
            result = []
            for m in data.get("matches", []):
                ids = {str(m["homeTeam"]["id"]), str(m["awayTeam"]["id"])}
                if str(hid) in ids and str(aid) in ids:
                    ft = m.get("score", {}).get("fullTime", {})
                    hg = ft.get("home", 0) or 0
                    ag = ft.get("away", 0) or 0
                    result.append({
                        "home": m["homeTeam"].get("shortName") or m["homeTeam"]["name"],
                        "away": m["awayTeam"].get("shortName") or m["awayTeam"]["name"],
                        "score": f"{hg}:{ag}",
                        "winner": "home" if hg > ag else "away" if ag > hg else "draw",
                        "date": m.get("utcDate", "")[:10],
                    })
                    if len(result) >= 5:
                        break
            return result
        except Exception:
            return []

    def _fd_analyze(self, hid: str, aid: str) -> dict:
        return self._build(self._fd_stats(hid), self._fd_stats(aid), self._fd_h2h(hid, aid))

    # ── DEMO ────────────────────────────────────────────────────────────────────

    def _demo_analyze(self, hid: str, aid: str) -> dict:
        def find(tid):
            if tid in self._team_cache:
                return self._team_cache[tid]
            for teams in DEMO_TEAMS.values():
                for t in teams:
                    if str(t["id"]) == tid:
                        return t
        H = find(hid); A = find(aid)
        if not H or not A:
            raise ValueError(f"Команди не знайдено: {hid}, {aid}")
        return self._build(H, A, self._demo_h2h(H["name"], A["name"]))

    def _demo_h2h(self, home: str, away: str) -> list:
        return [
            {"home": home, "away": away, "score": "2:0", "winner": "home", "date": "2024-10-15"},
            {"home": away, "away": home, "score": "1:1", "winner": "draw", "date": "2024-04-20"},
            {"home": home, "away": away, "score": "3:1", "winner": "home", "date": "2023-10-12"},
            {"home": away, "away": home, "score": "0:1", "winner": "away", "date": "2023-04-18"},
            {"home": home, "away": away, "score": "1:0", "winner": "home", "date": "2022-10-09"},
        ]

    # ── SHARED ──────────────────────────────────────────────────────────────────

    def _fallback(self, team_id: str) -> dict:
        return {"name": self._team_cache.get(str(team_id), {}).get("name", f"T{team_id}"),
                "avg_scored": 1.2, "avg_conceded": 1.1, "form": "WWDLL", "home_bonus": 0.10}

    def _build(self, H: dict, A: dict, h2h: list) -> dict:
        xg_h = H["avg_scored"] * 0.55 + A["avg_conceded"] * 0.45 + H.get("home_bonus", 0.10)
        xg_a = A["avg_scored"] * 0.55 + H["avg_conceded"] * 0.45
        return {
            "home": H["name"], "away": A["name"],
            "form_home": H.get("form", "?????"),
            "form_away": A.get("form", "?????"),
            "xg": {"home": round(xg_h, 2), "away": round(xg_a, 2),
                   "total": round(xg_h + xg_a, 2)},
            "predictions": self._poisson_predict(xg_h, xg_a),
            "avg": {"home_scored":   H["avg_scored"],
                    "home_conceded": H["avg_conceded"],
                    "away_scored":   A["avg_scored"],
                    "away_conceded": A["avg_conceded"]},
            "h2h": h2h,
            "source": self.source_label(),
        }

    # ── ANOMALY DETECTION ───────────────────────────────────────────────────────

    def find_anomalies(self) -> list:
        """
        Шукає live матчі де статистика команд вказує на гол,
        але рахунок ще не відкрито або нижчий за очікуваний.
        Повертає список аномалій з поясненням і score.
        """
        live = self.get_live_matches()
        if not live:
            return []

        anomalies = []
        for m in live:
            sh = m.get("score_home", 0)
            sa = m.get("score_away", 0)
            minute = m.get("minute")
            status = m.get("status", "")

            # Пропускаємо перерву і матчі без хвилини
            if status == "HT" or not isinstance(minute, int):
                continue

            # Отримуємо статистику команд
            try:
                H = self._get_team_stats_cached(m["home_id"])
                A = self._get_team_stats_cached(m["away_id"])
            except Exception:
                continue

            xg_h = H["avg_scored"] * 0.55 + A["avg_conceded"] * 0.45 + H.get("home_bonus", 0.10)
            xg_a = A["avg_scored"] * 0.55 + H["avg_conceded"] * 0.45
            xg_total = xg_h + xg_a

            # Очікувані голи на поточну хвилину
            expected_by_now = xg_total * (minute / 90)
            actual_goals    = sh + sa
            goal_deficit    = round(expected_by_now - actual_goals, 2)

            signals  = []
            score    = 0  # чим більше — тим аномальніша ситуація

            # ── Сигнал 1: обидві команди забивні, рахунок 0:0 після 55+ хв
            if sh == 0 and sa == 0 and minute >= 55:
                both_avg = H["avg_scored"] + A["avg_scored"]
                if both_avg >= 2.8:
                    signals.append(f"⚽ Обидві забивають в середньому {both_avg:.1f} г/м, але 0:0 на {minute}'")
                    score += 35

            # ── Сигнал 2: очікувані голи сильно більші за фактичні
            if goal_deficit >= 1.0 and minute >= 40:
                signals.append(f"📊 Очікувалось {expected_by_now:.1f} голів до {minute}', фактично: {actual_goals}")
                score += int(goal_deficit * 20)

            # ── Сигнал 3: обидві команди забивні, але тотал < 1 після 65 хв
            if actual_goals <= 1 and minute >= 65:
                if xg_total >= 2.5:
                    signals.append(f"🔥 xG матчу {xg_total:.1f}, але лише {actual_goals} гол(ів) на {minute}'")
                    score += 30

            # ── Сигнал 4: атакуюча команда веде 0 голів при xG > 1.5
            if sh == 0 and xg_h >= 1.5 and minute >= 50:
                signals.append(f"🏠 {m['home']} забиває {H['avg_scored']:.1f} г/м — досі 0 голів на {minute}'")
                score += 25

            if sa == 0 and xg_a >= 1.3 and minute >= 50:
                signals.append(f"✈️ {m['away']} забиває {A['avg_scored']:.1f} г/м — досі 0 голів на {minute}'")
                score += 20

            # ── Сигнал 5: форма обох команд переважно W/W, матч порожній
            form_score_h = sum(3 if c=="W" else 1 if c=="D" else 0 for c in H.get("form",""))
            form_score_a = sum(3 if c=="W" else 1 if c=="D" else 0 for c in A.get("form",""))
            if form_score_h >= 12 and form_score_a >= 12 and actual_goals == 0 and minute >= 60:
                signals.append(f"📈 Обидві команди у топ-формі (W-серії), матч порожній на {minute}'")
                score += 20

            # ── Сигнал 6: рахунок менший ніж у H2H зазвичай
            avg_h2h_goals = self._avg_h2h_goals(m["home_id"], m["away_id"])
            if avg_h2h_goals >= 2.8 and actual_goals == 0 and minute >= 50:
                signals.append(f"📖 H2H середній тотал {avg_h2h_goals:.1f}, зараз {actual_goals} на {minute}'")
                score += 15

            if signals and score >= 25:
                # Ймовірність голу в залишок матчу
                remaining = max(90 - minute, 1)
                xg_remaining = xg_total * (remaining / 90) * 1.15  # тиск зростає
                prob_goal = round((1 - math.exp(-xg_remaining)) * 100)

                anomalies.append({
                    "home":       m["home"],
                    "away":       m["away"],
                    "home_id":    m["home_id"],
                    "away_id":    m["away_id"],
                    "score":      f"{sh}:{sa}",
                    "minute":     minute,
                    "league":     m.get("league", ""),
                    "signals":    signals,
                    "anomaly_score": min(score, 99),
                    "prob_goal":  prob_goal,
                    "xg_total":   round(xg_total, 2),
                    "remaining":  remaining,
                })

        # Сортуємо за силою аномалії
        anomalies.sort(key=lambda x: x["anomaly_score"], reverse=True)
        return anomalies

    def _get_team_stats_cached(self, team_id: str) -> dict:
        """Кешовані статистики команди — спочатку демо/кеш, потім API"""
        cache_key = f"stats_{team_id}"
        if cache_key in self._team_cache:
            return self._team_cache[cache_key]

        # Спочатку шукаємо в демо даних
        for teams in DEMO_TEAMS.values():
            for t in teams:
                if str(t["id"]) == str(team_id):
                    self._team_cache[cache_key] = t
                    return t

        # Якщо є API — запитуємо
        if self._src == "apisports":
            stats = self._as_stats(team_id)
        elif self._src == "footballdata":
            stats = self._fd_stats(team_id)
        else:
            stats = self._fallback(team_id)

        self._team_cache[cache_key] = stats
        return stats

    def _avg_h2h_goals(self, home_id: str, away_id: str) -> float:
        """Середній тотал голів в очних зустрічах"""
        try:
            if self._src == "apisports":
                h2h = self._as_h2h(home_id, away_id)
            elif self._src == "footballdata":
                h2h = self._fd_h2h(home_id, away_id)
            else:
                h2h = self._demo_h2h("H", "A")

            if not h2h:
                return 2.5
            totals = []
            for m in h2h:
                parts = m["score"].split(":")
                if len(parts) == 2:
                    totals.append(int(parts[0]) + int(parts[1]))
            return round(sum(totals) / len(totals), 1) if totals else 2.5
        except Exception:
            return 2.5

    def _poisson(self, lam: float, k: int) -> float:
        return math.exp(-lam) * (lam ** k) / math.factorial(k)

    def _poisson_predict(self, xg_h: float, xg_a: float) -> dict:
        hw = dr = aw = o25 = o15 = bt = 0.0
        for i in range(9):
            for j in range(9):
                p = self._poisson(xg_h, i) * self._poisson(xg_a, j)
                if   i > j:  hw += p
                elif i == j: dr += p
                else:        aw += p
                if i + j > 2: o25 += p
                if i + j > 1: o15 += p
                if i > 0 and j > 0: bt += p
        tot = hw + dr + aw
        return {
            "home_win": round(hw / tot * 100),
            "draw":     round(dr / tot * 100),
            "away_win": round(aw / tot * 100),
            "over25":   round(o25 * 100),
            "over15":   round(o15 * 100),
            "btts":     round(bt * 100),
        }

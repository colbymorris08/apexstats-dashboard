"""GameChanger (team-manager.gc.com) API client for Apex HS stats."""
from __future__ import annotations

import base64
import json
import os
import secrets
import time
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests
from Crypto.Hash import HMAC, SHA256

APEX_ROOT = Path(__file__).resolve().parent
GC_SESSION_PATH = APEX_ROOT / ".gc_session.json"
GC_API_BASE = "https://api.team-manager.gc.com"
GC_WEB_BASE = "https://web.gc.com"
GC_AUTH_CLIENT_KEY = (
    "759352bf-23af-45ae-a2ed-2148518e554e:dgf7Iqnt8aRQj98MyEIZzpUWIz4TF931ueMlhyYYDoE="
)
GC_CLIENT_ID, GC_SIGNING_KEY_B64 = GC_AUTH_CLIENT_KEY.split(":", 1)
GC_DEFAULT_EMAIL = "colbym@apexbaseball.com"
GC_DEFAULT_PASSWORD = "B@$3b@ll1!"
PACIFIC_TZ = ZoneInfo("America/Los_Angeles")


def _values_for_signer(obj: Any) -> list[str]:
    if isinstance(obj, list):
        out: list[str] = []
        for item in obj:
            out.extend(_values_for_signer(item))
        return out
    if isinstance(obj, dict):
        if not obj:
            return []
        out = []
        for key in sorted(obj.keys()):
            out.extend(_values_for_signer(obj[key]))
        return out
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, (int, float)):
        return [str(obj)]
    if obj is None:
        return []
    raise TypeError(type(obj))


def _sign_payload(client_key_b64: str, meta: dict[str, Any], payload: dict[str, Any]) -> str:
    key = base64.b64decode(client_key_b64)
    mac = HMAC.new(key, digestmod=SHA256)
    mac.update(f"{meta['timestamp']}|".encode())
    mac.update(base64.b64decode(meta["nonce"]))
    mac.update(b"|")
    mac.update("|".join(_values_for_signer(payload)).encode())
    prev = meta.get("previousSignature")
    if prev:
        mac.update(b"|")
        mac.update(base64.b64decode(prev))
    return base64.b64encode(mac.digest()).decode()


@dataclass
class GameChangerSession:
    access_token: str
    refresh_token: str
    access_expires: int
    refresh_expires: int
    device_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def is_access_valid(self, skew_seconds: int = 120) -> bool:
        return int(time.time()) + skew_seconds < int(self.access_expires)

    def is_refresh_valid(self, skew_seconds: int = 120) -> bool:
        return int(time.time()) + skew_seconds < int(self.refresh_expires)

    def to_json(self) -> dict[str, Any]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "access_expires": self.access_expires,
            "refresh_expires": self.refresh_expires,
            "device_id": self.device_id,
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> GameChangerSession:
        return cls(
            access_token=str(data["access_token"]),
            refresh_token=str(data["refresh_token"]),
            access_expires=int(data["access_expires"]),
            refresh_expires=int(data["refresh_expires"]),
            device_id=str(data.get("device_id") or uuid.uuid4()),
        )


class GameChangerClient:
    def __init__(self, session: GameChangerSession) -> None:
        self.session = session

    def _auth_request(
        self,
        payload: dict[str, Any],
        token: str | None = None,
        prev_sig: str | None = None,
        use_prev: bool = True,
    ) -> tuple[dict[str, Any], str | None]:
        ts = int(time.time())
        nonce_b64 = base64.b64encode(secrets.token_bytes(32)).decode()
        meta: dict[str, Any] = {"timestamp": ts, "nonce": nonce_b64}
        if prev_sig and use_prev:
            meta["previousSignature"] = prev_sig
        sig = _sign_payload(GC_SIGNING_KEY_B64, meta, payload)
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "gc-app-name": "web",
            "gc-app-version": "0.0.0",
            "gc-signature": f"{nonce_b64}.{sig}",
            "gc-client-id": GC_CLIENT_ID,
            "gc-timestamp": str(ts),
            "gc-device-id": self.session.device_id,
        }
        if token:
            headers["gc-token"] = token
        r = requests.post(f"{GC_API_BASE}/auth", headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        resp = r.json()
        hdr = r.headers.get("gc-signature", "")
        new_prev = hdr.split(".")[1] if "." in hdr else prev_sig
        return resp, new_prev

    def _api_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "gc-token": self.session.access_token,
            "gc-device-id": self.session.device_id,
            "gc-client-id": GC_CLIENT_ID,
            "gc-app-name": "web",
            "gc-app-version": "0.0.0",
        }

    def get(self, path: str, timeout: int = 30) -> Any:
        r = requests.get(f"{GC_API_BASE}{path}", headers=self._api_headers(), timeout=timeout)
        r.raise_for_status()
        return r.json()

    @classmethod
    def login(cls, email: str, password: str, device_id: str | None = None) -> GameChangerClient:
        session = GameChangerSession(
            access_token="",
            refresh_token="",
            access_expires=0,
            refresh_expires=0,
            device_id=device_id or str(uuid.uuid4()),
        )
        client = cls(session)
        prev: str | None = None
        client_resp, prev = client._auth_request(
            {"type": "client-auth", "client_id": GC_CLIENT_ID}, use_prev=False
        )
        client_token = client_resp["token"]
        _, prev = client._auth_request(
            {"type": "user-auth", "email": email}, token=client_token, prev_sig=prev
        )
        token_resp, _ = client._auth_request(
            {"type": "password", "password": password}, token=client_token, prev_sig=prev
        )
        if token_resp.get("type") != "token":
            raise RuntimeError(f"GameChanger login failed: {token_resp.get('type')}")
        session.access_token = token_resp["access"]["data"]
        session.refresh_token = token_resp["refresh"]["data"]
        session.access_expires = int(token_resp["access"]["expires"])
        session.refresh_expires = int(token_resp["refresh"]["expires"])
        return client

    def refresh(self) -> None:
        prev: str | None = None
        token_resp, _ = self._auth_request(
            {"type": "refresh"},
            token=self.session.refresh_token,
            use_prev=False,
        )
        if token_resp.get("type") != "token":
            raise RuntimeError("GameChanger token refresh failed")
        self.session.access_token = token_resp["access"]["data"]
        self.session.refresh_token = token_resp["refresh"]["data"]
        self.session.access_expires = int(token_resp["access"]["expires"])
        self.session.refresh_expires = int(token_resp["refresh"]["expires"])


def _load_session_file(path: Path) -> GameChangerSession | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text())
        return GameChangerSession.from_json(data)
    except Exception:
        return None


def _save_session_file(path: Path, session: GameChangerSession) -> None:
    path.write_text(json.dumps(session.to_json(), indent=2))


def get_gamechanger_client() -> GameChangerClient | None:
    """Return an authenticated GameChanger client, or None if auth is disabled/fails."""
    if os.environ.get("GC_DISABLE", "").strip().lower() in {"1", "true", "yes"}:
        return None

    email = os.environ.get("GC_EMAIL", GC_DEFAULT_EMAIL).strip()
    password = os.environ.get("GC_PASSWORD", GC_DEFAULT_PASSWORD)
    token_override = os.environ.get("GC_TOKEN", "").strip()
    session_path = Path(os.environ.get("GC_SESSION_PATH", str(GC_SESSION_PATH)))

    if token_override:
        refresh = os.environ.get("GC_REFRESH_TOKEN", "").strip()
        session = GameChangerSession(
            access_token=token_override,
            refresh_token=refresh or token_override,
            access_expires=int(time.time()) + 3600,
            refresh_expires=int(time.time()) + 86400 * 10,
        )
        client = GameChangerClient(session)
        return client

    session = _load_session_file(session_path)
    if session:
        client = GameChangerClient(session)
        if session.is_access_valid():
            return client
        if session.is_refresh_valid():
            try:
                client.refresh()
                _save_session_file(session_path, client.session)
                return client
            except Exception:
                pass

    if not email or not password:
        return None
    try:
        client = GameChangerClient.login(email, password, device_id=session.device_id if session else None)
        _save_session_file(session_path, client.session)
        return client
    except Exception:
        return None


@dataclass
class GCPlayerRef:
    team_id: str
    team_name: str
    player_id: str
    first_name: str
    last_name: str
    schedule_url: str = ""


@dataclass
class GameChangerIndex:
    client: GameChangerClient
    players_by_norm_name: dict[str, list[GCPlayerRef]] = field(default_factory=dict)
    _season_stats: dict[str, dict[str, Any]] = field(default_factory=dict)
    _schedules: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    _team_meta: dict[str, dict[str, Any]] = field(default_factory=dict)
    _boxscores: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def build(cls, client: GameChangerClient, norm_name_fn: Any, norm_token_fn: Any) -> GameChangerIndex:
        idx = cls(client=client)
        teams = client.get("/me/teams")
        if not isinstance(teams, list):
            return idx
        for team in teams:
            sport = str(team.get("sport") or "").lower()
            if sport and sport != "baseball":
                continue
            team_id = str(team.get("id") or "")
            if not team_id:
                continue
            try:
                meta = client.get(f"/teams/{team_id}")
            except Exception:
                meta = dict(team)
            idx._team_meta[team_id] = meta
            schedule_url = _team_schedule_url(meta)
            try:
                players = client.get(f"/teams/{team_id}/players")
            except Exception:
                continue
            if not isinstance(players, list):
                continue
            team_name = str(meta.get("name") or team.get("name") or "")
            for p in players:
                if str(p.get("status") or "").lower() not in {"", "active"}:
                    continue
                first = str(p.get("first_name") or "").strip()
                last = str(p.get("last_name") or "").strip()
                if not first and not last:
                    continue
                full = f"{first} {last}".strip()
                norm = norm_name_fn(full)
                ref = GCPlayerRef(
                    team_id=team_id,
                    team_name=team_name,
                    player_id=str(p.get("id") or ""),
                    first_name=first,
                    last_name=last,
                    schedule_url=schedule_url,
                )
                idx.players_by_norm_name.setdefault(norm, []).append(ref)
        return idx

    def match_player(
        self,
        client_name: str,
        school: str,
        norm_name_fn: Any,
        norm_token_fn: Any,
        name_parts_fn: Any,
    ) -> GCPlayerRef | None:
        want_norm = norm_name_fn(client_name)
        direct = self.players_by_norm_name.get(want_norm) or []
        if len(direct) == 1:
            return direct[0]
        first, last = name_parts_fn(client_name)
        first_i = norm_token_fn(first[:1]) if first else ""
        last_n = norm_token_fn(last)
        school_tokens = _school_match_tokens(school, norm_token_fn)

        best: GCPlayerRef | None = None
        best_score = -1
        pool = direct if direct else [ref for refs in self.players_by_norm_name.values() for ref in refs]
        for ref in pool:
            full = f"{ref.first_name} {ref.last_name}".strip()
            ref_norm = norm_name_fn(full)
            pf, pl = name_parts_fn(full)
            pl_n = norm_token_fn(pl)
            if pl_n != last_n and ref_norm != want_norm:
                continue
            score = 0
            if ref_norm == want_norm:
                score += 10
            elif want_norm and (ref_norm.startswith(want_norm) or want_norm.startswith(ref_norm)):
                score += 6
            if pl_n == last_n:
                score += 4
                if first_i and norm_token_fn(pf[:1]) == first_i:
                    score += 2
                elif first_i and norm_token_fn(pf).startswith(first_i):
                    score += 1
            if school_tokens:
                team_tokens = _school_match_tokens(ref.team_name, norm_token_fn)
                score += len(school_tokens & team_tokens) * 2
            if score > best_score:
                best_score = score
                best = ref
        if best_score < 4:
            return None
        return best

    def season_stats(self, team_id: str) -> dict[str, Any]:
        if team_id not in self._season_stats:
            self._season_stats[team_id] = self.client.get(f"/teams/{team_id}/season-stats")
        return self._season_stats[team_id]

    def schedule(self, team_id: str) -> list[dict[str, Any]]:
        if team_id not in self._schedules:
            raw = self.client.get(f"/teams/{team_id}/schedule")
            self._schedules[team_id] = raw if isinstance(raw, list) else []
        return self._schedules[team_id]

    def boxscore(self, event_id: str) -> dict[str, Any] | None:
        if event_id in self._boxscores:
            return self._boxscores[event_id]
        try:
            data = self.client.get(f"/game-stream-processing/{event_id}/boxscore")
        except Exception:
            self._boxscores[event_id] = {}
            return None
        self._boxscores[event_id] = data if isinstance(data, dict) else {}
        return self._boxscores[event_id] or None


def _team_schedule_url(team_meta: dict[str, Any]) -> str:
    public_id = str(team_meta.get("public_id") or "").strip()
    season_year = team_meta.get("season_year") or ""
    slug = str(team_meta.get("url_encoded_name") or "").strip()
    if public_id and season_year and slug:
        return f"{GC_WEB_BASE}/teams/{public_id}/{season_year}-season--{slug}/schedule"
    if public_id:
        return f"{GC_WEB_BASE}/teams/{public_id}/schedule"
    return GC_WEB_BASE


def _school_match_tokens(school: str, norm_token_fn: Any) -> set[str]:
    raw = (school or "").lower()
    for ch in "()":
        raw = raw.replace(ch, " ")
    stop = {
        "hs",
        "high",
        "school",
        "the",
        "academy",
        "varsity",
        "jv",
        "fl",
        "ca",
        "il",
        "ri",
        "fla",
        "calif",
    }
    tokens: set[str] = set()
    for part in raw.replace("/", " ").replace(",", " ").split():
        t = norm_token_fn(part)
        if len(t) >= 3 and t not in stop:
            tokens.add(t)
    return tokens


def _gc_offense_line(stats: dict[str, Any]) -> dict[str, Any]:
    ab = int(stats.get("AB") or 0)
    h = int(stats.get("H") or 0)
    return {
        "ab": ab,
        "r": int(stats.get("R") or 0),
        "h": h,
        "rbi": int(stats.get("RBI") or 0),
        "bb": int(stats.get("BB") or 0),
        "k": int(stats.get("SO") or 0),
        "hr": int(stats.get("HR") or 0),
        "triples": int(stats.get("3B") or 0),
        "doubles": int(stats.get("2B") or 0),
        "sb": int(stats.get("SB") or 0),
        "hbp": int(stats.get("HBP") or 0),
        "avg": float(stats.get("AVG")) if stats.get("AVG") not in (None, "-", "") else (round(h / ab, 3) if ab else 0.0),
        "ops": float(stats.get("OPS")) if stats.get("OPS") not in (None, "-", "") else 0.0,
    }


def _gc_pitching_line(stats: dict[str, Any]) -> dict[str, Any]:
    return {
        "ip": stats.get("IP"),
        "h": int(stats.get("H") or 0),
        "r": int(stats.get("R") or 0),
        "er": int(stats.get("ER") or 0),
        "bb": int(stats.get("BB") or 0),
        "k": int(stats.get("SO") or 0),
        "hr": int(stats.get("HR") or 0),
        "era": stats.get("ERA") if stats.get("ERA") not in (None, "-", "") else 0.0,
        "w": int(stats.get("W") or 0),
        "l": int(stats.get("L") or 0),
        "sv": int(stats.get("SV") or 0),
    }


def _player_season_lines(
    season_payload: dict[str, Any], player_id: str
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    players = (season_payload.get("stats_data") or {}).get("players") or {}
    pdata = players.get(player_id) or {}
    pstats = pdata.get("stats") or {}
    offense = pstats.get("offense") or {}
    defense = pstats.get("defense") or {}
    hit_line = None
    pitch_line = None
    if int(offense.get("GP") or offense.get("AB") or 0) > 0:
        hit_line = _gc_offense_line(offense)
    pitch_ip = defense.get("IP") or defense.get("GP:P")
    if pitch_ip and float(pitch_ip or 0) > 0:
        pitch_line = _gc_pitching_line(defense)
    return hit_line, pitch_line


def _parse_boxscore_player_lines(
    box: dict[str, Any], team_id: str, player_id: str
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    side = box.get(team_id) or box.get(str(team_id))
    if not side and box:
        # boxscore keys are public team ids; fall back to first side with our player.
        for val in box.values():
            if isinstance(val, dict) and any(
                str(p.get("id")) == player_id for p in (val.get("players") or []) if isinstance(p, dict)
            ):
                side = val
                break
    if not isinstance(side, dict):
        return None, None
    hit_stats: dict[str, Any] = {}
    pitch_stats: dict[str, Any] = {}
    for group in side.get("groups") or []:
        if not isinstance(group, dict):
            continue
        category = str(group.get("category") or "")
        extras = {e.get("stat_name"): e for e in (group.get("extra") or []) if isinstance(e, dict)}
        for row in group.get("stats") or []:
            if str(row.get("player_id")) != player_id:
                continue
            base = dict(row.get("stats") or {})
            for stat_name, block in extras.items():
                for entry in block.get("stats") or []:
                    if str(entry.get("player_id")) == player_id:
                        base[stat_name] = entry.get("value")
            if category == "lineup":
                hit_stats = base
            elif category == "pitching":
                pitch_stats = base
    hit_line = _gc_offense_line(hit_stats) if hit_stats else None
    pitch_line = _gc_pitching_line(pitch_stats) if pitch_stats else None
    return hit_line, pitch_line


def _event_pacific_date(event: dict[str, Any]) -> date | None:
    dt_raw = ((event.get("start") or {}).get("datetime")) or ""
    if not dt_raw:
        return None
    try:
        return datetime.fromisoformat(dt_raw.replace("Z", "+00:00")).astimezone(PACIFIC_TZ).date()
    except Exception:
        return None


def _merge_hit_lines(lines: list[dict[str, Any]]) -> dict[str, Any]:
    agg = {"ab": 0, "r": 0, "h": 0, "rbi": 0, "bb": 0, "k": 0, "hr": 0, "triples": 0, "doubles": 0, "sb": 0}
    for line in lines:
        for k in agg:
            agg[k] += int(line.get(k) or 0)
    agg["avg"] = round(agg["h"] / agg["ab"], 3) if agg["ab"] else 0.0
    return agg


def _merge_pitch_lines(lines: list[dict[str, Any]]) -> dict[str, Any]:
    agg = {"ip": 0.0, "h": 0, "r": 0, "er": 0, "bb": 0, "k": 0, "hr": 0, "w": 0, "l": 0, "sv": 0}
    for line in lines:
        try:
            agg["ip"] = float(agg["ip"]) + float(line.get("ip") or 0)
        except Exception:
            pass
        for k in ("h", "r", "er", "bb", "k", "hr", "w", "l", "sv"):
            agg[k] += int(line.get(k) or 0)
    if agg["ip"] > 0:
        agg["era"] = round(agg["er"] * 9.0 / agg["ip"], 2)
    return agg


def gc_player_game_lines(
    index: GameChangerIndex,
    ref: GCPlayerRef,
    yday: date,
    month_start: date,
    today: date,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    """Return (last_night_hit, month_hit, last_night_pitch, month_pitch)."""
    team_meta = index._team_meta.get(ref.team_id) or {}
    public_id = str(team_meta.get("public_id") or "")
    last_hits: list[dict[str, Any]] = []
    month_hits: list[dict[str, Any]] = []
    last_pitches: list[dict[str, Any]] = []
    month_pitches: list[dict[str, Any]] = []
    for item in index.schedule(ref.team_id):
        ev = item.get("event") or {}
        if str(ev.get("event_type") or "") != "game":
            continue
        gd = _event_pacific_date(ev)
        if gd is None or gd > today:
            continue
        if gd < month_start and gd != yday:
            continue
        event_id = str(ev.get("id") or "")
        if not event_id:
            continue
        box = index.boxscore(event_id)
        if not box:
            continue
        box_team_key = public_id if public_id in box else ref.team_id
        hit_line, pitch_line = _parse_boxscore_player_lines(box, box_team_key, ref.player_id)
        if gd == yday:
            if hit_line:
                last_hits.append(hit_line)
            if pitch_line:
                last_pitches.append(pitch_line)
        if month_start <= gd <= today:
            if hit_line:
                month_hits.append(hit_line)
            if pitch_line:
                month_pitches.append(pitch_line)
    return (
        _merge_hit_lines(last_hits) if last_hits else None,
        _merge_hit_lines(month_hits) if month_hits else None,
        _merge_pitch_lines(last_pitches) if last_pitches else None,
        _merge_pitch_lines(month_pitches) if month_pitches else None,
    )


def fetch_public_roster(client: GameChangerClient, public_id: str) -> list[dict[str, Any]]:
    raw = client.get(f"/teams/public/{public_id}/players")
    return raw if isinstance(raw, list) else []


def match_gc_roster_player(
    players: list[dict[str, Any]],
    client_name: str,
    norm_name_fn: Any,
    norm_token_fn: Any,
    name_parts_fn: Any,
) -> dict[str, Any] | None:
    want_norm = norm_name_fn(client_name)
    first, last = name_parts_fn(client_name)
    first_i = norm_token_fn(first[:1]) if first else ""
    last_n = norm_token_fn(last)

    best: dict[str, Any] | None = None
    best_score = -1
    for p in players:
        if str(p.get("status") or "").lower() not in {"", "active"}:
            continue
        pf = str(p.get("first_name") or "").strip()
        pl = str(p.get("last_name") or "").strip()
        full = f"{pf} {pl}".strip()
        if not full:
            continue
        ref_norm = norm_name_fn(full)
        pl_n = norm_token_fn(pl)
        if pl_n != last_n and ref_norm != want_norm:
            continue
        score = 0
        if ref_norm == want_norm:
            score += 10
        elif want_norm and (ref_norm.startswith(want_norm) or want_norm.startswith(ref_norm)):
            score += 6
        if pl_n == last_n:
            score += 4
            if not pf.strip():
                score += 5
            else:
                first_n = norm_token_fn(first) if first else ""
                pf_n = norm_token_fn(pf)
                if first_n and pf_n == first_n:
                    score += 4
                elif first_i and norm_token_fn(pf[:1]) == first_i:
                    score += 2
                elif first_n and pf_n and (pf_n.startswith(first_n[:3]) or first_n.startswith(pf_n[:3])):
                    score += 1
                elif ref_norm != want_norm:
                    continue
        if score > best_score:
            best_score = score
            best = p
    if best_score < 6:
        return None
    return best


def search_gc_teams(client: GameChangerClient, name: str, *, limit: int = 25) -> list[dict[str, Any]]:
    """Search GameChanger for public baseball teams by name."""
    r = requests.post(
        f"{GC_API_BASE}/search",
        headers=client._api_headers(),
        json={"name": name, "types": ["team"]},
        timeout=30,
    )
    r.raise_for_status()
    hits = r.json().get("hits") or []
    out: list[dict[str, Any]] = []
    for h in hits:
        if h.get("type") != "team":
            continue
        t = h.get("result") or {}
        if str(t.get("sport") or "").lower() != "baseball":
            continue
        out.append(t)
        if len(out) >= limit:
            break
    return out


def public_player_season_lines(
    client: GameChangerClient, public_id: str, player_id: str
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    try:
        stats = client.get(f"/teams/public/{public_id}/players/{player_id}/stats")
    except Exception:
        return None, None
    if not isinstance(stats, list) or not stats:
        return None, None
    last = stats[-1]
    if last.get("is_blurred"):
        return None, None
    cum = ((last.get("cumulative_stats") or {}).get("stats") or {})
    offense = cum.get("offense") or {}
    defense = cum.get("defense") or {}
    hit_line = None
    pitch_line = None
    if int(offense.get("GP") or offense.get("AB") or 0) > 0:
        hit_line = _gc_offense_line(offense)
    pitch_ip = defense.get("IP") or defense.get("GP:P")
    if pitch_ip and float(pitch_ip or 0) > 0:
        pitch_line = _gc_pitching_line(defense)
    return hit_line, pitch_line

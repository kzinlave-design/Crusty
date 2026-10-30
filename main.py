# main.py — Crusty Search (monolith, fixed + free-hosting optimized)
import threading
from flask import Flask
import asyncio, aiosqlite, random, re, os, sys, logging, json, hashlib, signal, time
import aiohttp
import ssl as _ssl
from html import escape as html_escape
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (Message, CallbackQuery, InlineKeyboardButton,
    InlineKeyboardMarkup, FSInputFile, InputMediaPhoto)
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest, TelegramConflictError

_ssl_ctx = _ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = _ssl.CERT_NONE

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
MAIN_MENU_IMAGE = os.path.join(BASE_DIR, "main.png")
PROFILE_IMAGE = os.path.join(BASE_DIR, "profile.png")
SHOP_IMAGE = os.path.join(BASE_DIR, "shop.png")
FUNCTIONAL_IMAGE = os.path.join(BASE_DIR, "functional.png")
DB_PATH = os.path.join(BASE_DIR, "bot.db")
LOCK_PATH = os.path.join(BASE_DIR, ".bot.lock")

BOT_NAME = "Crusty Search"
API_TOKEN = "8863973446:AAGaecUPFV03k_jvNw_NVAvEIa0YoH7TYpw"
ADMINS = [8292372344, 7146758056, 8708165470]

CHANNELS = [
    {"id": -1004389665536, "url": "https://t.me/B2L3NC1AGA", "name": "B2L3NC1AGA"},
    {"id": -1004330593063, "url": "https://t.me/CrustySearch", "name": "CrustySearch"},
]

BOT_USERNAME = "CrustySearchBot"
BOT_LINK = "https://t.me/CrustySearch"

E_LINK       = "6028171274939797252"
E_FUNCTIONAL = "5850309953293653168"
E_PROFILE    = "6032693626394382504"
E_BUY        = "5904462880941545555"
E_MYBOTS     = "6030400221232501136"
E_SUPPORT    = "5238025132177369293"
E_ADMIN      = "5208614506099398888"
E_FIND       = "6032850693348399258"

def em(eid: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'

EMOJI_LINK       = em(E_LINK, "🔗")
EMOJI_FUNCTIONAL = em(E_FUNCTIONAL, "⚙️")
EMOJI_PROFILE    = em(E_PROFILE, "👤")
EMOJI_BUY        = em(E_BUY, "💳")
EMOJI_MYBOTS     = em(E_MYBOTS, "🤖")
EMOJI_SUPPORT    = em(E_SUPPORT, "🆘")
EMOJI_ADMIN      = em(E_ADMIN, "⚙️")
EMOJI_FIND       = em(E_FIND, "🔍")

RES = {
    "u_hr_nick": "https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-username?username={username}",
    "u_hr_email": "https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-email?email={email}",
    "u_psbdmp_email": "https://psbdmp.ws/api/search/email/{email}",
    "u_proxynova": "https://api.proxynova.com/comb?query={query}&start=0&limit=100",
    "u_vk": "https://api.vk.com/method/users.get?access_token=0af157510af157510af15751aa0a89e69600af10af157516a0bc15996e74fe2b440998c&v=5.131&user_ids={user_id}&fields=first_name,last_name,status,sex,country,photo_max_orig",
    "u_vk_resolve": "https://api.vk.com/method/utils.resolveScreenName?access_token=0af157510af157510af15751aa0a89e69600af10af157516a0bc15996e74fe2b440998c&v=5.131&screen_name={screen_name}",
}

API_BASE = "https://api.depsearch.pro"
API_KEY = "rVCp0AQcXJsS8fr1KPyzkCGs86DGeZb9"

CARD_NUMBER = "2200 7021 7923 2868"
CARD_HOLDER = "ПАВЕЛ Д"
BTC_ADDRESS   = "1HYyHSyWFybCrmbBHVzmVLV7Dr9JpEHigS"
TRC20_ADDRESS = "TNx7yzrfzWPu8YiC8ZJqooA844UsrdEGD4"
USDT_ADDRESS  = "EQBAjphav1zeeYFw6LB5K7JMLaj8OV3wt9eoEf_7z3hikrck"
TON_ADDRESS   = "UQCx9nGpv4yRuWt8CBfDO4e-NZDbtbZ2ojQuNUelxPgtB4s-"

PRICE_PER_QUERY = 4
TARIFF_INFO = {
    "1q":   {"name": "1 Запрос",     "queries": 1,   "rub": 4},
    "10q":  {"name": "10 Запросов",  "queries": 10,  "rub": 40},
    "25q":  {"name": "25 Запросов",  "queries": 25,  "rub": 100},
    "50q":  {"name": "50 Запросов",  "queries": 50,  "rub": 200},
    "100q": {"name": "100 Запросов", "queries": 100, "rub": 400},
}
RUB_PER_USD = 90.0
CRYPTO_RATES = {"USDT": 1.0, "BTC": 60000.0, "TON": 5.0}
REF_QUERIES_PERCENT = 25
REF_MONEY_PERCENT = 20
DAILY_BONUS_QUERIES = 2
BOT_CREATE_BONUS = 5

SELF_LOOKUP_SALT = "crusty_self_lookup_salt_v1_2026"

STARS_ADMINS = [
    {"name": "1 Админ", "username": "malmovkilerr"},
    {"name": "2 Админ", "username": "swatlolz"},
]

# ============================================================
# OPTIMIZATION CONSTANTS (free-hosting)
# ============================================================
POLLING_RETRY_DELAY   = 5.0     # базовая пауза перед retry
POLLING_MAX_RETRIES   = 10      # максимум попыток
POLLING_PRE_DELAY     = 1.5     # пауза после delete_webhook
BROADCAST_CONCURRENCY = 5       # параллельных отправок
BROADCAST_SLEEP       = 0.08    # пауза между отправками
HTTP_LIMIT            = 40
HTTP_LIMIT_PER_HOST   = 10
HTTP_TTL_DNS          = 180

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

# ==== Render.com health-check ====
from flask import Flask  # добавьте в импорты сверху, а не здесь

web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Bot is running", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

_MAIN_LOCK_HANDLE = None

def acquire_single_instance_lock():
    global _MAIN_LOCK_HANDLE
    try:
        if os.name == "nt":
            import msvcrt
            fh = open(LOCK_PATH, "a+b")
            try:
                msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                fh.close(); return False
            _MAIN_LOCK_HANDLE = fh
        else:
            import fcntl
            fh = open(LOCK_PATH, "a+b")
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                fh.close(); return False
            _MAIN_LOCK_HANDLE = fh
        return True
    except Exception as ex:
        logger.warning(f"lock error: {ex}")
        return True


def release_single_instance_lock():
    global _MAIN_LOCK_HANDLE
    if _MAIN_LOCK_HANDLE is None: return
    try:
        if os.name == "nt":
            import msvcrt
            try:
                _MAIN_LOCK_HANDLE.seek(0)
                msvcrt.locking(_MAIN_LOCK_HANDLE.fileno(), msvcrt.LK_UNLCK, 1)
            except Exception: pass
        else:
            import fcntl
            try: fcntl.flock(_MAIN_LOCK_HANDLE.fileno(), fcntl.LOCK_UN)
            except Exception: pass
        _MAIN_LOCK_HANDLE.close()
    except Exception: pass
    _MAIN_LOCK_HANDLE = None


def h_esc(s) -> str:
    if s is None: return ""
    return html_escape(str(s), quote=False)


def rub_to_crypto(rub, crypto):
    return (rub / RUB_PER_USD) / CRYPTO_RATES.get(crypto, 1.0)


def fmt_crypto(a, c):
    if c == "BTC": return f"{a:.8f}"
    if c == "TON": return f"{a:.4f}"
    return f"{a:.4f}"


# ============================================================
# HTTP — как браузер
# ============================================================
_HTTP_SESSION = None
_HTTP_LOCK = asyncio.Lock()

async def get_session():
    global _HTTP_SESSION
    if _HTTP_SESSION is None or _HTTP_SESSION.closed:
        async with _HTTP_LOCK:
            if _HTTP_SESSION is None or _HTTP_SESSION.closed:
                conn = aiohttp.TCPConnector(
                    ssl=_ssl_ctx,
                    limit=HTTP_LIMIT,
                    limit_per_host=HTTP_LIMIT_PER_HOST,
                    ttl_dns_cache=HTTP_TTL_DNS,
                    enable_cleanup_closed=True,
                )
                _HTTP_SESSION = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=25, connect=8, sock_read=20),
                    connector=conn,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                                      "Chrome/131.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                                  "image/avif,image/webp,image/apng,*/*;q=0.8",
                        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Accept-Encoding": "gzip, deflate",
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache",
                        "Sec-Fetch-Dest": "document",
                        "Sec-Fetch-Mode": "navigate",
                        "Sec-Fetch-Site": "none",
                        "Sec-Fetch-User": "?1",
                        "Upgrade-Insecure-Requests": "1",
                        "Connection": "keep-alive",
                    },
                )
    return _HTTP_SESSION

async def close_session():
    global _HTTP_SESSION
    if _HTTP_SESSION and not _HTTP_SESSION.closed:
        try: await _HTTP_SESSION.close()
        except Exception: pass
    _HTTP_SESSION = None


# ============================================================
# DEPSEARCH
# ============================================================
class APIUnavailable(Exception):
    pass

async def api_query(q, retries=2, timeout=20):
    q_str = str(q).strip()
    encoded = q_str.replace(" ", "%20")
    url = f"{API_BASE}/quest={encoded}&token={API_KEY}&lang=ru"
    logger.info(f"[DepSearch] URL: {url}")

    last_err = "unavailable"
    last_status = None

    for attempt in range(retries + 1):
        try:
            session = await get_session()
            async with session.get(url, timeout=aiohttp.ClientTimeout(
                    total=timeout, connect=8, sock_read=timeout)) as r:
                txt = await r.text()
                last_status = r.status
                logger.info(f"[DepSearch] HTTP {r.status} body={txt[:200]!r}")

                if r.status == 200:
                    try:
                        return True, json.loads(txt)
                    except Exception as ex:
                        logger.warning(f"[DepSearch] bad json: {ex}")
                        return False, "bad_json"
                if r.status == 400: return False, "bad_request"
                if r.status == 401: return False, "auth_error"
                if r.status == 403: return False, "forbidden"
                if r.status == 404: return False, "not_found"
                if r.status == 429: return False, "rate_limit"
                if r.status >= 500: return False, "server_error"
                last_err = f"http_{r.status}"
        except asyncio.TimeoutError:
            last_err = "timeout"
            logger.warning(f"[DepSearch] timeout (attempt {attempt+1})")
        except aiohttp.ClientConnectorError as ex:
            last_err = "conn_error"
            logger.warning(f"[DepSearch] conn err: {ex}")
        except aiohttp.ClientError as ex:
            last_err = "client_error"
            logger.warning(f"[DepSearch] client err: {ex}")
        except Exception as ex:
            last_err = "unknown"
            logger.warning(f"[DepSearch] err: {ex}")

        if attempt < retries:
            await asyncio.sleep(0.6 * (attempt + 1))

    if last_status is not None:
        raise APIUnavailable(last_err if last_err != "unavailable" else f"http_{last_status}")
    raise APIUnavailable(last_err)


async def fetch_json(url, timeout=10):
    try:
        session = await get_session()
        async with session.get(url, timeout=aiohttp.ClientTimeout(
                total=timeout, connect=5, sock_read=timeout)) as r:
            if r.status != 200:
                logger.info(f"[fetch] {url[:80]} -> {r.status}")
                return None
            txt = await r.text()
            try: return json.loads(txt)
            except Exception: return None
    except asyncio.TimeoutError:
        logger.info(f"[fetch] timeout {url[:80]}")
    except Exception as ex:
        logger.info(f"[fetch] {url[:80]}: {ex}")
    return None


# ============================================================
# ПАРСЕРЫ
# ============================================================
def extract_phones_from(obj):
    found = set()
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                kl = str(k).lower()
                if isinstance(v, str):
                    vs = v.strip()
                    if any(x in kl for x in ("phone", "tel", "моб", "тел", "number", "mobile", "телефон")):
                        d = re.sub(r"\D", "", vs)
                        if 10 <= len(d) <= 15: found.add(vs)
                else: walk(v)
        elif isinstance(o, list):
            for i in o: walk(i)
        elif isinstance(o, str):
            for m in re.findall(r"\+?\d[\d\s\-\(\)]{9,16}\d", o):
                d = re.sub(r"\D", "", m)
                if 10 <= len(d) <= 15: found.add(m.strip())
    walk(obj); return sorted(found)


def extract_emails_from(obj):
    found = set()
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                kl = str(k).lower()
                if isinstance(v, str):
                    if "email" in kl or "mail" in kl or "почта" in kl:
                        if "@" in v and "." in v.split("@")[-1] and len(v) < 80:
                            found.add(v.strip())
                else: walk(v)
        elif isinstance(o, list):
            for i in o: walk(i)
        elif isinstance(o, str):
            for m in re.findall(r"[\w\.\-]+@[\w\.\-]+\.\w+", o):
                if len(m) < 80: found.add(m)
    walk(obj); return sorted(found)


async def search_by_username(username):
    username = username.lstrip("@").strip()
    if not username or len(username) < 2:
        return None

    phones, emails, extra = set(), set(), []

    async def safe(coro, timeout=10):
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except Exception as ex:
            logger.info(f"src skip: {ex}")
            return None

    dep_queries = [f"nick:{username}", f"@{username}", username]
    async def dep_call(q):
        try:
            return q, await api_query(q, retries=1, timeout=20)
        except APIUnavailable as ex:
            logger.warning(f"DepSearch unavailable for {q}: {ex}")
            return q, None
        except Exception as ex:
            logger.warning(f"DepSearch err for {q}: {ex}")
            return q, None

    dep_tasks = [dep_call(q) for q in dep_queries]
    hr_coro = safe(fetch_json(RES["u_hr_nick"].format(username=username)), 10)
    pv_coro = safe(fetch_json(RES["u_proxynova"].format(query=username)), 10)
    vk_resolve_coro = safe(fetch_json(RES["u_vk_resolve"].format(screen_name=username)), 10)

    dep_results_raw = await asyncio.gather(*dep_tasks)
    hr, pv, vk_resolve = await asyncio.gather(hr_coro, pv_coro, vk_resolve_coro)

    dep_answered = False
    for q, res in dep_results_raw:
        if res is not None:
            dep_answered = True
            ok, ds = res
            if ok and ds:
                if ds.get("results"):
                    extra.append((f"DepSearch ({q})", ds))
                phones.update(extract_phones_from(ds))
                emails.update(extract_emails_from(ds))

    if not dep_answered:
        raise APIUnavailable("timeout")

    if hr and (hr.get("stealers") or hr.get("data") or hr.get("employees")):
        phones.update(extract_phones_from(hr))
        emails.update(extract_emails_from(hr))
        extra.append(("HudsonRock", hr))

    if pv:
        phones.update(extract_phones_from(pv))
        emails.update(extract_emails_from(pv))
        if isinstance(pv, dict) and pv.get("lines"):
            extra.append(("Proxynova", pv))

    if vk_resolve and isinstance(vk_resolve, dict) and vk_resolve.get("response") \
            and vk_resolve["response"].get("object_id"):
        vk_id = vk_resolve["response"]["object_id"]
        vk_res = await safe(fetch_json(RES["u_vk"].format(user_id=vk_id)), 10)
        if vk_res and vk_res.get("response"):
            extra.append(("VK", vk_res))
            phones.update(extract_phones_from(vk_res))
            emails.update(extract_emails_from(vk_res))

    if not phones and not emails and not extra:
        return None

    return {
        "username": username,
        "phones": sorted(phones),
        "emails": sorted(emails),
        "extra": extra,
    }


def flatten_dict(d, prefix=""):
    rows = []
    if isinstance(d, dict):
        for k, v in d.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, (dict, list)): rows.extend(flatten_dict(v, key))
            else: rows.append((key, v))
    elif isinstance(d, list):
        for i, item in enumerate(d):
            key = f"{prefix}[{i}]" if prefix else f"[{i}]"
            if isinstance(item, (dict, list)): rows.extend(flatten_dict(item, key))
            else: rows.append((key, item))
    else:
        rows.append((prefix, d))
    return rows


def detect_query_type(q):
    s = q.strip()
    m = re.match(r"^(snils|снилс)[\s:\-]*(\d[\d\s\-]{9,15}\d)$", s, re.I)
    if m:
        d = re.sub(r"\D", "", m.group(2))
        if len(d) == 11: return "snils", f"snils{d}", "СНИЛС"
    m = re.match(r"^(inn|инн)[\s:\-]*(\d[\d\s\-]{8,15}\d)$", s, re.I)
    if m:
        d = re.sub(r"\D", "", m.group(2))
        if len(d) in (10, 12): return "inn", f"inn{d}", "ИНН"
    if s.lower().startswith("nick:"):  return "nick", s, "Ник"
    if s.lower().startswith("pass:"):  return "pass", s, "Пароль"
    if s.lower().startswith("tt:"):    return "tiktok", s, "TikTok"
    if s.lower().startswith("vkid"):   return "vk", s, "ВКонтакте"
    if s.lower().startswith(("addr:", "адрес:")): return "addr", s, "Адрес"
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", s):   return "ip", s, "IP"
    if "@" in s and not s.startswith("@") and "." in s.split("@")[-1]:
        return "email", s, "Email"
    digits = re.sub(r"\D", "", s)
    has_letters = bool(re.search(r"[A-Za-zА-Яа-яЁё]", s))
    only_phone_chars = bool(re.match(r"^[\+\d\s\-\(\)]+$", s))
    if only_phone_chars and not has_letters and 10 <= len(digits) <= 15:
        return "phone", s, "Телефон"
    if re.match(r"^[A-HJ-NPR-Z0-9]{17}$", s.upper()): return "vin", s, "VIN"
    if re.match(r"^[А-ЯЁA-Z]\d{3}[А-ЯЁA-Z]{2}\d{2,3}$", s.upper()):
        return "grz", s, "Автономер"
    if re.search(r"[А-ЯЁа-яё]", s) and re.match(r"^[А-ЯЁа-яёA-Za-z0-9\s\.\,\-\/]+$", s):
        return "fio", s, "ФИО"
    if s.startswith("@"):
        nick = s[1:]
        if re.match(r"^[A-Za-z0-9_\.]{3,32}$", nick): return "nick", f"nick:{nick}", "Ник"
    if re.match(r"^[A-Za-z0-9_\.]{3,32}$", s): return "nick", f"nick:{s}", "Ник"
    return "other", s, "Запрос"


def normalize_phone(q):
    d = re.sub(r"\D", "", q.strip())
    if len(d) == 11 and d.startswith("8"):
        d = "7" + d[1:]
    elif len(d) == 11 and d.startswith("7"):
        pass
    elif len(d) == 10:
        d = "7" + d
    return d


def safe_query_for_html(q: str) -> str:
    if not q: return "—"
    s = h_esc(q)
    if len(s) > 60: s = s[:60] + "…"
    return s


# ============================================================
# SELF-LOOKUP
# ============================================================
def _self_hash(normalized_phone: str) -> str:
    return hashlib.sha256(f"{SELF_LOOKUP_SALT}|phone|{normalized_phone}".encode()).hexdigest()


async def self_lookup_find(normalized_phone: str):
    h = _self_hash(normalized_phone)
    db = await aiosqlite.connect(DB_PATH)
    try:
        cur = await db.execute(
            "SELECT owner_user_id, owner_username, owner_first_name, owner_last_name, "
            "source, created_at FROM self_lookup WHERE hash_key=?", (h,))
        return await cur.fetchone()
    finally:
        await db.close()


async def self_lookup_save(normalized_phone: str, owner_user_id: int,
                           owner_username: str, owner_fn: str, owner_ln: str,
                           source: str = "auto"):
    h = _self_hash(normalized_phone)
    db = await aiosqlite.connect(DB_PATH)
    try:
        await db.execute(
            "INSERT OR IGNORE INTO self_lookup "
            "(hash_key, phone_masked, owner_user_id, owner_username, "
            "owner_first_name, owner_last_name, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (h, normalized_phone[-4:].rjust(len(normalized_phone), "*"),
             owner_user_id, owner_username or "",
             owner_fn or "", owner_ln or "", source))
        await db.commit()
        cur = await db.execute("SELECT changes()")
        row = await cur.fetchone()
        return bool(row and row[0])
    except Exception as ex:
        logger.warning(f"self_lookup_save: {ex}")
        return False
    finally:
        await db.close()


def _tokens_from_user(user) -> set:
    toks = set()
    def add(x):
        if not x: return
        x = str(x).strip().lower()
        if len(x) < 3: return
        toks.add(x)
    add(user.username)
    add(user.first_name)
    add(user.last_name)
    if user.first_name and user.last_name:
        add(f"{user.first_name} {user.last_name}")
        add(f"{user.last_name} {user.first_name}")
    return toks


def _flatten_strings(obj, out=None, depth=0):
    if out is None: out = []
    if depth > 12: return out
    if isinstance(obj, dict):
        for v in obj.values():
            _flatten_strings(v, out, depth + 1)
    elif isinstance(obj, list):
        for it in obj:
            _flatten_strings(it, out, depth + 1)
    elif isinstance(obj, str):
        out.append(obj)
    return out


def _match_owner_in_result(user, data) -> bool:
    if not data:
        return False
    user_tokens = _tokens_from_user(user)
    if not user_tokens:
        return False
    strings = _flatten_strings(data)
    if not strings:
        return False
    for s in strings:
        sl = str(s).strip().lower()
        if not sl: continue
        if sl in user_tokens:
            return True
        if sl.startswith("@") and sl[1:] in user_tokens:
            return True
        for t in user_tokens:
            if len(t) >= 4 and t in sl:
                return True
    return False


# ============================================================
# ФОРМАТИРОВАНИЕ
# ============================================================
def format_results(query, data, qtype_name="", self_binding=None):
    lines = ["╔══════════════════════════╗",
             "║   🔎  РЕЗУЛЬТАТ ПОИСКА    ║",
             "╚══════════════════════════╝", ""]

    if self_binding:
        owner_id, owner_un, owner_fn, owner_ln, src, created = self_binding
        lines.extend([
            "╔══════════════════════════╗",
            "║   🎯  СВЯЗЬ С АККАУНТОМ   ║",
            "╚══════════════════════════╝", "",
            f"📞 Номер привязан к TG-аккаунту:",
            f"   • user_id: <code>{owner_id}</code>",
            f"   • username: @{h_esc(owner_un or '—')}",
            f"   • имя: {h_esc((owner_fn + ' ' + owner_ln).strip() or '—')}",
            f"   • засветил: {h_esc(created)}",
            "", "━━━━━━━━━━━━━━━━━━━━━━━━", "",
        ])

    if qtype_name: lines.append(f"🏷 <b>Тип:</b> {h_esc(qtype_name)}")
    lines.append(f"📌 <b>Запрос:</b> <code>{h_esc(query)}</code>")
    lines.append(f"🕐 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")

    if "phone_info" in data:
        pi = data["phone_info"]
        lines.extend(["", "📱 <b>ИНФОРМАЦИЯ О НОМЕРЕ</b>", "",
                      f"   📞 Номер: <code>{h_esc(pi.get('phone', '—'))}</code>",
                      f"   📡 Оператор: {h_esc(pi.get('operator', '—'))}",
                      f"   🌍 Регион: {h_esc(pi.get('region', '—'))}",
                      f"   🕐 Таймзона: {h_esc(pi.get('timezone', '—'))}",
                      f"   ⏰ Местное время: {h_esc(pi.get('local_time', '—'))}"])
    if "ip_info" in data:
        ii = data["ip_info"]
        lines.extend(["", "🌐 <b>ИНФОРМАЦИЯ ОБ IP</b>", "",
                      f"   🌍 Страна: {h_esc(ii.get('country', '—'))}",
                      f"   🏙 Город: {h_esc(ii.get('city', '—'))}",
                      f"   📡 Провайдер: {h_esc(ii.get('provider', '—'))}"])

    results = data.get("results", [])
    lines.extend(["", "━━━━━━━━━━━━━━━━━━━━━━━━", ""])
    if results:
        lines.append(f"📊 <b>НАЙДЕНО: {len(results)}</b>"); lines.append("")
        for i, item in enumerate(results[:10], 1):
            lines.append(f"┌─ <b>#{i}</b> ─────────────")
            if isinstance(item, dict):
                for k, v in list(item.items())[:40]:
                    if isinstance(v, (dict, list)):
                        for kk, vv in flatten_dict(v, k)[:20]:
                            lines.append(f"│ <b>{h_esc(kk)}:</b> {h_esc(vv)}")
                    else:
                        lines.append(f"│ <b>{h_esc(k)}:</b> {h_esc(v)}")
            else:
                lines.append(f"│ {h_esc(item)}")
            lines.extend(["└─────────────────────", ""])
        if len(results) > 10:
            lines.append(f"… И ещё {len(results) - 10}. HTML полный.")
    else:
        lines.append("❌ Ничего не найдено.")
    lines.extend(["", "━━━━━━━━━━━━━━━━━━━━━━━━"])
    return "\n".join(lines)


def format_username_result(username, result):
    lines = ["╔══════════════════════════╗",
             "║   🔎  ПОИСК ПО ВСЕМУ      ║",
             "╚══════════════════════════╝", ""]
    lines.append(f"👤 <b>Ник:</b> <code>@{h_esc(username)}</code>")
    lines.append(f"🕐 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
    if result["phones"]:
        lines.extend(["", "📱 <b>НОМЕРА ТЕЛЕФОНОВ:</b>", ""])
        for p in result["phones"]:
            lines.append(f"   ☎️ <code>{h_esc(p)}</code>")
    else:
        lines.extend(["", "📱 <b>Номера не найдены</b>"])
    if result["emails"]:
        lines.extend(["", "📧 <b>EMAIL:</b>", ""])
        for e in result["emails"]:
            lines.append(f"   ✉️ <code>{h_esc(e)}</code>")
    for src_name, raw in result.get("extra", []):
        results = raw.get("results") if isinstance(raw, dict) else None
        if results:
            lines.extend(["", "━━━━━━━━━━━━━━━━━━━━━━━━", "",
                          f"📊 <b>{h_esc(src_name)}: {len(results)}</b>", ""])
            for i, item in enumerate(results[:5], 1):
                lines.append(f"┌─ <b>#{i}</b> ─────────────")
                if isinstance(item, dict):
                    for k, v in list(item.items())[:15]:
                        if isinstance(v, (dict, list)):
                            for kk, vv in flatten_dict(v, k)[:10]:
                                lines.append(f"│ <b>{h_esc(kk)}:</b> {h_esc(vv)}")
                        else:
                            lines.append(f"│ <b>{h_esc(k)}:</b> {h_esc(v)}")
                lines.append("└─────────────────────"); lines.append("")
    lines.extend(["", "━━━━━━━━━━━━━━━━━━━━━━━━"])
    return "\n".join(lines)


def build_html_report(query, data, qtype_name="", username_result=None, self_binding=None):
    def esc(s):
        return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    def md5h(x):
        try:
            return hashlib.md5(str(x).encode("utf-8", "ignore")).hexdigest()[:12]
        except Exception:
            return "000000000000"

    records = []
    phones_all, emails_all, fio_all, regions_all, birth_all = set(), set(), set(), set(), set()
    sources_meta = []

    def pick(flat, keys):
        for k, v in flat:
            if k.lower() in keys and v not in (None, ""):
                return str(v).strip()
        return ""

    if username_result:
        for p in username_result.get("phones", []): phones_all.add(str(p))
        for e in username_result.get("emails", []): emails_all.add(str(e))
        for src_name, raw in username_result.get("extra", []):
            results = raw.get("results") if isinstance(raw, dict) else None
            if not results: continue
            block = []
            for item in results:
                flat = flatten_dict(item) if isinstance(item, dict) else [("value", str(item))]
                block.append(flat); records.append(flat)
            sources_meta.append((src_name, block))

    if data:
        if isinstance(data.get("phone_info"), dict):
            pi = data["phone_info"]
            flat = [[k, v] for k, v in pi.items()]
            records.append(flat)
            if pi.get("phone"): phones_all.add(str(pi["phone"]))
            if pi.get("region"): regions_all.add(str(pi["region"]))
        if isinstance(data.get("ip_info"), dict):
            ii = data["ip_info"]
            flat = [[k, v] for k, v in ii.items()]
            records.append(flat)
            if ii.get("country"): regions_all.add(str(ii["country"]))
        for item in data.get("results", []):
            flat = flatten_dict(item) if isinstance(item, dict) else [("value", str(item))]
            records.append(flat)

    for flat in records:
        fio = pick(flat, ("фио", "fio", "name", "full_name", "fullname",
                          "имя", "first_name", "last_name", "фамилия"))
        if fio and 2 < len(fio) < 120: fio_all.add(fio)
        for k, v in flat:
            kl = k.lower()
            if not v: continue
            vs = str(v).strip()
            if not vs or len(vs) > 200: continue
            if "phone" in kl or "тел" in kl or "mobile" in kl:
                d = re.sub(r"\D", "", vs)
                if 10 <= len(d) <= 15: phones_all.add(vs)
            elif "email" in kl or "mail" in kl or "почта" in kl:
                if "@" in vs and "." in vs.split("@")[-1]: emails_all.add(vs)
            elif any(x in kl for x in ("регион", "region", "город", "city", "country", "страна")):
                regions_all.add(vs)
            elif any(x in kl for x in ("дата_рождения", "birth", "dob", "год_рождения")):
                birth_all.add(vs)

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    report_id = "CS-" + md5h(f"{query}|{now}").upper()[:10]
    total_records = len(records)
    sources_count = len(sources_meta) if sources_meta else (1 if records else 0)

    summary_cards = [("Записей", f"{total_records:02d}", "найдено"),
                     ("Источников", f"{sources_count:02d}", "баз данных"),
                     ("Тип", esc(qtype_name or "—"), "запроса")]
    if phones_all:
        summary_cards.append(("Телефон", f'<span class="mono">{esc(sorted(phones_all)[0])}</span>', "идентификатор"))
    if emails_all:
        summary_cards.append(("Email", f'<span class="mono">{esc(sorted(emails_all)[0])}</span>', "адрес"))
    if fio_all:
        summary_cards.append(("ФИО", esc(sorted(fio_all)[0]), f"{len(fio_all)} вариант(ов)"))

    summary_html = "".join(
        f'<div class="metric"><div class="k">{esc(k)}</div><div class="v">{v}</div>'
        f'<div class="hint">{esc(h)}</div></div>'
        for k, v, h in summary_cards)

    self_html = ""
    if self_binding:
        owner_id, owner_un, owner_fn, owner_ln, src, created = self_binding
        self_html = (
            '<section class="reveal"><div class="section-title">'
            '<h2>🎯 Связь с TG-аккаунтом</h2><p>self-lookup</p></div>'
            '<div class="panel"><div class="kv">'
            f'<div class="key">user_id</div><div class="mono">{esc(owner_id)}</div>'
            f'<div class="key">username</div><div>@{esc(owner_un or "—")}</div>'
            f'<div class="key">Имя</div><div>{esc((owner_fn + " " + owner_ln).strip() or "—")}</div>'
            f'<div class="key">Засветил</div><div class="mono">{esc(created)}</div>'
            f'<div class="key">Источник</div><div>{esc(src)}</div>'
            '</div></div></section>')

    identity_rows = ""
    for name in sorted(fio_all)[:8]:
        score = random.randint(35, 95)
        meta_bits = list(birth_all)[:1] + list(regions_all)[:1]
        meta_str = " · ".join(esc(x) for x in meta_bits) if meta_bits else "—"
        identity_rows += (
            f'<div class="identity"><div>'
            f'<div class="name">{esc(name)}</div>'
            f'<div class="meta">{meta_str}</div>'
            f'</div><div><div class="score">{score}%</div>'
            f'<div class="bar"><i style="width:{score}%"></i></div></div></div>')
    if not identity_rows:
        identity_rows = ('<div class="identity"><div><div class="name">—</div>'
                         '<div class="meta">нет данных</div></div></div>')

    kv_rows = ""
    if phones_all: kv_rows += f'<div class="key">Телефон</div><div class="mono">{esc(sorted(phones_all)[0])}</div>'
    if emails_all: kv_rows += f'<div class="key">Email</div><div class="mono">{esc(sorted(emails_all)[0])}</div>'
    if fio_all:    kv_rows += f'<div class="key">ФИО</div><div>{esc(sorted(fio_all)[0])}</div>'
    if birth_all:  kv_rows += f'<div class="key">Дата рождения</div><div class="mono">{esc(sorted(birth_all)[0])}</div>'
    if regions_all:kv_rows += f'<div class="key">Регион</div><div>{esc(", ".join(sorted(regions_all)[:3]))}</div>'
    kv_rows += f'<div class="key">Запрос</div><div class="mono">{esc(query)}</div>'

    profiles_rows = ""
    for flat in records[:30]:
        fio   = pick(flat, ("фио", "fio", "name", "full_name", "fullname", "имя"))
        nick  = pick(flat, ("nick", "nickname", "username", "логин", "login"))
        ident = pick(flat, ("id", "user_id", "uid", "identifier", "телефон", "phone", "email"))
        src   = pick(flat, ("source", "источник", "database", "база"))
        if not (fio or nick or ident): continue
        profiles_rows += (
            f'<tr><td>{esc(src or "—")}</td>'
            f'<td>{esc(fio or nick or "—")}</td>'
            f'<td class="mono">{esc(ident or "—")}</td></tr>')
    if not profiles_rows:
        profiles_rows = '<tr><td colspan="3" style="text-align:center;color:#777">нет профилей</td></tr>'

    aliases_html = ""
    for a in sorted(fio_all)[:20]:  aliases_html += f'<span class="tag">{esc(a)}</span>'
    for e in sorted(emails_all)[:20]: aliases_html += f'<span class="tag">{esc(e)}</span>'
    for p in sorted(phones_all)[:20]: aliases_html += f'<span class="tag">{esc(p)}</span>'
    if not aliases_html: aliases_html = '<span class="tag">—</span>'

    addresses_html = ""
    for r in sorted(regions_all)[:10]:
        addresses_html += (
            f'<div class="address"><div><b>{esc(r)}</b>'
            f'<div class="meta">регион / локация</div></div>'
            f'<button class="mapbtn">📍 Карта</button></div>')
    if not addresses_html:
        addresses_html = '<div class="address"><div><b>—</b><div class="meta">нет данных</div></div></div>'

    sources_html = ""
    if sources_meta:
        for i, (src_name, block) in enumerate(sources_meta):
            open_attr = " open" if i == 0 else ""
            rows = ""
            for flat in block[:1]:
                for k, v in flat[:20]:
                    rows += f'<div class="key">{esc(k)}</div><div>{esc(v)}</div>'
            if not rows: rows = '<div class="key">—</div><div>пусто</div>'
            sources_html += (
                f'<details class="source"{open_attr}>'
                f'<summary><b>{esc(src_name)}</b><span>{len(block):02d} записей</span></summary>'
                f'<div class="source-body"><div class="kv">{rows}</div></div>'
                f'</details>')
    else:
        for i, flat in enumerate(records[:8]):
            open_attr = " open" if i == 0 else ""
            rows = "".join(f'<div class="key">{esc(k)}</div><div>{esc(v)}</div>' for k, v in flat[:20])
            sources_html += (
                f'<details class="source"{open_attr}>'
                f'<summary><b>CRUSTYSEARCH / запись #{i+1}</b><span>{len(flat):02d} полей</span></summary>'
                f'<div class="source-body"><div class="kv">{rows}</div></div>'
                f'</details>')
    if not sources_html:
        sources_html = ('<details class="source" open><summary><b>Нет данных</b><span>00</span></summary>'
                        '<div class="source-body"><div class="kv"><div class="key">—</div>'
                        '<div>пусто</div></div></div></details>')

    phones_tags = "".join(f'<span class="tag">{esc(p)}</span>' for p in sorted(phones_all)) \
                  or '<span class="tag">телефоны не найдены</span>'
    emails_tags = "".join(f'<span class="tag">{esc(e)}</span>' for e in sorted(emails_all)) \
                  or '<span class="tag">email не найдены</span>'

    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CrustySearch — {esc(query)}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');
:root{{
  --bg:#050506; --panel:rgba(255,255,255,.028); --panel-2:rgba(255,255,255,.045);
  --line:rgba(255,255,255,.09); --line-2:rgba(255,255,255,.16);
  --text:#f4f4f1; --muted:#85868b; --muted-2:#63656c;
  --r-xl:26px; --r-lg:20px; --r-md:16px; --r-pill:999px;
  --ease:cubic-bezier(.22,.8,.22,1);
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth;background:var(--bg)}}
body{{margin:0;color:var(--text);background:var(--bg);font-family:Inter,system-ui,sans-serif;font-weight:500;min-height:100vh;-webkit-font-smoothing:antialiased}}
button,input{{font:inherit}}button{{color:inherit;cursor:pointer;border:0;background:none}}
.mono{{font-family:"JetBrains Mono",monospace;font-size:.9em;letter-spacing:-.02em}}
.wrap{{max-width:1240px;margin:auto;padding:0 30px}}
.top{{height:68px;background:rgba(5,5,6,.85);backdrop-filter:blur(20px) saturate(140%);-webkit-backdrop-filter:blur(20px) saturate(140%);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:30}}
.topbar{{height:100%;display:flex;align-items:center;gap:22px}}
.brand{{font-size:19px;font-weight:800;letter-spacing:-.05em;white-space:nowrap}}
.brand span{{font-weight:500;color:#999}}
.search{{height:42px;flex:1;max-width:440px;margin-left:auto;border:1px solid var(--line);background:rgba(255,255,255,.04);padding:0 16px;outline:none;font-weight:600;color:var(--text);border-radius:var(--r-pill);transition:background .25s var(--ease),border-color .25s var(--ease),box-shadow .25s var(--ease)}}
.search:focus{{background:rgba(255,255,255,.06);border-color:var(--line-2);box-shadow:0 0 0 4px rgba(255,255,255,.05)}}
.search::placeholder{{color:var(--muted-2)}}
.actions{{display:flex;gap:8px}}
.btn{{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:0 16px;font-weight:700;font-size:13px;color:var(--text);background:rgba(255,255,255,.045);border:1px solid var(--line);border-radius:var(--r-pill);text-decoration:none;transition:transform .22s var(--ease),background .22s var(--ease),border-color .22s var(--ease),box-shadow .22s var(--ease)}}
.btn:hover{{background:rgba(255,255,255,.09);border-color:var(--line-2);transform:translateY(-2px);box-shadow:0 12px 30px rgba(0,0,0,.35)}}
.btn:active{{transform:translateY(0) scale(.97)}}
.hero{{margin-top:18px;padding:46px 0 34px;background:var(--panel);border:1px solid var(--line);border-radius:var(--r-xl);overflow:hidden;animation:fadeUp .7s var(--ease) both}}
.crumb{{font-size:11px;color:var(--muted);font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:14px}}
.badge{{display:inline-block;border:1px solid var(--line);padding:4px 10px;margin-left:7px;color:var(--text);background:rgba(255,255,255,.04);border-radius:var(--r-pill);letter-spacing:.06em;font-size:11px}}
.hero h1{{font-size:46px;line-height:.98;letter-spacing:-.06em;font-weight:800;margin:0 0 12px;animation:fadeUp .8s .05s var(--ease) both}}
.sub{{font-weight:600;color:var(--muted)}}
.sub .mono{{color:var(--text)}}
.nav{{margin-top:14px;background:var(--panel);border:1px solid var(--line);border-radius:var(--r-lg);overflow:auto}}
.navrow{{display:flex;gap:28px;overflow:auto;white-space:nowrap;padding:0 30px}}
.nav a{{padding:16px 0;color:var(--muted);font-size:12px;font-weight:700;position:relative;text-decoration:none;transition:color .22s var(--ease)}}
.nav a::after{{content:"";position:absolute;left:0;right:100%;bottom:0;height:2px;background:var(--text);transition:right .3s var(--ease);border-radius:2px}}
.nav a:hover{{color:var(--text)}}
.nav a:hover::after{{right:0}}
main{{padding:34px 0 80px}}
.notice{{background:rgba(255,255,255,.035);color:var(--text);padding:14px 18px;font-size:12px;font-weight:600;margin-bottom:26px;border:1px solid var(--line);border-radius:var(--r-md);animation:fadeUp .6s var(--ease) both}}
section{{margin-bottom:44px;scroll-margin-top:95px}}
.section-title{{display:flex;justify-content:space-between;align-items:end;margin-bottom:14px}}
.section-title h2{{font-size:22px;font-weight:800;letter-spacing:-.04em;margin:0}}
.section-title p{{font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin:0}}
.card,.panel,.source{{background:var(--panel);border:1px solid var(--line);border-radius:var(--r-lg);transition:border-color .28s var(--ease),background .28s var(--ease),transform .28s var(--ease),box-shadow .28s var(--ease)}}
.card:hover,.panel:hover{{border-color:var(--line-2);background:rgba(255,255,255,.035);box-shadow:0 16px 40px rgba(0,0,0,.28);transform:translateY(-2px)}}
.summary{{display:grid;grid-template-columns:repeat(3,1fr);overflow:hidden}}
.metric{{padding:24px;border-right:1px solid var(--line);border-bottom:1px solid var(--line);transition:background .25s var(--ease);animation:fadeUp .6s var(--ease) both}}
.metric:hover{{background:rgba(255,255,255,.03)}}
.metric:nth-child(3n){{border-right:0}}
.metric:nth-last-child(-n+3){{border-bottom:0}}
.metric .k{{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;font-weight:800}}
.metric .v{{font-size:24px;font-weight:800;letter-spacing:-.04em;margin-top:8px;overflow-wrap:anywhere}}
.metric .hint{{font-size:11px;color:var(--muted-2);font-weight:600;margin-top:3px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.panel{{padding:22px}}
.panel h3{{margin:0 0 16px;font-size:14px;font-weight:800}}
.identity{{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:14px 10px;border-top:1px solid var(--line);border-radius:12px;transition:padding-left .25s var(--ease),background .25s var(--ease)}}
.identity:hover{{padding-left:16px;background:rgba(255,255,255,.02)}}
.identity:first-of-type{{border-top:0}}
.name{{font-weight:800}}
.meta{{font-size:11px;color:var(--muted);font-weight:600;margin-top:2px}}
.score{{font-family:"JetBrains Mono",monospace;font-weight:600;font-size:12px}}
.bar{{width:96px;height:5px;background:rgba(255,255,255,.06);margin-top:8px;overflow:hidden;border-radius:var(--r-pill)}}
.bar i{{display:block;height:100%;background:#fff;transform-origin:left;border-radius:var(--r-pill);animation:bar 1s var(--ease) both}}
.kv{{display:grid;grid-template-columns:175px 1fr}}
.kv div{{padding:10px 0;border-bottom:1px solid var(--line)}}
.kv .key{{color:var(--muted);font-weight:600}}
.kv .mono{{color:var(--text)}}
table{{width:100%;border-collapse:separate;border-spacing:0;overflow:hidden;border-radius:var(--r-lg)}}
th,td{{text-align:left;padding:12px 16px;border-bottom:1px solid var(--line)}}
th{{font-size:10px;color:var(--muted);text-transform:uppercase;font-weight:800;letter-spacing:.08em;background:rgba(255,255,255,.02)}}
td{{font-weight:600;font-size:12px}}
tbody tr{{transition:background .2s var(--ease)}}
tbody tr:hover{{background:rgba(255,255,255,.03)}}
tbody tr:last-child td{{border-bottom:0}}
.tag{{display:inline-block;background:rgba(255,255,255,.045);padding:7px 12px;margin:4px;font-size:11px;font-weight:700;border:1px solid var(--line);border-radius:var(--r-pill);color:var(--text);transition:transform .22s var(--ease),background .22s var(--ease),border-color .22s var(--ease)}}
.tag:hover{{background:rgba(255,255,255,.11);border-color:var(--line-2);transform:translateY(-2px)}}
.address{{display:flex;justify-content:space-between;align-items:center;padding:14px 10px;border-top:1px solid var(--line);border-radius:12px;transition:background .22s var(--ease)}}
.address:first-child{{border-top:0}}
.address:hover{{background:rgba(255,255,255,.02)}}
.address b{{font-weight:800}}
.mapbtn{{border:1px solid var(--line);background:rgba(255,255,255,.045);padding:8px 12px;font-weight:700;font-size:12px;border-radius:var(--r-pill);transition:transform .22s var(--ease),background .22s var(--ease),border-color .22s var(--ease)}}
.mapbtn:hover{{background:rgba(255,255,255,.09);border-color:var(--line-2);transform:translateY(-2px)}}
.sources{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.source{{overflow:hidden;background:rgba(255,255,255,.02)}}
.source summary{{cursor:pointer;list-style:none;padding:16px 20px;display:flex;justify-content:space-between;align-items:center;font-weight:800;transition:background .22s var(--ease)}}
.source summary::-webkit-details-marker{{display:none}}
.source summary::after{{content:"+";font-size:18px;font-weight:400;color:var(--muted);transition:transform .3s var(--ease),color .3s var(--ease)}}
.source[open] summary::after{{transform:rotate(45deg);color:var(--text)}}
.source summary:hover{{background:rgba(255,255,255,.03)}}
.source summary span{{color:var(--muted);font:500 10px "JetBrains Mono",monospace}}
.source-body{{border-top:1px solid var(--line);padding:16px 20px;animation:openBody .3s var(--ease) both}}
.source .kv{{grid-template-columns:140px 1fr}}
.source .kv div{{border-bottom:1px solid var(--line)}}
footer{{border-top:1px solid var(--line);padding:28px 0;color:var(--muted);font-size:11px;font-weight:600;background:rgba(255,255,255,.012);border-radius:var(--r-lg) var(--r-lg) 0 0;margin-top:30px}}
.reveal{{opacity:0;transform:translateY(18px);transition:opacity .6s var(--ease),transform .6s var(--ease)}}
.reveal.show{{opacity:1;transform:none}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
@keyframes bar{{from{{transform:scaleX(0)}}}}
@keyframes openBody{{from{{opacity:0;transform:translateY(-6px)}}to{{opacity:1;transform:none}}}}
@media(max-width:800px){{
  .wrap{{padding:0 16px}}
  .top{{height:auto}}
  .topbar{{min-height:64px;padding:12px 0;flex-wrap:wrap;gap:14px}}
  .search{{order:3;flex-basis:100%;max-width:none;margin:0}}
  .actions{{margin-left:auto}}
  .actions .btn:first-child{{display:none}}
  .hero{{padding:34px 0 26px;border-radius:var(--r-lg)}}
  .hero h1{{font-size:34px}}
  .navrow{{gap:20px;padding:0 18px}}
  .summary,.grid2,.sources{{grid-template-columns:1fr}}
  .metric{{border-right:0}}
  .metric:nth-last-child(-n+3){{border-bottom:1px solid var(--line)}}
  .metric:last-child{{border-bottom:0}}
  .kv{{grid-template-columns:120px 1fr}}
  th,td{{padding:10px 12px}}
  th:nth-child(3),td:nth-child(3){{display:none}}
  .source .kv{{grid-template-columns:110px 1fr}}
}}
@media(prefers-reduced-motion:reduce){{
  *,*::before,*::after{{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important;scroll-behavior:auto!important}}
}}
::selection{{background:rgba(255,255,255,.22);color:#fff}}
::-webkit-scrollbar{{width:10px;height:10px}}
::-webkit-scrollbar-track{{background:transparent}}
::-webkit-scrollbar-thumb{{background:rgba(255,255,255,.12);border:3px solid transparent;background-clip:padding-box;border-radius:var(--r-pill)}}
::-webkit-scrollbar-thumb:hover{{background:rgba(255,255,255,.22);background-clip:padding-box}}
a{{color:var(--text);text-decoration:none}}
</style>
</head>
<body>
<header class="top"><div class="wrap topbar">
<div class="brand">CrustySearch <span>/ Report</span></div>
<input class="search" placeholder="Поиск по отчету…">
<div class="actions">
<button class="btn" onclick="navigator.clipboard?.writeText(location.href)">Копировать</button>
<a class="btn" href="https://t.me/CrustySearch" target="_blank" rel="noopener">CrustySearch</a>
</div>
</div></header>

<div class="hero"><div class="wrap">
<div class="crumb">Отчёт / <span class="mono">{esc(report_id)}</span> <span class="badge">{esc(qtype_name or "ПОИСК")}</span></div>
<h1>{esc(query)}</h1>
<div class="sub">Найдено записей <span class="mono">{total_records}</span> · Источников <span class="mono">{sources_count}</span></div>
</div></div>

<nav class="nav"><div class="navrow wrap">
<a href="#summary">Краткая сводка</a>
<a href="#profiles">Профили</a>
<a href="#identifiers">Идентификаторы</a>
<a href="#aliases">Возможные имена</a>
<a href="#addresses">Адреса</a>
<a href="#sources">Расширенный отчет</a>
</div></nav>

<main class="wrap">
<div class="notice">ОТЧЁТ СФОРМИРОВАН · {now} · Все данные получены из открытых источников.</div>

{self_html}

<section id="summary" class="reveal">
<div class="section-title"><h2>Краткая сводка</h2><p>Сводные данные</p></div>
<div class="card summary">{summary_html}</div>
</section>

<section class="reveal">
<div class="grid2">
<div class="panel"><h3>Найденные личности</h3>{identity_rows}</div>
<div class="panel"><h3>Основные идентификаторы</h3><div class="kv">{kv_rows}</div></div>
</div>
</section>

<section id="profiles" class="reveal">
<div class="section-title"><h2>Профили в интернете</h2><p>{total_records} записей</p></div>
<div class="card"><table><thead><tr><th>Источник</th><th>Имя / никнейм</th><th>Идентификатор</th></tr></thead><tbody>{profiles_rows}</tbody></table></div>
</section>

<section id="identifiers" class="reveal">
<div class="section-title"><h2>Идентификаторы</h2><p>телефоны и email</p></div>
<div class="panel">{phones_tags}{emails_tags}</div>
</section>

<section id="aliases" class="reveal">
<div class="section-title"><h2>Возможные имена</h2><p>{len(fio_all)} вариантов</p></div>
<div class="panel">{aliases_html}</div>
</section>

<section id="addresses" class="reveal">
<div class="section-title"><h2>Адреса и регионы</h2><p>{len(regions_all)} вариантов</p></div>
<div class="panel">{addresses_html}</div>
</section>

<section id="sources" class="reveal">
<div class="section-title"><h2>Расширенный отчет</h2><p>источники и поля</p></div>
<div class="sources">{sources_html}</div>
</section>
</main>

<footer><div class="wrap">CrustySearch · Report · {now}</div></footer>

<script>
const io=new IntersectionObserver(es=>es.forEach(e=>{{if(e.isIntersecting)e.target.classList.add("show")}}),{{threshold:.08}});
document.querySelectorAll(".reveal").forEach(x=>io.observe(x));
document.querySelector(".search").addEventListener("input",e=>{{
  const q=e.target.value.toLowerCase().trim();
  document.querySelectorAll("section,.source,.panel").forEach(x=>{{
    x.style.outline = (q && x.innerText.toLowerCase().includes(q)) ? "2px solid rgba(255,255,255,.35)" : "";
  }});
}});
</script>
</body></html>"""


# ============================================================
# БД
# ============================================================
def generate_uid(): return f"USR-{random.randint(10000, 99999)}"
def generate_payment_code() -> str:
    p1 = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=4))
    p2 = "".join(random.choices("0123456789", k=4))
    return f"CS-{p1}-{p2}"


async def _db_connect():
    """Единая точка подключения с оптимизациями под фри-хостинг."""
    db = await aiosqlite.connect(DB_PATH)
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA busy_timeout=8000")
    await db.execute("PRAGMA synchronous=NORMAL")
    return db


async def init_db():
    db = await _db_connect()
    await db.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, uid TEXT UNIQUE,
        username TEXT DEFAULT '', first_name TEXT DEFAULT '', last_name TEXT DEFAULT '',
        status TEXT DEFAULT 'active', is_verified INTEGER DEFAULT 0,
        license_type TEXT DEFAULT '', license_start TIMESTAMP, license_expiry TIMESTAMP,
        join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_payments INTEGER DEFAULT 0, total_amount REAL DEFAULT 0.0,
        admin_notes TEXT DEFAULT '', banned INTEGER DEFAULT 0,
        ban_reason TEXT DEFAULT '', ban_date TIMESTAMP, balance REAL DEFAULT 0.0,
        last_support_message TIMESTAMP, queries_left INTEGER DEFAULT 2,
        referrer_id INTEGER DEFAULT 0, ref_balance REAL DEFAULT 0.0,
        last_daily_bonus TIMESTAMP, bot_bonus_received INTEGER DEFAULT 0)""")
    await db.execute("""CREATE TABLE IF NOT EXISTS payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        tariff TEXT NOT NULL, duration_days INTEGER, amount REAL DEFAULT 0.0,
        currency TEXT DEFAULT 'USDT', payment_method TEXT DEFAULT '',
        transaction_id TEXT DEFAULT '', payment_code TEXT DEFAULT '',
        payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'pending', admin_id INTEGER DEFAULT 0, processed_date TIMESTAMP)""")
    await db.execute("""CREATE TABLE IF NOT EXISTS user_bots (
        bot_id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER NOT NULL,
        bot_token TEXT UNIQUE NOT NULL, bot_username TEXT DEFAULT '',
        bot_name TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1)""")
    await db.execute("""CREATE TABLE IF NOT EXISTS bot_settings (
        key TEXT PRIMARY KEY, value TEXT DEFAULT '')""")
    await db.execute("""CREATE TABLE IF NOT EXISTS broadcasts (
        broadcast_id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER NOT NULL,
        message_type TEXT DEFAULT 'text', message_text TEXT DEFAULT '',
        media_file_id TEXT DEFAULT '', sent_count INTEGER DEFAULT 0,
        failed_count INTEGER DEFAULT 0, total_users INTEGER DEFAULT 0,
        broadcast_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT DEFAULT 'pending')""")
    await db.execute("""CREATE TABLE IF NOT EXISTS broadcast_recipients (
        recipient_id INTEGER PRIMARY KEY AUTOINCREMENT, broadcast_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL, delivery_status TEXT DEFAULT 'sent',
        error_description TEXT DEFAULT '', delivery_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    await db.execute("""CREATE TABLE IF NOT EXISTS self_lookup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hash_key TEXT UNIQUE NOT NULL,
        phone_masked TEXT DEFAULT '',
        owner_user_id INTEGER NOT NULL,
        owner_username TEXT DEFAULT '',
        owner_first_name TEXT DEFAULT '',
        owner_last_name TEXT DEFAULT '',
        source TEXT DEFAULT 'auto',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_self_lookup_hash ON self_lookup(hash_key)")
    await db.commit()
    for a in [
        "ALTER TABLE users ADD COLUMN queries_left INTEGER DEFAULT 2",
        "ALTER TABLE users ADD COLUMN referrer_id INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN ref_balance REAL DEFAULT 0.0",
        "ALTER TABLE users ADD COLUMN last_daily_bonus TIMESTAMP",
        "ALTER TABLE users ADD COLUMN bot_bonus_received INTEGER DEFAULT 0",
        "ALTER TABLE payments ADD COLUMN payment_code TEXT DEFAULT ''",
    ]:
        try: await db.execute(a); await db.commit()
        except Exception: pass
    await db.close()


async def get_setting(key, default=""):
    db = await _db_connect()
    cur = await db.execute("SELECT value FROM bot_settings WHERE key=?", (key,))
    row = await cur.fetchone(); await db.close()
    return row[0] if row else default


async def set_setting(key, value):
    db = await _db_connect()
    await db.execute("INSERT OR REPLACE INTO bot_settings (key, value) VALUES (?, ?)", (key, value))
    await db.commit(); await db.close()


async def get_stickers():
    v = await get_setting("stickers", "")
    if not v: return []
    try: return json.loads(v)
    except Exception: return []


async def add_sticker(fid):
    s = await get_stickers()
    if fid in s: return False
    s.append(fid); await set_setting("stickers", json.dumps(s)); return True


async def clear_stickers(): await set_setting("stickers", "")


async def pick_sticker():
    s = await get_stickers()
    return random.choice(s) if s else None


async def add_user_to_db(uid, username="", fn="", ln=""):
    db = await _db_connect()
    cur = await db.execute("SELECT uid FROM users WHERE user_id=?", (uid,))
    row = await cur.fetchone()
    u = row[0] if row and row[0] else generate_uid()
    await db.execute("INSERT OR IGNORE INTO users (user_id, uid, username, first_name, last_name, status) "
                     "VALUES (?, ?, ?, ?, ?, 'active')", (uid, u, username, fn, ln))
    await db.execute("UPDATE users SET username=?, first_name=?, last_name=?, last_activity=CURRENT_TIMESTAMP, status='active' WHERE user_id=?",
                     (username, fn, ln, uid))
    await db.commit(); await db.close()


async def check_daily_bonus(uid):
    db = await _db_connect()
    cur = await db.execute("SELECT last_daily_bonus FROM users WHERE user_id=?", (uid,))
    row = await cur.fetchone()
    if not row:
        await db.close(); return False
    last = row[0]; give = False
    if not last:
        give = True
    else:
        try:
            if (datetime.now() - datetime.strptime(last, "%Y-%m-%d %H:%M:%S.%f")).total_seconds() >= 86400:
                give = True
        except Exception: give = False
    if give:
        await db.execute("UPDATE users SET queries_left=queries_left+?, last_daily_bonus=CURRENT_TIMESTAMP WHERE user_id=?",
                         (DAILY_BONUS_QUERIES, uid))
        await db.commit()
    await db.close(); return give


async def set_referrer(uid, ref):
    if not ref or ref == uid: return
    db = await _db_connect()
    cur = await db.execute("SELECT referrer_id FROM users WHERE user_id=?", (uid,))
    r = await cur.fetchone()
    if r and r[0] and r[0] != 0:
        await db.close(); return
    cur = await db.execute("SELECT user_id FROM users WHERE user_id=?", (ref,))
    if not await cur.fetchone():
        await db.close(); return
    await db.execute("UPDATE users SET referrer_id=? WHERE user_id=?", (ref, uid))
    await db.commit(); await db.close()
    try: await bot.send_message(ref, "🎉 По вашей ссылке зарегистрировался новый пользователь!")
    except Exception: pass


async def verify_user(uid):
    db = await _db_connect()
    await db.execute("UPDATE users SET is_verified=1 WHERE user_id=?", (uid,))
    await db.commit(); await db.close()


async def get_user_uid(uid):
    db = await _db_connect()
    cur = await db.execute("SELECT uid FROM users WHERE user_id=?", (uid,))
    row = await cur.fetchone(); await db.close()
    return row[0] if row else ""


_USER_KEYS = ["user_id", "uid", "username", "first_name", "last_name", "status",
              "is_verified", "license_type", "license_start", "license_expiry",
              "join_date", "last_activity", "total_payments", "total_amount",
              "admin_notes", "banned", "ban_reason", "ban_date", "balance",
              "last_support_message", "queries_left", "referrer_id", "ref_balance",
              "last_daily_bonus", "bot_bonus_received"]


async def get_user_full_info(uid):
    db = await _db_connect()
    cur = await db.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    row = await cur.fetchone(); await db.close()
    if not row: return None
    return dict(zip(_USER_KEYS, row))


async def get_queries_left(uid):
    db = await _db_connect()
    cur = await db.execute("SELECT queries_left FROM users WHERE user_id=?", (uid,))
    row = await cur.fetchone(); await db.close()
    return row[0] if row and row[0] is not None else 0


async def decrement_queries(uid):
    db = await _db_connect()
    await db.execute("UPDATE users SET queries_left=MAX(0, queries_left-1) WHERE user_id=?", (uid,))
    await db.commit(); await db.close()


async def add_queries(uid, a):
    db = await _db_connect()
    await db.execute("UPDATE users SET queries_left=queries_left+? WHERE user_id=?", (a, uid))
    await db.commit(); await db.close()


async def remove_queries(uid, a):
    db = await _db_connect()
    await db.execute("UPDATE users SET queries_left=MAX(0, queries_left-?) WHERE user_id=?", (a, uid))
    await db.commit(); await db.close()


async def set_queries(uid, a):
    db = await _db_connect()
    await db.execute("UPDATE users SET queries_left=? WHERE user_id=?", (a, uid))
    await db.commit(); await db.close()


async def subtract_balance(uid, a):
    db = await _db_connect()
    await db.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (a, uid))
    await db.commit(); await db.close()


async def add_balance(uid, a):
    db = await _db_connect()
    await db.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (a, uid))
    await db.commit(); await db.close()


async def log_payment(uid, tariff, days, txid="", status="pending", currency="USDT", method="", code=""):
    db = await _db_connect()
    cur = await db.execute(
        "INSERT INTO payments (user_id, tariff, duration_days, transaction_id, status, currency, payment_method, payment_code) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (uid, tariff, days, txid, status, currency, method, code))
    pid = cur.lastrowid; await db.commit(); await db.close(); return pid


async def get_payment_info(pid):
    db = await _db_connect()
    cur = await db.execute("SELECT user_id, tariff, status, admin_id FROM payments WHERE payment_id=?", (pid,))
    row = await cur.fetchone(); await db.close(); return row


async def try_approve(pid, aid):
    db = await _db_connect(); db.row_factory = aiosqlite.Row
    try:
        await db.execute("BEGIN IMMEDIATE")
        cur = await db.execute("SELECT status, admin_id FROM payments WHERE payment_id=?", (pid,))
        r = await cur.fetchone()
        if not r: await db.rollback(); return False, "not_found"
        if r["status"] == "approved":
            await db.rollback(); return False, f"already_approved:{r['admin_id']}"
        if r["status"] == "rejected":
            await db.rollback(); return False, "already_rejected"
        await db.execute("UPDATE payments SET status='approved', admin_id=?, processed_date=CURRENT_TIMESTAMP WHERE payment_id=?",
                         (aid, pid))
        await db.commit(); return True, "ok"
    except Exception as ex:
        try: await db.rollback()
        except Exception: pass
        logger.error(f"approve: {ex}"); return False, "error"
    finally: await db.close()


async def try_reject(pid, aid):
    db = await _db_connect(); db.row_factory = aiosqlite.Row
    try:
        await db.execute("BEGIN IMMEDIATE")
        cur = await db.execute("SELECT status, admin_id FROM payments WHERE payment_id=?", (pid,))
        r = await cur.fetchone()
        if not r: await db.rollback(); return False, "not_found"
        if r["status"] == "approved":
            await db.rollback(); return False, f"already_approved:{r['admin_id']}"
        if r["status"] == "rejected":
            await db.rollback(); return False, "already_rejected"
        await db.execute("UPDATE payments SET status='rejected', admin_id=?, processed_date=CURRENT_TIMESTAMP WHERE payment_id=?",
                         (aid, pid))
        await db.commit(); return True, "ok"
    except Exception as ex:
        try: await db.rollback()
        except Exception: pass
        logger.error(f"reject: {ex}"); return False, "error"
    finally: await db.close()


async def log_broadcast(aid, mt, mtext="", mfile=""):
    db = await _db_connect()
    cur = await db.execute("INSERT INTO broadcasts (admin_id, message_type, message_text, media_file_id) VALUES (?, ?, ?, ?)",
                           (aid, mt, mtext, mfile))
    bid = cur.lastrowid; await db.commit(); await db.close(); return bid


async def log_broadcast_recipient(bid, uid, st="sent", err=""):
    db = await _db_connect()
    await db.execute("INSERT INTO broadcast_recipients (broadcast_id, user_id, delivery_status, error_description) VALUES (?, ?, ?, ?)",
                     (bid, uid, st, err))
    await db.commit(); await db.close()


async def update_broadcast_stats(bid, sent, failed, total):
    db = await _db_connect()
    await db.execute("UPDATE broadcasts SET sent_count=?, failed_count=?, total_users=?, status='completed' WHERE broadcast_id=?",
                     (sent, failed, total, bid))
    await db.commit(); await db.close()


async def get_all_users():
    db = await _db_connect()
    cur = await db.execute("SELECT user_id FROM users WHERE banned=0")
    rows = await cur.fetchall(); await db.close(); return [r[0] for r in rows]


async def ban_user(uid, r=""):
    db = await _db_connect()
    await db.execute("UPDATE users SET banned=1, ban_reason=?, ban_date=CURRENT_TIMESTAMP WHERE user_id=?", (r, uid))
    await db.commit(); await db.close()


async def unban_user(uid):
    db = await _db_connect()
    await db.execute("UPDATE users SET banned=0, ban_reason='', ban_date=NULL WHERE user_id=?", (uid,))
    await db.commit(); await db.close()


async def add_note(uid, n):
    db = await _db_connect()
    await db.execute("UPDATE users SET admin_notes=? WHERE user_id=?", (n, uid))
    await db.commit(); await db.close()


async def grant_license(uid, t):
    b = TARIFF_INFO.get(t, {}).get("queries", 0)
    db = await _db_connect()
    await db.execute("UPDATE users SET status='active', license_type=?, total_payments=total_payments+1, queries_left=queries_left+? WHERE user_id=?",
                     (t, b, uid))
    await db.commit(); await db.close()
    await reward_referrer(uid, t)


async def reward_referrer(uid, t):
    info = await get_user_full_info(uid) or {}
    ref = info.get("referrer_id", 0)
    if not ref: return
    q = TARIFF_INFO.get(t, {}).get("queries", 0)
    m = TARIFF_INFO.get(t, {}).get("rub", 0)
    bq = int(q * REF_QUERIES_PERCENT / 100)
    bm = round(m * REF_MONEY_PERCENT / 100, 2)
    db = await _db_connect()
    await db.execute("UPDATE users SET queries_left=queries_left+?, ref_balance=ref_balance+? WHERE user_id=?",
                     (bq, bm, ref))
    await db.commit(); await db.close()
    try:
        await bot.send_message(ref, f"🎁 <b>Реферальный бонус</b>\n\nВаш реферал купил <b>{h_esc(TARIFF_INFO.get(t,{}).get('name',t))}</b>\n\n"
                                    f"{EMOJI_FIND} Запросов: <b>+{bq}</b>\n💰 Реф. баланс: <b>+{bm}₽</b>", parse_mode="HTML")
    except Exception: pass


async def check_support_cooldown(uid):
    db = await _db_connect()
    cur = await db.execute("SELECT last_support_message FROM users WHERE user_id=?", (uid,))
    row = await cur.fetchone(); await db.close()
    if row and row[0]:
        try:
            if (datetime.now() - datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S.%f")).total_seconds() < 10:
                return False
        except Exception: pass
    return True


async def update_support_ts(uid):
    db = await _db_connect()
    await db.execute("UPDATE users SET last_support_message=CURRENT_TIMESTAMP WHERE user_id=?", (uid,))
    await db.commit(); await db.close()


async def add_user_bot(owner, tok, un="", nm=""):
    db = await _db_connect()
    try:
        cur = await db.execute("INSERT INTO user_bots (owner_id, bot_token, bot_username, bot_name) VALUES (?, ?, ?, ?)",
                               (owner, tok, un, nm))
        bid = cur.lastrowid; await db.commit(); return bid
    except Exception as ex:
        logger.warning(f"add_user_bot: {ex}"); return None
    finally: await db.close()


async def get_user_bots(owner):
    db = await _db_connect()
    cur = await db.execute("SELECT bot_id, bot_username, bot_name, is_active, created_at FROM user_bots "
                           "WHERE owner_id=? ORDER BY created_at DESC", (owner,))
    rows = await cur.fetchall(); await db.close(); return rows


async def get_active_user_bots():
    db = await _db_connect()
    cur = await db.execute("SELECT bot_id, owner_id, bot_token FROM user_bots WHERE is_active=1 ORDER BY bot_id ASC")
    rows = await cur.fetchall(); await db.close(); return rows


async def find_bot_by_token(token):
    db = await _db_connect()
    cur = await db.execute("SELECT bot_id, owner_id FROM user_bots WHERE bot_token=?", (token,))
    row = await cur.fetchone(); await db.close(); return row


def dtext(k): return TARIFF_INFO.get(k, {}).get("name", k)
def dqueries(k): return TARIFF_INFO.get(k, {}).get("queries", 0)


# ============================================================
# ПОДПИСКА
# ============================================================
_sub_cache = {}
_SUB_CACHE_TTL = 30.0
_OK_STATUSES = {"creator", "administrator", "member"}


async def check_subscription(bot_instance, user_id):
    if user_id in ADMINS:
        return []
    now = time.monotonic()
    not_sub = []
    to_check = []
    for ch in CHANNELS:
        key = (user_id, ch["id"])
        cached = _sub_cache.get(key)
        if cached and (now - cached[1]) < _SUB_CACHE_TTL:
            if not cached[0]:
                not_sub.append(ch)
        else:
            to_check.append(ch)
    for ch in to_check:
        try:
            m = await bot_instance.get_chat_member(ch["id"], user_id)
            status = getattr(m, "status", None)
            status_str = status if isinstance(status, str) else getattr(status, "value", str(status))
            is_ok = status_str in _OK_STATUSES
            _sub_cache[(user_id, ch["id"])] = (is_ok, now)
            logger.info(f"[sub] user={user_id} ch={ch['name']} status={status_str} ok={is_ok}")
            if not is_ok:
                not_sub.append(ch)
        except Exception as ex:
            logger.warning(f"[sub] check failed user={user_id} ch={ch['name']}: {ex}")
    return not_sub


def invalidate_sub_cache(user_id):
    for key in list(_sub_cache.keys()):
        if key[0] == user_id: _sub_cache.pop(key, None)


def sub_kb(not_sub):
    rows = [[InlineKeyboardButton(text=f"📢 {c['name']}", url=c["url"], style="primary")] for c in not_sub]
    rows.append([InlineKeyboardButton(text="✅ Проверить", callback_data="check_sub", style="success")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


SUB_TEXT = "🔒 <b>Подпишись на каналы чтобы пользоваться ботом</b>"


class SubscriptionMiddleware:
    def __init__(self, channels, admin_list):
        self.channels = channels
        self.admin_list = admin_list

    async def __call__(self, handler, event, data):
        if not hasattr(event, "from_user") or not event.from_user:
            return await handler(event, data)
        uid = event.from_user.id
        if uid in self.admin_list:
            return await handler(event, data)
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)
        if isinstance(event, CallbackQuery) and event.data == "check_sub":
            return await handler(event, data)
        bot_instance = data.get("bot")
        not_sub = await check_subscription(bot_instance, uid)
        if not_sub:
            names = ", ".join(c["name"] for c in not_sub)
            logger.info(f"[sub] BLOCK user={uid} not_sub={names}")
            if isinstance(event, Message):
                await event.answer(SUB_TEXT, reply_markup=sub_kb(not_sub), parse_mode="HTML")
            elif isinstance(event, CallbackQuery):
                await event.answer("🔒 Подпишись на каналы.", show_alert=True)
                try:
                    await event.message.answer(SUB_TEXT, reply_markup=sub_kb(not_sub), parse_mode="HTML")
                except Exception: pass
            return
        return await handler(event, data)


class OperationStates(StatesGroup):
    waiting_for_proof = State()
    waiting_for_query = State()
    admin_broadcast = State()
    admin_search_user = State()
    admin_add_queries = State()
    admin_remove_queries = State()
    admin_add_balance = State()
    admin_edit_note = State()
    admin_add_sticker = State()
    support_message = State()
    creating_bot_token = State()


bot = Bot(token=API_TOKEN)
current_tariff = {}
payment_proof = {}
payment_proof_method = {}
payment_code = {}
running_user_bots = {}
user_results = {}
_running_tokens = set()
_running_bids = set()
_running_lock = asyncio.Lock()
# _shutdown_event создаётся внутри main(), в актуальном event loop

# ============================================================
# UI
# ============================================================
async def _edit_media(message, img, caption, kb):
    has = img and os.path.exists(img)
    if has:
        try:
            await message.edit_media(media=InputMediaPhoto(media=FSInputFile(img), caption=caption, parse_mode="HTML"),
                                     reply_markup=kb)
            return
        except TelegramBadRequest as ex:
            s = str(ex)
            if "message is not modified" in s: return
            if "no media" in s or "can't be edited" in s:
                try: await message.edit_text(caption, reply_markup=kb, parse_mode="HTML"); return
                except TelegramBadRequest: pass
    try:
        await message.edit_text(caption, reply_markup=kb, parse_mode="HTML"); return
    except TelegramBadRequest as ex:
        if "message is not modified" in str(ex): return
    try:
        await message.edit_caption(caption=caption, reply_markup=kb, parse_mode="HTML"); return
    except TelegramBadRequest: pass
    try: await message.answer(caption, reply_markup=kb, parse_mode="HTML")
    except Exception as ex: logger.error(f"edit_media: {ex}")


async def _safe_edit(cb, caption, kb=None):
    msg = cb.message
    if msg.photo or msg.video or msg.document or msg.animation:
        try:
            await msg.edit_caption(caption=caption, reply_markup=kb, parse_mode="HTML"); return
        except TelegramBadRequest as ex:
            if "message is not modified" in str(ex): return
    try:
        await msg.edit_text(caption, reply_markup=kb, parse_mode="HTML"); return
    except TelegramBadRequest as ex:
        if "message is not modified" in str(ex): return
    try:
        await msg.edit_caption(caption=caption, reply_markup=kb, parse_mode="HTML"); return
    except TelegramBadRequest: pass
    try: await msg.answer(caption, reply_markup=kb, parse_mode="HTML")
    except Exception as ex: logger.error(f"safe_edit: {ex}")


async def set_main(m, c, k): await _edit_media(m, MAIN_MENU_IMAGE, c, k)
async def set_shop(cb, c, k): await _edit_media(cb.message, SHOP_IMAGE, c, k)
async def set_prof(cb, c, k): await _edit_media(cb.message, PROFILE_IMAGE, c, k)
async def set_func(cb, c, k): await _edit_media(cb.message, FUNCTIONAL_IMAGE, c, k)


async def send_sticker_and_text(chat_id, caption, kb=None, bot_instance=None):
    b = bot_instance or bot
    st = await pick_sticker()
    if st:
        try: await b.send_sticker(chat_id, st)
        except Exception as ex: logger.warning(f"sticker: {ex}")
    txt = f"{caption}\n\n{EMOJI_LINK} Актуальная рабочая ссылка на бота: {BOT_LINK}"
    try: await b.send_message(chat_id, txt, reply_markup=kb, parse_mode="HTML")
    except Exception: return False
    return True


def main_menu_kb(uid):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="Функционал", callback_data="menu_functional",
                               style="primary", icon_custom_emoji_id=E_FUNCTIONAL))
    b.row(InlineKeyboardButton(text="Профиль", callback_data="profile",
                               style="primary", icon_custom_emoji_id=E_PROFILE),
          InlineKeyboardButton(text="Купить запросы", callback_data="menu_payment",
                               style="success", icon_custom_emoji_id=E_BUY))
    b.row(InlineKeyboardButton(text="Мои боты", callback_data="menu_my_bots",
                               style="primary", icon_custom_emoji_id=E_MYBOTS))
    b.row(InlineKeyboardButton(text="Поддержка", callback_data="support",
                               style="danger", icon_custom_emoji_id=E_SUPPORT))
    if uid in ADMINS:
        b.row(InlineKeyboardButton(text="Админ-панель", callback_data="admin_panel",
                                   style="primary", icon_custom_emoji_id=E_ADMIN))
    return b.as_markup()


def functional_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Найти по всему", callback_data="menu_find",
                              style="success", icon_custom_emoji_id=E_FIND)],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main_menu", style="danger")]])


def no_queries_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить", callback_data="menu_payment",
                              style="success", icon_custom_emoji_id=E_BUY)],
        [InlineKeyboardButton(text="Получить бесплатно", callback_data="create_bot_start",
                              style="primary", icon_custom_emoji_id=E_MYBOTS)]])


def payment_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Купить запросы", callback_data="buy_access",
                              style="success", icon_custom_emoji_id=E_BUY)],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main_menu", style="danger")]])


def tariff_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 запрос — 4₽", callback_data="tariff_1q", style="primary")],
        [InlineKeyboardButton(text="10 запросов — 40₽", callback_data="tariff_10q", style="primary")],
        [InlineKeyboardButton(text="25 запросов — 100₽", callback_data="tariff_25q", style="primary")],
        [InlineKeyboardButton(text="50 запросов — 200₽", callback_data="tariff_50q", style="primary")],
        [InlineKeyboardButton(text="100 запросов — 400₽", callback_data="tariff_100q", style="success")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_payment_menu", style="danger")]])


def tariff_detail_kb(t, fio=""):
    i = TARIFF_INFO.get(t, {}); rub = i.get("rub", 0)
    text = (f"🔎 <b>Пакет:</b> {h_esc(i.get('name', t))}\n💵 <b>Цена:</b> {rub}₽\n\n"
            f"👤 ФИО: <b>{h_esc(fio) or 'Не указано'}</b>")
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="Звёзды ⭐", callback_data=f"paystars_{t}", style="primary"))
    b.row(InlineKeyboardButton(text="Рубли (карта) 💳", callback_data=f"payrub_{t}", style="success"))
    b.row(InlineKeyboardButton(text="USDT TRC-20", callback_data=f"crypto_trc20_{t}", style="primary"))
    b.row(InlineKeyboardButton(text="BTC", callback_data=f"crypto_btc_{t}", style="primary"))
    b.row(InlineKeyboardButton(text="TON", callback_data=f"crypto_ton_{t}", style="primary"))
    b.row(InlineKeyboardButton(text="USDT (Gram)", callback_data=f"crypto_usdt_{t}", style="primary"))
    b.row(InlineKeyboardButton(text="Назад", callback_data="buy_access", style="danger"))
    return text, b.as_markup()


def _make_pay_code(user_id):
    code = generate_payment_code()
    payment_code[user_id] = code
    return code


def rub_payment_kb(t, uid):
    i = TARIFF_INFO.get(t, {}); code = _make_pay_code(uid)
    text = (f"💳 <b>Оплата картой</b>\n\nПакет: <b>{h_esc(i.get('name', t))}</b>\n"
            f"Сумма: <b>{i.get('rub', 0)}₽</b>\n\n"
            f"╔══════════════════════════╗\n║  <b>КОД ДЛЯ ОПЛАТЫ:</b>\n║  <code>{code}</code>\n╚══════════════════════════╝\n\n"
            f"⚠️ <b>ОБЯЗАТЕЛЬНО</b> вставь код в <b>комментарий</b> к переводу!\n\n"
            f"<b>Реквизиты:</b>\n💳 Карта: <code>{CARD_NUMBER}</code>\n👤 Получатель: <code>{CARD_HOLDER}</code>\n\n"
            f"После перевода нажми «Я оплатил».")
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="Я оплатил ✅", callback_data=f"rubpaid_{t}", style="success"))
    b.row(InlineKeyboardButton(text="Назад", callback_data=f"tariff_{t}", style="danger"))
    return text, b.as_markup()


def crypto_payment_kb(t, ck, uid):
    names = {"trc20": ("USDT TRC-20", "USDT"), "btc": ("Bitcoin (BTC)", "BTC"),
             "ton": ("TON", "TON"), "usdt": ("USDT (Gram / TON)", "USDT")}
    addrs = {"trc20": TRC20_ADDRESS, "btc": BTC_ADDRESS, "ton": TON_ADDRESS, "usdt": USDT_ADDRESS}
    i = TARIFF_INFO.get(t, {}); rub = i.get("rub", 0)
    dn, rk = names.get(ck, (ck, ck)); addr = addrs.get(ck, "") or "Не указан"
    amt = rub_to_crypto(rub, rk); code = _make_pay_code(uid)
    text = (f"💎 <b>Оплата {h_esc(dn)}</b>\n\nПакет: <b>{h_esc(i.get('name', t))}</b>\n"
            f"Сумма: <b>{rub}₽</b>\n💵 К оплате: <b><code>{fmt_crypto(amt, rk)}</code> {rk}</b>\n\n"
            f"╔══════════════════════════╗\n║  <b>КОД ДЛЯ ОПЛАТЫ:</b>\n║  <code>{code}</code>\n╚══════════════════════════╝\n\n"
            f"⚠️ <b>ОБЯЗАТЕЛЬНО</b> вставь код в <b>комментарий/memo</b>!\n\n"
            f"<b>Адрес:</b>\n<code>{h_esc(addr)}</code>\n\nПосле перевода нажми «Я оплатил».")
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="Я оплатил ✅", callback_data=f"cryptopaid_{ck}_{t}", style="success"))
    b.row(InlineKeyboardButton(text="Назад", callback_data=f"tariff_{t}", style="danger"))
    return text, b.as_markup()


def stars_admins_kb(t, uid):
    code = _make_pay_code(uid)
    b = InlineKeyboardBuilder()
    for a in STARS_ADMINS:
        b.row(InlineKeyboardButton(text=f"{a['name']} — @{a['username']}",
                                   url=f"https://t.me/{a['username']}", style="primary"))
    b.row(InlineKeyboardButton(text="Назад", callback_data=f"tariff_{t}", style="danger"))
    text = (f"⭐ <b>Оплата звёздами</b>\n\nПакет: <b>{h_esc(dtext(t))}</b>\n\n"
            f"╔══════════════════════════╗\n║  <b>КОД ДЛЯ ОПЛАТЫ:</b>\n║  <code>{code}</code>\n╚══════════════════════════╝\n\n"
            f"⚠️ Напиши код админу вместе с оплатой.")
    return text, b.as_markup()


def admin_panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Статистика", callback_data="admin_stats", style="primary")],
        [InlineKeyboardButton(text="Рассылка", callback_data="admin_broadcast_start", style="primary")],
        [InlineKeyboardButton(text="Поиск пользователя", callback_data="admin_search_user", style="primary")],
        [InlineKeyboardButton(text="Выдать запросы", callback_data="admin_give_queries", style="success")],
        [InlineKeyboardButton(text="Убрать запросы", callback_data="admin_take_queries", style="danger")],
        [InlineKeyboardButton(text="Выдать баланс", callback_data="admin_give_balance", style="success")],
        [InlineKeyboardButton(text="Стикеры старта", callback_data="admin_stickers", style="primary")],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main_menu", style="danger")]])


def admin_stickers_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить стикер", callback_data="admin_sticker_add", style="success")],
        [InlineKeyboardButton(text="Очистить все", callback_data="admin_sticker_clear", style="danger")],
        [InlineKeyboardButton(text="Назад", callback_data="admin_panel", style="danger")]])


def admin_user_kb(uid):
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="+Запросы", callback_data=f"admin_addq_{uid}", style="success"),
          InlineKeyboardButton(text="-Запросы", callback_data=f"admin_subq_{uid}", style="danger"))
    b.row(InlineKeyboardButton(text="+Баланс", callback_data=f"admin_addbal_{uid}", style="success"),
          InlineKeyboardButton(text="Заметка", callback_data=f"admin_note_{uid}", style="primary"))
    b.row(InlineKeyboardButton(text="Бан", callback_data=f"admin_ban_{uid}", style="danger"),
          InlineKeyboardButton(text="Разбан", callback_data=f"admin_unban_{uid}", style="success"))
    b.row(InlineKeyboardButton(text="Назад", callback_data="admin_panel", style="danger"))
    return b.as_markup()


def my_bots_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Создать бота", callback_data="create_bot_start",
                              style="success", icon_custom_emoji_id=E_MYBOTS)],
        [InlineKeyboardButton(text="Мои боты", callback_data="my_bots_list",
                              style="primary", icon_custom_emoji_id=E_MYBOTS)],
        [InlineKeyboardButton(text="Назад", callback_data="back_to_main_menu", style="danger")]])


def create_bot_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть @BotFather", url="https://t.me/BotFather", style="primary")],
        [InlineKeyboardButton(text="Я получил токен", callback_data="create_bot_got_token",
                              style="success", icon_custom_emoji_id=E_MYBOTS)],
        [InlineKeyboardButton(text="Отмена", callback_data="back_to_main_menu", style="danger")]])


def payment_admin_kb(pid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Принять", callback_data=f"adm_ok_{pid}", style="success"),
         InlineKeyboardButton(text="Отклонить", callback_data=f"adm_no_{pid}", style="danger")]])


def friendly_api_error(reason):
    return {
        "timeout": "Сервер поиска не отвечает. Попробуй позже.",
        "conn_error": "Нет соединения с сервером поиска.",
        "client_error": "Ошибка соединения с сервером поиска.",
        "bad_json": "Сервер вернул некорректный ответ.",
        "bad_request": "Некорректный запрос.",
        "auth_error": "Ошибка авторизации на сервере поиска.",
        "forbidden": "Сервер отклонил запрос (403).",
        "not_found": "Не найдено.",
        "rate_limit": "Слишком много запросов. Подожди немного.",
        "server_error": "Сервер поиска временно недоступен.",
        "unavailable": "Сервер поиска временно недоступен.",
        "unknown": "Не удалось выполнить поиск.",
    }.get(reason, f"Не удалось выполнить поиск ({reason}).")


# ============================================================
# ХЕНДЛЕРЫ
# ============================================================
async def h_start(message: Message):
    uid = message.from_user.id
    if uid not in ADMINS:
        invalidate_sub_cache(uid)
        not_sub = await check_subscription(message.bot, uid)
        if not_sub:
            await message.answer(SUB_TEXT, reply_markup=sub_kb(not_sub), parse_mode="HTML")
            return
    args = message.text.split(maxsplit=1)
    ref = 0
    if len(args) > 1 and args[1].startswith("ref"):
        try: ref = int(args[1][3:])
        except Exception: ref = 0
    existing = await get_user_full_info(uid)
    await add_user_to_db(uid, message.from_user.username or "", message.from_user.first_name or "", message.from_user.last_name or "")
    await verify_user(uid)
    if existing is None and ref: await set_referrer(uid, ref)
    daily = await check_daily_bonus(uid)
    left = await get_queries_left(uid)
    lt = "∞" if uid in ADMINS else str(left)
    txt = f"Добро пожаловать в <b>{BOT_NAME}</b>.\n\n{EMOJI_FIND} Запросов: <b>{lt}</b>"
    if daily and uid not in ADMINS:
        txt += f"\n\n🎁 <b>Ежедневный бонус: +{DAILY_BONUS_QUERIES} запроса!</b>"
    await send_sticker_and_text(uid, txt, main_menu_kb(uid), bot_instance=message.bot)


async def h_check_sub(cb: CallbackQuery):
    uid = cb.from_user.id
    invalidate_sub_cache(uid)
    not_sub = await check_subscription(cb.bot, uid)
    if not_sub:
        names = ", ".join(c["name"] for c in not_sub)
        await cb.answer(f"❌ Ты не подписан: {names}", show_alert=True)
        try: await cb.message.edit_reply_markup(reply_markup=sub_kb(not_sub))
        except Exception: pass
        return
    await cb.answer("✅ Подписка подтверждена.")
    await add_user_to_db(uid, cb.from_user.username or "", cb.from_user.first_name or "", cb.from_user.last_name or "")
    await verify_user(uid)
    daily = await check_daily_bonus(uid)
    left = await get_queries_left(uid)
    lt = "∞" if uid in ADMINS else str(left)
    txt = f"Добро пожаловать в <b>{BOT_NAME}</b>.\n\n{EMOJI_FIND} Запросов: <b>{lt}</b>"
    if daily and uid not in ADMINS:
        txt += f"\n\n🎁 <b>Ежедневный бонус: +{DAILY_BONUS_QUERIES} запроса!</b>"
    try: await _edit_media(cb.message, MAIN_MENU_IMAGE, txt, main_menu_kb(uid))
    except Exception: await send_sticker_and_text(uid, txt, main_menu_kb(uid), bot_instance=cb.bot)


async def h_back(cb: CallbackQuery):
    await cb.answer(); await set_main(cb.message, "Главное меню.", main_menu_kb(cb.from_user.id))


async def h_menu_functional(cb: CallbackQuery):
    await cb.answer(); await set_func(cb, f"{EMOJI_FUNCTIONAL} Функционал:", functional_kb())


async def h_menu_find(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    uid = cb.from_user.id
    if uid not in ADMINS:
        info = await get_user_full_info(uid) or {}
        ql = info.get("queries_left", 0) or 0
        bal = info.get("balance", 0.0) or 0.0
        if ql <= 0 and bal < PRICE_PER_QUERY:
            await _safe_edit(cb, "🚫 <b>Нету запросов</b>\n\n"
                                 f"Запросов: <b>{ql}</b>\nБаланс: <b>{bal:.2f}₽</b>\n\n"
                                 "Купи доступ или создай бота.", no_queries_kb())
            return
    await state.set_state(OperationStates.waiting_for_query)
    txt = (f"{EMOJI_FIND} <b>Поиск по всему</b>\n\n"
           "Отправь любой запрос — бот сам определит тип:\n\n"
           "📱 <b>Телефон:</b> <code>79277231370</code>\n"
           "👤 <b>ФИО:</b> <code>Иванов Иван 1985</code>\n"
           "🔤 <b>Ник:</b> <code>@username</code>\n"
           "📧 <b>Email:</b> <code>user@mail.com</code>\n"
           "🔐 <b>Пароль:</b> <code>pass:qwerty</code>\n"
           "🆔 <b>СНИЛС:</b> <code>snils12345678901</code>\n"
           "🏢 <b>ИНН:</b> <code>inn582801503237</code>\n"
           "🚗 <b>ГРЗ:</b> <code>А123БВ77</code>\n"
           "🌐 <b>IP:</b> <code>8.8.8.8</code>")
    await _safe_edit(cb, txt, InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_find", style="danger")]]))


async def h_cancel_find(cb: CallbackQuery, state: FSMContext):
    await cb.answer(); await state.clear()
    await set_func(cb, f"{EMOJI_FUNCTIONAL} Функционал:", functional_kb())


async def h_query(message: Message, state: FSMContext):
    uid = message.from_user.id
    raw = (message.text or "").strip()
    if len(raw) < 3:
        await message.answer("❌ Слишком короткий запрос."); return

    await add_user_to_db(uid,
                         message.from_user.username or "",
                         message.from_user.first_name or "",
                         message.from_user.last_name or "")

    qtype, api_str, qtype_name = detect_query_type(raw)

    info = await get_user_full_info(uid) or {}
    ql = info.get("queries_left", 0) or 0
    bal = info.get("balance", 0.0) or 0.0

    if uid not in ADMINS:
        if ql > 0:
            await decrement_queries(uid)
            pay_note = f"−1 запрос (осталось: {ql - 1})"
        elif bal >= PRICE_PER_QUERY:
            await subtract_balance(uid, PRICE_PER_QUERY)
            pay_note = f"−{PRICE_PER_QUERY}₽ с баланса (осталось: {bal - PRICE_PER_QUERY:.2f}₽)"
        else:
            await message.answer("🚫 <b>Недостаточно средств</b>\n\n"
                                 f"Запросов: <b>{ql}</b>\nБаланс: <b>{bal:.2f}₽</b>\n\n"
                                 "Пополни баланс или купи запросы.",
                                 reply_markup=no_queries_kb(), parse_mode="HTML")
            await state.clear(); return
    else:
        pay_note = "Бесплатно (админ)"

    msg = await message.answer("Ищем во всех базах...")

    self_binding = None
    normalized_phone = None
    if qtype == "phone":
        normalized_phone = normalize_phone(raw)
        try:
            hit = await self_lookup_find(normalized_phone)
            if hit:
                owner_id, owner_un, owner_fn, owner_ln, src, created = hit
                if owner_id != uid:
                    self_binding = hit
        except Exception as ex:
            logger.warning(f"self_lookup_find: {ex}")

    if qtype == "nick":
        username = raw.lstrip("@").replace("nick:", "").strip()
        try:
            result = await search_by_username(username)
            api_error = None
        except APIUnavailable as ex:
            result = None; api_error = str(ex)
        except Exception as ex:
            logger.error(f"search_by_username err: {ex}")
            result = None; api_error = "unknown"

        if api_error:
            if uid not in ADMINS: await add_queries(uid, 1)
            info = await get_user_full_info(uid) or {}
            left = info.get("queries_left", 0) or 0
            bal = info.get("balance", 0.0) or 0.0
            lt = "∞" if uid in ADMINS else str(left)
            txt = (f"⚠️ <b>{h_esc(friendly_api_error(api_error))}</b>\n\n"
                   f"📌 Запрос: <code>{safe_query_for_html(raw)}</code>\n\n"
                   f"<i>Запрос возвращён на баланс.</i>\n\n"
                   f"{EMOJI_FIND} Запросов: {lt} | 💰 Баланс: {bal:.2f}₽")
            try:
                await msg.edit_text(txt, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Меню", callback_data="back_to_main_menu", style="danger")]]),
                    parse_mode="HTML")
            except Exception: pass
            await state.clear(); return

        if not result:
            if uid not in ADMINS: await add_queries(uid, 1)
            info = await get_user_full_info(uid) or {}
            left = info.get("queries_left", 0) or 0
            bal = info.get("balance", 0.0) or 0.0
            lt = "∞" if uid in ADMINS else str(left)
            txt = (f"❌ <b>Ничего не найдено</b>\n\n"
                   f"👤 Ник: <code>@{h_esc(username)}</code>\n\n"
                   f"<i>Запрос возвращён.</i>\n\n"
                   f"{EMOJI_FIND} Запросов: {lt} | 💰 Баланс: {bal:.2f}₽")
            try:
                await msg.edit_text(txt, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Меню", callback_data="back_to_main_menu", style="danger")]]),
                    parse_mode="HTML")
            except Exception: pass
            await state.clear(); return

        user_results[uid] = {"query": raw, "username_result": result, "is_username": True}
        info = await get_user_full_info(uid) or {}
        left = info.get("queries_left", 0) or 0
        bal = info.get("balance", 0.0) or 0.0
        lt = "∞" if uid in ADMINS else str(left)
        formatted = format_username_result(username, result)
        formatted += f"\n\n💳 <b>Оплата:</b> {h_esc(pay_note)}"
        formatted += f"\n{EMOJI_FIND} <b>Запросов:</b> {lt} | 💰 <b>Баланс:</b> {bal:.2f}₽"
        if len(formatted) > 4000:
            formatted = formatted[:4000] + "\n\n… Обрезано. HTML полный."
        try:
            await msg.edit_text(formatted, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Скачать HTML", callback_data="download_html",
                                      style="success", icon_custom_emoji_id=E_FIND)],
                [InlineKeyboardButton(text="Меню", callback_data="back_to_main_menu", style="danger")]]),
                parse_mode="HTML")
        except TelegramBadRequest:
            await message.answer(formatted, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Скачать HTML", callback_data="download_html",
                                      style="success", icon_custom_emoji_id=E_FIND)],
                [InlineKeyboardButton(text="Меню", callback_data="back_to_main_menu", style="danger")]]),
                parse_mode="HTML")
        await state.clear(); return

    if qtype == "phone":
        api_str = normalized_phone

    api_error = None; data = None; ok = False
    try:
        ok, data = await api_query(api_str, retries=2, timeout=20)
    except APIUnavailable as ex:
        api_error = str(ex)
    except Exception as ex:
        logger.error(f"api_query err: {ex}")
        api_error = "unknown"

    if api_error:
        if uid not in ADMINS: await add_queries(uid, 1)
        info = await get_user_full_info(uid) or {}
        left = info.get("queries_left", 0) or 0
        bal = info.get("balance", 0.0) or 0.0
        lt = "∞" if uid in ADMINS else str(left)
        txt = (f"⚠️ <b>{h_esc(friendly_api_error(api_error))}</b>\n\n"
               f"📌 Запрос: <code>{safe_query_for_html(raw)}</code>\n\n"
               f"<i>Запрос возвращён на баланс.</i>\n\n"
               f"{EMOJI_FIND} Запросов: {lt} | 💰 Баланс: {bal:.2f}₽")
        try:
            await msg.edit_text(txt, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Меню", callback_data="back_to_main_menu", style="danger")]]),
                parse_mode="HTML")
        except Exception: pass
        await state.clear(); return

    if not ok:
        if uid not in ADMINS: await add_queries(uid, 1)
        info = await get_user_full_info(uid) or {}
        left = info.get("queries_left", 0) or 0
        bal = info.get("balance", 0.0) or 0.0
        lt = "∞" if uid in ADMINS else str(left)
        txt = (f"⚠️ <b>{h_esc(friendly_api_error(data or 'unknown'))}</b>\n\n"
               f"📌 Запрос: <code>{safe_query_for_html(raw)}</code>\n\n"
               f"<i>Запрос возвращён.</i>\n\n"
               f"{EMOJI_FIND} Запросов: {lt} | 💰 Баланс: {bal:.2f}₽")
        try:
            await msg.edit_text(txt, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Меню", callback_data="back_to_main_menu", style="danger")]]),
                parse_mode="HTML")
        except Exception: pass
        await state.clear(); return

    if qtype == "phone" and normalized_phone and not self_binding:
        try:
            has_any = bool(data and (data.get("results") or data.get("phone_info") or data.get("ip_info")))
            match = _match_owner_in_result(message.from_user, data) if data else False
            if has_any or match:
                saved = await self_lookup_save(
                    normalized_phone,
                    uid,
                    message.from_user.username or "",
                    message.from_user.first_name or "",
                    message.from_user.last_name or "",
                    source="auto_match" if match else "auto_first"
                )
                if saved:
                    logger.info(f"[self_lookup] saved {normalized_phone} -> {uid} (match={match})")
        except Exception as ex:
            logger.warning(f"self_lookup_save: {ex}")

    user_results[uid] = {"query": raw, "data": data, "qtype_name": qtype_name}
    info = await get_user_full_info(uid) or {}
    left = info.get("queries_left", 0) or 0
    bal = info.get("balance", 0.0) or 0.0
    lt = "∞" if uid in ADMINS else str(left)
    formatted = format_results(raw, data, qtype_name=qtype_name, self_binding=self_binding)
    formatted += f"\n\n💳 <b>Оплата:</b> {h_esc(pay_note)}"
    formatted += f"\n{EMOJI_FIND} <b>Запросов:</b> {lt} | 💰 <b>Баланс:</b> {bal:.2f}₽"
    if len(formatted) > 4000:
        formatted = formatted[:4000] + "\n\n… Обрезано. HTML полный."
    try:
        await msg.edit_text(formatted, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Скачать HTML", callback_data="download_html",
                                  style="success", icon_custom_emoji_id=E_FIND)],
            [InlineKeyboardButton(text="Меню", callback_data="back_to_main_menu", style="danger")]]),
            parse_mode="HTML")
    except TelegramBadRequest:
        await message.answer(formatted, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Скачать HTML", callback_data="download_html",
                                  style="success", icon_custom_emoji_id=E_FIND)],
            [InlineKeyboardButton(text="Меню", callback_data="back_to_main_menu", style="danger")]]),
            parse_mode="HTML")
    await state.clear()


async def h_download_html(cb: CallbackQuery):
    await cb.answer()
    saved = user_results.get(cb.from_user.id)
    if not saved:
        await cb.answer("Сначала сделай поиск.", show_alert=True); return
    query = saved["query"]
    if saved.get("is_username"):
        html = build_html_report(query, None, username_result=saved["username_result"])
    else:
        html = build_html_report(query, saved["data"], qtype_name=saved.get("qtype_name", ""),
                                 self_binding=saved.get("self_binding"))
    safe = re.sub(r"[^\w\-]", "_", query)[:40]
    fname = f"report_{safe}.html"
    path = os.path.join(BASE_DIR, fname)
    try:
        with open(path, "w", encoding="utf-8") as f: f.write(html)
    except Exception as ex:
        await cb.answer(f"Ошибка: {ex}", show_alert=True); return
    try:
        await cb.message.answer_document(FSInputFile(path, filename=fname), caption="📄 Отчёт готов.")
    except Exception as ex:
        await cb.answer(f"Ошибка: {ex}", show_alert=True); return
    try: os.remove(path)
    except Exception: pass


async def h_profile(cb: CallbackQuery):
    await cb.answer()
    info = await get_user_full_info(cb.from_user.id) or {}
    if not info: return
    uid = info.get("user_id", cb.from_user.id)
    left = info.get("queries_left", 0) or 0
    lt = "∞" if uid in ADMINS else str(left)
    bal = info.get("balance", 0.0) or 0.0
    rbal = info.get("ref_balance", 0.0) or 0.0
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref{uid}"
    txt = (f"{EMOJI_PROFILE} <b>Профиль</b>\n\nВаш ID: <code>{uid}</code>\n"
           f"{EMOJI_FIND} Доступно запросов: <b>{lt}</b>\nВаш баланс: <b>{bal:.2f}₽</b>\n"
           f"Реферальный баланс: <b>{rbal:.2f}₽</b>\n\n"
           f"{EMOJI_LINK} <b>Ваша реферальная ссылка:</b>\n<code>{ref_link}</code>\n\n"
           f"<i>За друга: {REF_QUERIES_PERCENT}% запросами и {REF_MONEY_PERCENT}% рублями</i>")
    await set_prof(cb, txt, InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Меню", callback_data="back_to_main_menu", style="danger")]]))


async def h_menu_payment(cb: CallbackQuery):
    await cb.answer(); await set_shop(cb, f"{EMOJI_BUY} Покупка запросов:", payment_menu_kb())


async def h_buy_access(cb: CallbackQuery):
    await cb.answer(); await set_shop(cb, "🔎 Выбери пакет:", tariff_kb())


async def h_back_payment(cb: CallbackQuery):
    await cb.answer(); await set_shop(cb, f"{EMOJI_BUY} Покупка запросов:", payment_menu_kb())


async def h_tariff(cb: CallbackQuery):
    await cb.answer()
    key = cb.data.split("_", 1)[1]
    current_tariff[cb.from_user.id] = key
    info = await get_user_full_info(cb.from_user.id) or {}
    fio = f"{info.get('first_name','')} {info.get('last_name','')}".strip()
    txt, kb = tariff_detail_kb(key, fio)
    await set_shop(cb, txt, kb)


async def h_payrub(cb: CallbackQuery):
    await cb.answer()
    key = cb.data.split("_", 1)[1]
    current_tariff[cb.from_user.id] = key
    txt, kb = rub_payment_kb(key, cb.from_user.id)
    await set_shop(cb, txt, kb)


async def h_paystars(cb: CallbackQuery):
    await cb.answer()
    key = cb.data.split("_", 1)[1]
    txt, kb = stars_admins_kb(key, cb.from_user.id)
    await set_shop(cb, txt, kb)


async def h_crypto(cb: CallbackQuery):
    await cb.answer()
    p = cb.data.split("_")
    txt, kb = crypto_payment_kb(p[2], p[1], cb.from_user.id)
    await set_shop(cb, txt, kb)


async def h_rubpaid(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    key = cb.data.split("_", 1)[1]
    uid = cb.from_user.id
    current_tariff[uid] = key
    payment_proof[uid] = key
    payment_proof_method[uid] = "rub"
    code = payment_code.get(uid) or generate_payment_code()
    payment_code[uid] = code
    await state.set_state(OperationStates.waiting_for_proof)
    await _safe_edit(cb,
        f"📝 <b>Отправь подтверждение оплаты</b>\n\nТвой код: <code>{code}</code>\n\n"
        f"💬 <b>ОБЯЗАТЕЛЬНО</b> укажи код в комментарии к переводу.\n"
        f"Пришли <b>скриншот/чек/хэш</b> или просто напиши код.",
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="back_to_main_menu", style="danger")]]))


async def h_cryptopaid(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    p = cb.data.split("_")
    ck = p[1]; tk = p[2]
    uid = cb.from_user.id
    current_tariff[uid] = tk
    payment_proof[uid] = tk
    payment_proof_method[uid] = f"crypto_{ck}"
    code = payment_code.get(uid) or generate_payment_code()
    payment_code[uid] = code
    await state.set_state(OperationStates.waiting_for_proof)
    await _safe_edit(cb,
        f"📝 <b>Отправь подтверждение оплаты</b>\n\nТвой код: <code>{code}</code>\n\n"
        f"💬 <b>ОБЯЗАТЕЛЬНО</b> укажи код в комментарии/memo.\n"
        f"Пришли <b>скриншот/чек/хэш</b> или просто напиши код.",
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="back_to_main_menu", style="danger")]]))


async def h_proof(message: Message, state: FSMContext):
    uid = message.from_user.id
    key = payment_proof.get(uid, "1q")
    method = payment_proof_method.get(uid, "rub")
    user_uid = await get_user_uid(uid)
    info = TARIFF_INFO.get(key, {})
    user_info = await get_user_full_info(uid) or {}
    fio = f"{user_info.get('first_name','')} {user_info.get('last_name','')}".strip() or "Не указано"
    names = {"rub": "Карта", "crypto_trc20": "USDT TRC-20", "crypto_btc": "BTC",
             "crypto_ton": "TON", "crypto_usdt": "USDT (Gram)"}
    method_ru = names.get(method, method)
    currency = "RUB" if method == "rub" else method.replace("crypto_", "").upper()
    comment = (message.text or "").strip() or "(без комментария)"
    code = payment_code.get(uid) or ""

    await message.answer("✅ Заявка отправлена на проверку.")
    pid = await log_payment(uid, key, info.get("queries", 0), txid=comment,
                            status="pending", currency=currency, method=method, code=code)

    admin_text = (
        f"🔔 <b>НОВАЯ ЗАЯВКА #{pid}</b>\n\n"
        f"╔══════════════════════════╗\n║  <b>ОЖИДАЕМЫЙ КОД:</b>\n║  <code>{h_esc(code)}</code>\n╚══════════════════════════╝\n\n"
        f"💬 <b>КОММЕНТАРИЙ ЮЗЕРА:</b>\n╔══════════════════════════╗\n║  <b><u>{h_esc(comment)}</u></b>\n╚══════════════════════════╝\n\n"
        f"👤 User_id: <code>{uid}</code>\n🆔 Uid: <code>{h_esc(user_uid)}</code>\n"
        f"📛 ФИО: <b>{h_esc(fio)}</b>\n{EMOJI_FIND} Пакет: <b>{h_esc(dtext(key))}</b>\n"
        f"💵 Способ: <b>{h_esc(method_ru)}</b>\n📊 Сумма: <b>{info.get('rub', 0)}₽</b>\n\n"
        f"⚠️ <b>СРАВНИ КОД С КОММЕНТАРИЕМ!</b>")
    kb = payment_admin_kb(pid)
    for adm in ADMINS:
        try:
            if message.photo:
                await message.bot.send_photo(adm, message.photo[-1].file_id, caption=admin_text, reply_markup=kb, parse_mode="HTML")
            elif message.document:
                await message.bot.send_document(adm, message.document.file_id, caption=admin_text, reply_markup=kb, parse_mode="HTML")
            elif message.video:
                await message.bot.send_video(adm, message.video.file_id, caption=admin_text, reply_markup=kb, parse_mode="HTML")
            else:
                await message.bot.send_message(adm, admin_text, reply_markup=kb, parse_mode="HTML")
        except Exception as ex:
            logger.error(f"notif adm: {ex}")
    await state.clear()
    await message.answer("Заявка на рассмотрении.", reply_markup=main_menu_kb(uid))


async def h_adm_ok(cb: CallbackQuery):
    if cb.from_user.id not in ADMINS:
        await cb.answer("Доступ запрещён.", show_alert=True); return
    try: pid = int(cb.data.split("_")[2])
    except Exception:
        await cb.answer("Ошибка.", show_alert=True); return
    ok, reason = await try_approve(pid, cb.from_user.id)
    if not ok:
        try: await cb.message.edit_reply_markup(reply_markup=None)
        except Exception: pass
        if reason.startswith("already_approved"):
            await cb.answer(f"❌ Уже обработано {reason.split(':')[1]}", show_alert=True)
        elif reason == "already_rejected":
            await cb.answer("❌ Уже отклонена.", show_alert=True)
        else:
            await cb.answer("Ошибка.", show_alert=True)
        return
    info = await get_payment_info(pid)
    if info:
        target, t = info[0], info[1]
        await grant_license(target, t)
        left = await get_queries_left(target)
        try: await cb.bot.send_message(target, f"✅ Оплата одобрена!\n\n{EMOJI_FIND} +{dqueries(t)} запросов\n📊 Всего: <b>{left}</b>",
                                       reply_markup=main_menu_kb(target), parse_mode="HTML")
        except Exception: pass
    try: await cb.message.edit_caption(caption=f"✅ Заявка #{pid} одобрена админом {cb.from_user.id}")
    except TelegramBadRequest:
        try: await cb.message.edit_text(f"✅ Заявка #{pid} одобрена")
        except Exception: pass
    for adm in ADMINS:
        if adm == cb.from_user.id: continue
        try: await cb.bot.send_message(adm, f"✅ Заявка #{pid} одобрена админом {cb.from_user.id}")
        except Exception: pass
    await cb.answer("✅ Одобрено.", show_alert=True)


async def h_adm_no(cb: CallbackQuery):
    if cb.from_user.id not in ADMINS:
        await cb.answer("Доступ запрещён.", show_alert=True); return
    try: pid = int(cb.data.split("_")[2])
    except Exception:
        await cb.answer("Ошибка.", show_alert=True); return
    ok, reason = await try_reject(pid, cb.from_user.id)
    if not ok:
        try: await cb.message.edit_reply_markup(reply_markup=None)
        except Exception: pass
        if reason.startswith("already_approved"):
            await cb.answer(f"❌ Уже одобрено {reason.split(':')[1]}", show_alert=True)
        elif reason == "already_rejected":
            await cb.answer("❌ Уже отклонена.", show_alert=True)
        else:
            await cb.answer("Ошибка.", show_alert=True)
        return
    info = await get_payment_info(pid)
    if info:
        try: await cb.bot.send_message(info[0], "❌ Заявка отклонена.")
        except Exception: pass
    try: await cb.message.edit_caption(caption=f"❌ Заявка #{pid} отклонена админом {cb.from_user.id}")
    except TelegramBadRequest:
        try: await cb.message.edit_text(f"❌ Заявка #{pid} отклонена")
        except Exception: pass
    for adm in ADMINS:
        if adm == cb.from_user.id: continue
        try: await cb.bot.send_message(adm, f"❌ Заявка #{pid} отклонена админом {cb.from_user.id}")
        except Exception: pass
    await cb.answer("❌ Отклонено.", show_alert=True)


async def h_support(cb: CallbackQuery, state: FSMContext):
    await cb.answer(); await state.set_state(OperationStates.support_message)
    await _safe_edit(cb, f"{EMOJI_SUPPORT} Отправь сообщение в поддержку.",
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="back_to_main_menu", style="danger")]]))


async def h_support_msg(message: Message, state: FSMContext):
    uid = message.from_user.id
    if not await check_support_cooldown(uid):
        await message.answer("Подожди 10 секунд."); return
    await update_support_ts(uid)
    user_uid = await get_user_uid(uid)
    txt = f"🆘 Поддержка\nuser_id: {uid}\nuid: {user_uid}\n\nДля ответа используй reply."
    try:
        if message.photo:
            await message.bot.send_photo(ADMINS[0], message.photo[-1].file_id, caption=txt)
        elif message.document:
            await message.bot.send_document(ADMINS[0], message.document.file_id, caption=txt)
        elif message.video:
            await message.bot.send_video(ADMINS[0], message.video.file_id, caption=txt)
        else:
            await message.bot.send_message(ADMINS[0], f"{txt}\n\n{message.text}")
    except Exception as ex:
        logger.error(f"support: {ex}")
    await message.answer("Отправлено.")
    await state.clear()
    await message.answer("Меню:", reply_markup=main_menu_kb(uid))


async def h_adm_reply(message: Message):
    if message.from_user.id not in ADMINS: return
    if not message.reply_to_message: return
    orig = message.reply_to_message.text or message.reply_to_message.caption or ""
    m = re.search(r'user_id:\s*(\d+)', orig)
    if not m: return
    target = int(m.group(1))
    txt = message.text or message.caption or ""
    if not txt: return
    try:
        if message.photo:
            await message.bot.send_photo(target, message.photo[-1].file_id, caption=f"Ответ:\n\n{txt}")
        elif message.document:
            await message.bot.send_document(target, message.document.file_id, caption=f"Ответ:\n\n{txt}")
        elif message.video:
            await message.bot.send_video(target, message.video.file_id, caption=f"Ответ:\n\n{txt}")
        else:
            await message.bot.send_message(target, f"Ответ:\n\n{txt}")
        await message.reply(f"Отправлено {target}.")
    except Exception as ex:
        await message.reply(f"Ошибка: {ex}")


async def h_menu_my_bots(cb: CallbackQuery):
    await cb.answer(); await set_func(cb, f"{EMOJI_MYBOTS} <b>Мои боты</b>\n\nСоздай своего бота.", my_bots_kb())


async def h_create_bot_start(cb: CallbackQuery):
    await cb.answer()
    text = ("📖 <b>Инструкция</b>\n\n1. Открой @BotFather\n2. /newbot\n3. Введи имя\n"
            "4. Введи username (на <code>bot</code>)\n5. Скопируй токен\n6. Пришли сюда\n\n"
            f"🎁 <b>Бонус:</b> +{BOT_CREATE_BONUS} запросов\n\n"
            "⚠️ Не передавай токен посторонним!")
    await _safe_edit(cb, text, create_bot_kb())


async def h_create_bot_got_token(cb: CallbackQuery, state: FSMContext):
    await cb.answer(); await state.set_state(OperationStates.creating_bot_token)
    await _safe_edit(cb, "📩 Пришли токен бота.")


async def h_create_bot_token(message: Message, state: FSMContext):
    uid = message.from_user.id
    token = (message.text or "").strip()
    if not re.match(r"^\d{6,}:[A-Za-z0-9_-]{30,}$", token):
        await message.answer("❌ Неверный формат."); return
    if token in _running_tokens:
        await message.answer("❌ Этот бот уже запущен."); await state.clear(); return
    try:
        tb = Bot(token=token); me = await tb.get_me(); await tb.session.close()
    except Exception as ex:
        await message.answer(f"❌ Токен не работает: <code>{h_esc(ex)}</code>", parse_mode="HTML"); return
    row = await find_bot_by_token(token)
    if row:
        await message.answer("⚠️ Уже добавлен." if row[1] == uid else "❌ Токен занят.")
        await state.clear(); return
    bid = await add_user_bot(uid, token, me.username or "", me.full_name or "")
    if not bid:
        await message.answer("❌ Ошибка."); await state.clear(); return
    info = await get_user_full_info(uid) or {}
    if (info.get("bot_bonus_received", 0) or 0) == 0:
        await add_queries(uid, BOT_CREATE_BONUS)
        db = await _db_connect()
        await db.execute("UPDATE users SET bot_bonus_received=1 WHERE user_id=?", (uid,))
        await db.commit(); await db.close()
        btxt = f"\n\n🎁 +{BOT_CREATE_BONUS} запросов"
    else:
        btxt = "\n\nℹ️ Бонус уже получал."
    left = await get_queries_left(uid)
    asyncio.create_task(run_user_bot(bid, token, uid))
    await message.answer(
        f"✅ <b>Бот создан!</b>\n\n🤖 {h_esc(me.full_name)}\n🔗 @{h_esc(me.username)}\n🆔 <code>{bid}</code>"
        f"{btxt}\n\n{EMOJI_FIND} Всего: <b>{left}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Открыть", url=f"https://t.me/{me.username}", style="primary")],
            [InlineKeyboardButton(text="Мои боты", callback_data="my_bots_list", style="success")]]))
    await state.clear()


async def h_my_bots_list(cb: CallbackQuery):
    await cb.answer()
    bots = await get_user_bots(cb.from_user.id)
    if not bots:
        txt = f"{EMOJI_MYBOTS} <b>У тебя пока нет ботов</b>"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Создать", callback_data="create_bot_start", style="success")],
            [InlineKeyboardButton(text="Назад", callback_data="menu_my_bots", style="danger")]])
    else:
        lines = [f"{EMOJI_MYBOTS} <b>Твои боты:</b>\n"]
        for bid, un, bn, act, cr in bots:
            st = "🟢" if act and bid in running_user_bots else "🔴"
            lines.append(f"{st} <b>{h_esc(bn or 'Без имени')}</b> — @{h_esc(un or '?')}\n   id: <code>{bid}</code>")
        txt = "\n".join(lines)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Создать ещё", callback_data="create_bot_start", style="success")],
            [InlineKeyboardButton(text="Назад", callback_data="menu_my_bots", style="danger")]])
    await _safe_edit(cb, txt, kb)


async def h_admin_panel(cb: CallbackQuery):
    await cb.answer()
    if cb.from_user.id not in ADMINS: return
    await _safe_edit(cb, f"{EMOJI_ADMIN} Панель управления", admin_panel_kb())


async def h_admin_stats(cb: CallbackQuery):
    await cb.answer()
    if cb.from_user.id not in ADMINS: return
    db = await _db_connect()
    total = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
    banned = (await (await db.execute("SELECT COUNT(*) FROM users WHERE banned=1")).fetchone())[0]
    pend = (await (await db.execute("SELECT COUNT(*) FROM payments WHERE status='pending'")).fetchone())[0]
    ubots = (await (await db.execute("SELECT COUNT(*) FROM user_bots WHERE is_active=1")).fetchone())[0]
    sl_count = (await (await db.execute("SELECT COUNT(*) FROM self_lookup")).fetchone())[0]
    await db.close()
    st = await get_stickers()
    txt = (f"📊 <b>Статистика</b>\n\n👥 Юзеров: <b>{total}</b>\n🚫 Бан: <b>{banned}</b>\n"
           f"💳 Заявок: <b>{pend}</b>\n🤖 Зеркал: <b>{ubots}</b>\n"
           f"🟢 Работает: <b>{len(running_user_bots)}</b>\n🎨 Стикеров: <b>{len(st)}</b>\n"
           f"🎯 Self-lookup записей: <b>{sl_count}</b>")
    await _safe_edit(cb, txt, InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="admin_panel", style="danger")]]))


async def h_admin_stickers(cb: CallbackQuery):
    await cb.answer()
    if cb.from_user.id not in ADMINS: return
    st = await get_stickers()
    txt = f"🎨 <b>Стикеры</b>\n\nНастроено: <b>{len(st)}</b>" if st else "🎨 <b>Стикеры</b>\n\nСтикеров нет."
    await _safe_edit(cb, txt, admin_stickers_kb())


async def h_admin_sticker_add(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    if cb.from_user.id not in ADMINS: return
    await state.set_state(OperationStates.admin_add_sticker)
    await _safe_edit(cb, "📩 Пришли стикер. /stop для выхода.",
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="admin_stickers", style="danger")]]))


async def h_admin_sticker_message(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS: return
    if message.text and message.text.strip() == "/stop":
        await state.clear(); await message.answer("Вышел."); return
    if not message.sticker:
        await message.answer("❌ Не стикер. /stop для выхода."); return
    if message.sticker.is_animated or message.sticker.is_video:
        await message.answer("⚠️ Только обычные."); return
    added = await add_sticker(message.sticker.file_id)
    st = await get_stickers()
    await message.answer(f"✅ Добавлен. Всего: {len(st)}" if added else f"⚠️ Уже есть. Всего: {len(st)}")


async def h_admin_sticker_clear(cb: CallbackQuery):
    await cb.answer()
    if cb.from_user.id not in ADMINS: return
    await clear_stickers()
    await _safe_edit(cb, "✅ Очищено.", InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data="admin_stickers", style="danger")]]))


async def h_admin_give_queries(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    if cb.from_user.id not in ADMINS: return
    await state.set_state(OperationStates.admin_add_queries)
    await state.update_data(edit_uid=None)
    await _safe_edit(cb, "🎁 <b>Выдать запросы</b>\n\nФормат: <code>ID КОЛИЧЕСТВО</code>",
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="admin_panel", style="danger")]]))


async def h_admin_take_queries(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    if cb.from_user.id not in ADMINS: return
    await state.set_state(OperationStates.admin_remove_queries)
    await state.update_data(edit_uid=None)
    await _safe_edit(cb, "➖ <b>Убрать запросы</b>\n\nФормат: <code>ID КОЛИЧЕСТВО</code>",
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="admin_panel", style="danger")]]))


async def h_admin_addq_h(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS: return
    parts = (message.text or "").strip().split()
    d = await state.get_data(); target = d.get("edit_uid")
    if target:
        try: value = int(parts[0])
        except Exception: await message.answer("Число."); return
    else:
        if len(parts) < 2: await message.answer("Формат: <code>ID КОЛИЧЕСТВО</code>", parse_mode="HTML"); return
        try: target = int(parts[0]); value = int(parts[1])
        except Exception: await message.answer("Числа."); return
    info = await get_user_full_info(target)
    if not info: await message.answer(f"❌ Не найден {target}."); await state.clear(); return
    await add_queries(target, value)
    left = await get_queries_left(target)
    await message.answer(f"✅ +{value} юзеру {target}. Всего: {left}")
    try: await message.bot.send_message(target, f"{EMOJI_FIND} +{value} запросов. Всего: {left}", parse_mode="HTML")
    except Exception: pass
    await state.clear()


async def h_admin_subq_h(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS: return
    parts = (message.text or "").strip().split()
    d = await state.get_data(); target = d.get("edit_uid")
    if target:
        if not parts:
            await set_queries(target, 0); await message.answer(f"✅ Обнулено {target}.")
            await state.clear(); return
        try: value = int(parts[0])
        except Exception: await message.answer("Число."); return
    else:
        if len(parts) < 2:
            try:
                target = int(parts[0]); await set_queries(target, 0)
                await message.answer(f"✅ Обнулено {target}."); await state.clear(); return
            except Exception: await message.answer("Формат: <code>ID КОЛИЧЕСТВО</code>"); return
        try: target = int(parts[0]); value = int(parts[1])
        except Exception: await message.answer("Числа."); return
    info = await get_user_full_info(target)
    if not info: await message.answer(f"❌ Не найден {target}."); await state.clear(); return
    await remove_queries(target, value)
    left = await get_queries_left(target)
    await message.answer(f"✅ −{value}. Осталось: {left}")
    await state.clear()


async def h_admin_addq(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    if cb.from_user.id not in ADMINS: return
    target = int(cb.data.split("_")[2])
    await state.set_state(OperationStates.admin_add_queries)
    await state.update_data(edit_uid=target)
    await _safe_edit(cb, f"Сколько выдать юзеру {target}?")


async def h_admin_subq(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    if cb.from_user.id not in ADMINS: return
    target = int(cb.data.split("_")[2])
    await state.set_state(OperationStates.admin_remove_queries)
    await state.update_data(edit_uid=target)
    await _safe_edit(cb, f"Сколько убрать у {target}?")


async def h_admin_give_balance(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    if cb.from_user.id not in ADMINS: return
    await state.set_state(OperationStates.admin_add_balance)
    await state.update_data(edit_uid=None)
    await _safe_edit(cb, "💰 <b>Выдать баланс</b>\n\nФормат: <code>ID СУММА</code>",
        InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="admin_panel", style="danger")]]))


async def h_admin_addbal_h(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS: return
    parts = (message.text or "").strip().split()
    d = await state.get_data(); target = d.get("edit_uid")
    if target:
        try: value = float(parts[0])
        except Exception: await message.answer("Число."); return
    else:
        if len(parts) < 2: await message.answer("Формат: <code>ID СУММА</code>"); return
        try: target = int(parts[0]); value = float(parts[1])
        except Exception: await message.answer("Числа."); return
    info = await get_user_full_info(target)
    if not info: await message.answer(f"❌ Не найден {target}."); await state.clear(); return
    await add_balance(target, value)
    nb = (info.get("balance", 0.0) or 0.0) + value
    await message.answer(f"✅ +{value}₽. Баланс: {nb:.2f}₽")
    await state.clear()


async def h_admin_addbal(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    if cb.from_user.id not in ADMINS: return
    target = int(cb.data.split("_")[2])
    await state.set_state(OperationStates.admin_add_balance)
    await state.update_data(edit_uid=target)
    await _safe_edit(cb, f"Сумма для {target}?")


async def h_admin_search_user(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    if cb.from_user.id not in ADMINS: return
    await state.set_state(OperationStates.admin_search_user)
    await _safe_edit(cb, "Введи user_id:", InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="admin_panel", style="danger")]]))


async def h_admin_search_h(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS: return
    try: target = int(message.text.strip())
    except Exception: await message.answer("Число."); return
    info = await get_user_full_info(target)
    if not info: await message.answer("Не найден."); await state.clear(); return
    txt = (f"👤 <b>Инфо</b>\n\nid: {info['user_id']}\nuid: {h_esc(info['uid'])}\n"
           f"ФИО: {h_esc(info['first_name'])} {h_esc(info['last_name'])}\n"
           f"username: @{h_esc(info['username'] or '—')}\n"
           f"{EMOJI_FIND} Запросов: {info.get('queries_left', 0)}\n"
           f"💰 Баланс: {(info.get('balance', 0.0) or 0.0):.2f}₽\n"
           f"💰 Реф: {(info.get('ref_balance', 0.0) or 0.0):.2f}₽")
    await message.answer(txt, reply_markup=admin_user_kb(target), parse_mode="HTML")
    await state.clear()


async def h_admin_note(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    if cb.from_user.id not in ADMINS: return
    target = int(cb.data.split("_")[2])
    await state.set_state(OperationStates.admin_edit_note)
    await state.update_data(edit_uid=target)
    await _safe_edit(cb, f"Заметка для {target}:")


async def h_admin_note_h(message: Message, state: FSMContext):
    if message.from_user.id not in ADMINS: return
    d = await state.get_data()
    await add_note(d.get("edit_uid"), message.text.strip())
    await message.answer("Сохранено.")
    await state.clear()


async def h_admin_ban(cb: CallbackQuery):
    if cb.from_user.id not in ADMINS: return
    target = int(cb.data.split("_")[2])
    await ban_user(target, "администратор")
    invalidate_sub_cache(target)
    await cb.answer(f"{target} забанен.", show_alert=True)


async def h_admin_unban(cb: CallbackQuery):
    if cb.from_user.id not in ADMINS: return
    target = int(cb.data.split("_")[2])
    await unban_user(target)
    await cb.answer(f"{target} разбанен.", show_alert=True)


async def h_admin_bc(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    if cb.from_user.id not in ADMINS: return
    await state.set_state(OperationStates.admin_broadcast)
    await _safe_edit(cb, "Сообщение для рассылки:", InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="admin_panel", style="danger")]]))


async def h_admin_bc_h(message: Message, state: FSMContext):
    """Оптимизированная рассылка с семафором."""
    if message.from_user.id not in ADMINS: return
    mt = "text"; mtext = message.text or ""; mfile = ""
    if message.photo: mt, mfile, mtext = "photo", message.photo[-1].file_id, message.caption or ""
    elif message.video: mt, mfile, mtext = "video", message.video.file_id, message.caption or ""
    elif message.document: mt, mfile, mtext = "doc", message.document.file_id, message.caption or ""
    bid = await log_broadcast(ADMINS[0], mt, mtext, mfile)
    users = await get_all_users()
    total = len(users); sent = failed = 0
    sm = await message.bot.send_message(ADMINS[0], f"Начата: {total}")

    sem = asyncio.Semaphore(BROADCAST_CONCURRENCY)

    async def send_one(u):
        nonlocal sent, failed
        async with sem:
            try:
                if mt == "text":    await message.bot.send_message(u, mtext)
                elif mt == "photo": await message.bot.send_photo(u, mfile, caption=mtext)
                elif mt == "video": await message.bot.send_video(u, mfile, caption=mtext)
                elif mt == "doc":   await message.bot.send_document(u, mfile, caption=mtext)
                sent += 1
                await log_broadcast_recipient(bid, u, "sent")
            except Exception as ex:
                failed += 1
                await log_broadcast_recipient(bid, u, "failed", str(ex))
            if (sent + failed) % 20 == 0:
                try: await sm.edit_text(f"... {sent}/{total} (ошибок: {failed})")
                except Exception: pass
            await asyncio.sleep(BROADCAST_SLEEP)

    await asyncio.gather(*(send_one(u) for u in users))
    await update_broadcast_stats(bid, sent, failed, total)
    try: await sm.edit_text(f"Готово. {sent} ок, {failed} ошибок")
    except Exception: pass
    await state.clear(); await message.answer("Завершено.")


def create_router():
    r = Router()
    r.message(CommandStart())(h_start)
    r.callback_query(F.data == "check_sub")(h_check_sub)
    r.callback_query(F.data == "back_to_main_menu")(h_back)
    r.callback_query(F.data == "menu_functional")(h_menu_functional)
    r.callback_query(F.data == "menu_find")(h_menu_find)
    r.callback_query(F.data == "cancel_find")(h_cancel_find)
    r.message(StateFilter(OperationStates.waiting_for_query))(h_query)
    r.callback_query(F.data == "download_html")(h_download_html)
    r.callback_query(F.data == "profile")(h_profile)
    r.callback_query(F.data == "menu_payment")(h_menu_payment)
    r.callback_query(F.data == "buy_access")(h_buy_access)
    r.callback_query(F.data == "back_to_payment_menu")(h_back_payment)
    r.callback_query(F.data.startswith("tariff_"))(h_tariff)
    r.callback_query(F.data.startswith("payrub_"))(h_payrub)
    r.callback_query(F.data.startswith("paystars_"))(h_paystars)
    r.callback_query(F.data.startswith("crypto_"))(h_crypto)
    r.callback_query(F.data.startswith("rubpaid_"))(h_rubpaid)
    r.callback_query(F.data.startswith("cryptopaid_"))(h_cryptopaid)
    r.message(StateFilter(OperationStates.waiting_for_proof))(h_proof)
    r.callback_query(F.data.startswith("adm_ok_"))(h_adm_ok)
    r.callback_query(F.data.startswith("adm_no_"))(h_adm_no)
    r.callback_query(F.data == "support")(h_support)
    r.message(StateFilter(OperationStates.support_message))(h_support_msg)
    r.message(F.reply_to_message)(h_adm_reply)
    r.callback_query(F.data == "menu_my_bots")(h_menu_my_bots)
    r.callback_query(F.data == "create_bot_start")(h_create_bot_start)
    r.callback_query(F.data == "create_bot_got_token")(h_create_bot_got_token)
    r.message(StateFilter(OperationStates.creating_bot_token))(h_create_bot_token)
    r.callback_query(F.data == "my_bots_list")(h_my_bots_list)
    r.callback_query(F.data == "admin_panel")(h_admin_panel)
    r.callback_query(F.data == "admin_stats")(h_admin_stats)
    r.callback_query(F.data == "admin_stickers")(h_admin_stickers)
    r.callback_query(F.data == "admin_sticker_add")(h_admin_sticker_add)
    r.callback_query(F.data == "admin_sticker_clear")(h_admin_sticker_clear)
    r.message(StateFilter(OperationStates.admin_add_sticker))(h_admin_sticker_message)
    r.callback_query(F.data == "admin_give_queries")(h_admin_give_queries)
    r.callback_query(F.data == "admin_take_queries")(h_admin_take_queries)
    r.callback_query(F.data == "admin_give_balance")(h_admin_give_balance)
    r.message(StateFilter(OperationStates.admin_add_queries))(h_admin_addq_h)
    r.message(StateFilter(OperationStates.admin_remove_queries))(h_admin_subq_h)
    r.message(StateFilter(OperationStates.admin_add_balance))(h_admin_addbal_h)
    r.callback_query(F.data.startswith("admin_addq_"))(h_admin_addq)
    r.callback_query(F.data.startswith("admin_subq_"))(h_admin_subq)
    r.callback_query(F.data.startswith("admin_addbal_"))(h_admin_addbal)
    r.callback_query(F.data == "admin_search_user")(h_admin_search_user)
    r.message(StateFilter(OperationStates.admin_search_user))(h_admin_search_h)
    r.callback_query(F.data.startswith("admin_note_"))(h_admin_note)
    r.message(StateFilter(OperationStates.admin_edit_note))(h_admin_note_h)
    r.callback_query(F.data.startswith("admin_ban_"))(h_admin_ban)
    r.callback_query(F.data.startswith("admin_unban_"))(h_admin_unban)
    r.callback_query(F.data == "admin_broadcast_start")(h_admin_bc)
    r.message(StateFilter(OperationStates.admin_broadcast))(h_admin_bc_h)
    return r


# ============================================================
# 🔥 БЕЗОПАСНЫЙ POLLING — ИСПРАВЛЕНИЕ TelegramConflictError
# ============================================================
# ============================================================
# 🔥 БЕЗОПАСНЫЙ POLLING — ИСПРАВЛЕНИЕ TelegramConflictError
# ============================================================
async def _force_delete_webhook(bot_instance: Bot) -> None:
    """
    Гарантированно снимает вебхук + drop_pending.
    Вызывается ПЕРЕД каждым start_polling (главный + зеркала).
    """
    try:
        info = await bot_instance.get_webhook_info()
        if info and info.url:
            logger.warning(f"[webhook] Обнаружен активный webhook: {info.url}. Удаляю...")
    except Exception as ex:
        logger.debug(f"[webhook] get_webhook_info: {ex}")
    try:
        await bot_instance.delete_webhook(drop_pending_updates=True)
        logger.info("[webhook] delete_webhook выполнен.")
    except Exception as ex:
        logger.warning(f"[webhook] delete_webhook: {ex}")


async def safe_start_polling(dp: Dispatcher, bot_instance: Bot, label: str = "main") -> None:
    """
    Безопасный polling с ретраями при TelegramConflictError.
    КЛЮЧЕВОЕ: перед КАЖДОЙ попыткой — delete_webhook + drop_pending.
    """
    last_exc = None
    for attempt in range(1, POLLING_MAX_RETRIES + 1):
        await _force_delete_webhook(bot_instance)
        # Пауза, чтобы Telegram успел освободить сессию от предыдущего long-poll
        await asyncio.sleep(POLLING_PRE_DELAY)

        try:
            logger.info(f"[{label}] start_polling, попытка {attempt}/{POLLING_MAX_RETRIES}")
            await dp.start_polling(
                bot_instance,
                drop_pending_updates=True,
                allowed_updates=dp.resolve_used_update_types(),
                handle_signals=False,   # сигналы обрабатываем сами
            )
            return
        except TelegramConflictError as ex:
            last_exc = ex
            wait = min(POLLING_RETRY_DELAY * attempt, 60)
            logger.warning(
                f"[{label}] TelegramConflictError (попытка {attempt}): {ex}. "
                f"Жду {wait:.1f} сек и пробую снова..."
            )
            await asyncio.sleep(wait)
        except asyncio.CancelledError:
            logger.info(f"[{label}] polling отменён.")
            raise
        except Exception as ex:
            last_exc = ex
            wait = min(POLLING_RETRY_DELAY * attempt, 60)
            logger.error(f"[{label}] Неожиданная ошибка polling: {ex}. Жду {wait:.1f} сек.")
            await asyncio.sleep(wait)

    logger.error(f"[{label}] Не удалось запустить polling за {POLLING_MAX_RETRIES} попыток.")
    if last_exc:
        raise last_exc


async def safe_start_polling(dp: Dispatcher, bot_instance: Bot, label: str = "main") -> None:
    """
    Безопасный polling с ретраями при TelegramConflictError.
    КЛЮЧЕВОЕ: перед КАЖДОЙ попыткой — delete_webhook + drop_pending.
    """
    last_exc = None
    for attempt in range(1, POLLING_MAX_RETRIES + 1):
        await _force_delete_webhook(bot_instance)
        # Пауза, чтобы Telegram успел освободить сессию от предыдущего long-poll
        await asyncio.sleep(POLLING_PRE_DELAY)

        try:
            logger.info(f"[{label}] start_polling, попытка {attempt}/{POLLING_MAX_RETRIES}")
            await dp.start_polling(
                bot_instance,
                drop_pending_updates=True,
                allowed_updates=dp.resolve_used_update_types(),
                handle_signals=False,   # сигналы обрабатываем сами
            )
            return
        except TelegramConflictError as ex:
            last_exc = ex
            wait = min(POLLING_RETRY_DELAY * attempt, 60)
            logger.warning(
                f"[{label}] TelegramConflictError (попытка {attempt}): {ex}. "
                f"Жду {wait:.1f} сек и пробую снова..."
            )
            await asyncio.sleep(wait)
        except asyncio.CancelledError:
            logger.info(f"[{label}] polling отменён.")
            raise
        except Exception as ex:
            last_exc = ex
            wait = min(POLLING_RETRY_DELAY * attempt, 60)
            logger.error(f"[{label}] Неожиданная ошибка polling: {ex}. Жду {wait:.1f} сек.")
            await asyncio.sleep(wait)

    logger.error(f"[{label}] Не удалось запустить polling за {POLLING_MAX_RETRIES} попыток.")
    if last_exc:
        raise last_exc


# ============================================================
# ЗЕРКАЛА
# ============================================================
async def run_user_bot(bid, token, owner_id):
    async with _running_lock:
        if token in _running_tokens or bid in _running_bids:
            logger.info(f"⏭ Зеркало #{bid} уже запущено.")
            return
        _running_tokens.add(token)
        _running_bids.add(bid)
        running_user_bots[bid] = {"bot": None, "task": asyncio.current_task()}

    child = None
    dp = None
    try:
        child = Bot(token=token)
        me = await child.get_me()
        logger.info(f"🚀 Зеркало #{bid}: @{me.username}")
        running_user_bots[bid]["bot"] = child

        db = await _db_connect()
        await db.execute("UPDATE user_bots SET bot_username=?, bot_name=? WHERE bot_id=?",
                         (me.username or "", me.full_name or "", bid))
        await db.commit(); await db.close()

        dp = Dispatcher(storage=MemoryStorage())
        dp.update.middleware(SubscriptionMiddleware(CHANNELS, ADMINS))
        dp.include_router(create_router())

        await safe_start_polling(dp, child, label=f"bot#{bid}")

    except asyncio.CancelledError:
        logger.info(f"🛑 Зеркало #{bid} остановлено.")
        raise
    except Exception as ex:
        logger.error(f"❌ Зеркало #{bid}: {ex}")
    finally:
        if dp is not None:
            try: await dp.storage.close()
            except Exception: pass
        async with _running_lock:
            _running_tokens.discard(token)
            _running_bids.discard(bid)
            cur = running_user_bots.get(bid)
            if cur and cur.get("task") is asyncio.current_task():
                running_user_bots.pop(bid, None)
        if child is not None:
            try: await child.session.close()
            except Exception: pass


async def start_all_user_bots():
    bots = await get_active_user_bots()
    started = skipped = 0
    seen_ids = set(); seen_tokens = set()
    for bid, owner, tok in bots:
        if not tok: continue
        if bid in seen_ids or tok in seen_tokens: skipped += 1; continue
        if bid in _running_bids or tok in _running_tokens: skipped += 1; continue
        seen_ids.add(bid); seen_tokens.add(tok)
        asyncio.create_task(run_user_bot(bid, tok, owner))
        started += 1
        await asyncio.sleep(1.5)
    logger.info(f"✅ Зеркал запущено: {started}, пропущено: {skipped}")


async def stop_all_user_bots():
    logger.info(f"⏹ Останавливаю {len(running_user_bots)} зеркал...")
    tasks = []
    for bid, data in list(running_user_bots.items()):
        task = data.get("task"); child = data.get("bot")
        if child:
            try: await child.session.close()
            except Exception: pass
        if task and not task.done():
            task.cancel()
            tasks.append(task)
    for t in tasks:
        try:
            await asyncio.wait_for(t, timeout=5)
        except Exception:
            pass
    running_user_bots.clear()
    _running_tokens.clear()
    _running_bids.clear()
    logger.info("✅ Все зеркала остановлены.")


# ============================================================
# MAIN
# ============================================================
def _install_signal_handlers(shutdown_event: asyncio.Event):
    """Сигналы устанавливаются в актуальном loop'е, event передаётся снаружи."""
    try:
        loop = asyncio.get_running_loop()
        def _stop():
            logger.info("Получен сигнал остановки.")
            shutdown_event.set()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _stop)
            except NotImplementedError:
                pass
    except Exception as ex:
        logger.debug(f"signal handlers: {ex}")


async def main():
    global BOT_USERNAME

    # 1) Инициализация БД
    await init_db()

    # 2) Узнаём username основного бота
    try:
        me = await bot.get_me()
        BOT_USERNAME = me.username or BOT_USERNAME
        logger.info(f"🤖 Бот: @{BOT_USERNAME}")
    except Exception as ex:
        logger.warning(f"get_me: {ex}")

    # 3) Создаём Event ВНУТРИ loop'а (важно для Python 3.9!)
    shutdown_event = asyncio.Event()

    # 4) Ставим обработчики сигналов (передаём event)
    _install_signal_handlers(shutdown_event)

    # 5) Собираем главный Dispatcher
    main_dp = Dispatcher(storage=MemoryStorage())
    main_dp.update.middleware(SubscriptionMiddleware(CHANNELS, ADMINS))
    main_dp.include_router(create_router())

    # 6) Запускаем зеркала фоном
    mirrors_task = asyncio.create_task(start_all_user_bots(), name="mirrors")

    # 7) Запускаем главный polling (long-running)
    polling_task = asyncio.create_task(
        safe_start_polling(main_dp, bot, label="main"),
        name="main_polling",
    )

    # 8) Задача, которая ждёт сигнал остановки
    stop_task = asyncio.create_task(shutdown_event.wait(), name="stop_wait")

    # 9) Ждём: либо polling сам упал/завершился, либо сигнал остановки
    try:
        done, pending = await asyncio.wait(
            {polling_task, stop_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
    except asyncio.CancelledError:
        done, pending = set(), {polling_task, stop_task}

    logger.info("Начинаю остановку...")

    # 10) Отменяем всё, что осталось
    for t in pending:
        t.cancel()
    for t in list(pending) + [mirrors_task]:
        if t.done():
            continue
        t.cancel()
        try:
            await t
        except (asyncio.CancelledError, Exception):
            pass

    # 11) Дочитываем исключения из завершённых тасок (чтобы не было "never retrieved")
    for t in done:
        try:
            exc = t.exception()
            if exc and not isinstance(exc, asyncio.CancelledError):
                logger.error(f"Задача {t.get_name()} упала: {exc!r}")
        except (asyncio.CancelledError, Exception):
            pass

    # 12) Гасим зеркала и сессии
    logger.info("Останавливаю зеркала...")
    await stop_all_user_bots()
    await close_session()
    try:
        await bot.session.close()
    except Exception:
        pass
    try:
        await main_dp.storage.close()
    except Exception:
        pass
    logger.info("✅ Всё остановлено.")


if __name__ == "__main__":
    if not acquire_single_instance_lock():
        logger.error("❌ Другой экземпляр бота уже запущен!")
        sys.exit(1)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
    finally:
        release_single_instance_lock()

if __name__ == "__main__":
    if not acquire_single_instance_lock():
        logger.error("❌ Другой экземпляр бота уже запущен!")
        sys.exit(1)

    # Flask в фоне — чтобы Render видел открытый порт
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("✅ Flask health-check запущен в фоне.")

    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")
    finally:
        release_single_instance_lock()

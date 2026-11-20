import asyncio
import time
import httpx
import json
import os
import sys
import threading
import zlib

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass
from collections import defaultdict
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from cachetools import TTLCache
from google.protobuf import json_format
from Crypto.Cipher import AES
import base64
import pickle
from datetime import datetime

# ============= PATH FIX =============
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
proto_dir = os.path.join(project_dir, 'proto')
if proto_dir not in sys.path:
    sys.path.insert(0, proto_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

try:
    from proto import FreeFire_pb2, main_pb2, AccountPersonalShow_pb2
    print("✅ Proto files imported successfully")
except ImportError:
    try:
        import FreeFire_pb2, main_pb2, AccountPersonalShow_pb2
        print("✅ Proto files imported directly")
    except ImportError as e:
        print(f"❌ Proto import error: {e}")
        sys.exit(1)

# === Settings ===
MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV  = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')
RELEASEVERSION = "OB55"
USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 9; ASUS_Z01QD Build/PI)"
REGION_PRIORITY = ["BR", "US", "ME", "BD", "IND", "SG", "ID", "TH", "VN", "PK", "EU"]
SUPPORTED_REGIONS = set(REGION_PRIORITY)
TOKEN_CACHE_FILE = '/tmp/token_cache.pkl'
IMAGE_BASE_URL = "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG/"

app = Flask(
    __name__,
    template_folder=os.path.join(project_dir, 'templates'),
    static_folder=os.path.join(project_dir, 'static')
)
CORS(app)
cache = TTLCache(maxsize=100, ttl=300)
token_manager = None

# === Pool de Contas (BR / US via uidpass.json com Fallback nativo) ===
UIDPASS_PATH = os.path.join(project_dir, 'uidpass.json')
FALLBACK_ACCOUNTS_BR = [
    {"uid": "5437930135", "password": "BR_TG_@VISWAJEETHU_AikwF46W"},
    {"uid": "5438234260", "password": "BR_TG_@VISWAJEETHU_AikwF46W"},
]
account_pool_br = []
pool_cursor = 0
pool_lock = threading.Lock()

if os.path.exists(UIDPASS_PATH):
    try:
        with open(UIDPASS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                account_pool_br = [acc for acc in data if isinstance(acc, dict) and 'uid' in acc and 'password' in acc]
    except Exception as e:
        print(f"[WARN] Erro ao carregar uidpass.json: {e}")

if not account_pool_br:
    print("ℹ️ Usando contas de fallback do código (uidpass.json não encontrado ou vazio)")
    account_pool_br = list(FALLBACK_ACCOUNTS_BR)

def get_next_br_account():
    global pool_cursor
    with pool_lock:
        pool = account_pool_br if account_pool_br else FALLBACK_ACCOUNTS_BR
        acc = pool[pool_cursor % len(pool)]
        pool_cursor = (pool_cursor + 1) % len(pool)
        return acc.get('uid', '5437930135'), acc.get('password', 'BR_TG_@VISWAJEETHU_AikwF46W')

def get_account_credentials(region: str) -> tuple:
    r = region.upper()
    if r in {"BR", "US", "SAC", "NA"}:
        return get_next_br_account()
    elif r == "IND":
        return "4363983977", "ISHITA_0AFN5_BY_SPIDEERIO_GAMING_UY12H"
    elif r == "ME":
        return "4269012488", "MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"
    elif r == "BD":
        return "4270778393", "MG24_GAMER_9NMYG_BY_SPIDEERIO_GAMING_FXK8R"
    else:
        return "4418979127", "RIZER_K4CY1_RIZER_WNX02"

# === Helper Functions ===
def pad(text: bytes) -> bytes:
    n = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([n] * n)

def aes_cbc_encrypt(key, iv, plaintext):
    return AES.new(key, AES.MODE_CBC, iv).encrypt(pad(plaintext))

def build_game_data_minimo(open_id, access_token, platform_type=4):
    def varint(v):
        out = bytearray()
        while True:
            byte = v & 0x7F
            v >>= 7
            out.append(byte | (0x80 if v else 0))
            if not v:
                return bytes(out)
    def f_str(num, valor):
        b = str(valor).encode('utf-8')
        return varint((num << 3) | 2) + varint(len(b)) + b
    return f_str(22, open_id) + f_str(29, access_token) + f_str(99, str(platform_type))

async def native_major_login(uid, password, region):
    oauth_url = "https://100067.connect.garena.com/oauth/guest/token/grant"
    payload = {
        'uid': uid,
        'password': password,
        'response_type': "token",
        'client_type': "2",
        'client_secret': "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        'client_id': "100067"
    }
    headers_oauth = {
        'User-Agent': "GarenaMSDK/4.0.19P9(SM-M526B ;Android 13;pt;BR;)",
        'Connection': "Keep-Alive",
        'Accept-Encoding': "gzip"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            r = await client.post(oauth_url, data=payload, headers=headers_oauth)
            if r.status_code != 200:
                return None
            data = r.json()
            open_id = data.get('open_id')
            access_token = data.get('access_token')
            if not open_id or not access_token:
                return None
            
            login_urls = [
                "https://loginbp.ppmainecoonghj.com/MajorLogin",
                "https://loginbp.ggblueshark.com/MajorLogin"
            ]
            headers_login = {
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; A063 Build/TKQ1.221220.001)",
                "Connection": "Keep-Alive",
                "Accept-Encoding": "gzip",
                "Content-Type": "application/x-www-form-urlencoded",
                "Expect": "100-continue",
                "X-Unity-Version": "2018.4.11f1",
                "X-GA": "v1 1",
                "X-GA-SV": "1789638359",
                "ReleaseVersion": RELEASEVERSION
            }
            for url in login_urls:
                for platform in [4, 1, 2]:
                    edata = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, build_game_data_minimo(open_id, access_token, platform))
                    try:
                        resp = await client.post(url, data=edata, headers=headers_login, timeout=5.0)
                        if resp.status_code == 200:
                            content = resp.content
                            offset = 64 if len(content) > 64 and content[64] == 0x08 else 0
                            login_res = FreeFire_pb2.LoginRes()
                            login_res.ParseFromString(content[offset:])
                            if login_res.token:
                                server_url = login_res.server_url or (
                                    'https://client.ind.freefiremobile.com' if region == 'IND' else 'https://client.us.freefiremobile.com'
                                )
                                return {
                                    'token': f"Bearer {login_res.token}",
                                    'region': login_res.lock_region or region,
                                    'server_url': server_url,
                                    'expires_at': time.time() + 25200
                                }
                    except Exception:
                        continue
    except Exception:
        pass
    return None

# === Token Manager ===
class TokenManager:
    def __init__(self, cache_file=TOKEN_CACHE_FILE):
        self.tokens = {}
        self.lock = threading.RLock()
        self.cache_file = cache_file
        self.load_tokens()

    def load_tokens(self):
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    saved = pickle.load(f)
                    now = time.time()
                    for r, info in saved.items():
                        if info.get('expires_at', 0) > now:
                            self.tokens[r] = info
                            print(f"✅ Loaded cached token: {r}")
        except Exception as e:
            print(f"❌ Load tokens error: {e}")

    def save_tokens(self):
        try:
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
            with open(self.cache_file, 'wb') as f:
                pickle.dump(dict(self.tokens), f)
        except Exception as e:
            print(f"❌ Save tokens error: {e}")

    async def get_token(self, region: str, force_refresh: bool = False):
        with self.lock:
            info = self.tokens.get(region)
            if not force_refresh and info and info.get('expires_at', 0) > time.time() + 60:
                return info

        new_token = await self.generate_token(region)
        if not new_token:
            return None

        with self.lock:
            self.tokens[region] = new_token
            self.save_tokens()
        return new_token

    async def generate_token(self, region: str):
        uid, password = get_account_credentials(region)
        headers = {"User-Agent": USERAGENT, "Accept": "application/json"}

        # 1. Autenticação direta nativa da Garena
        token_info = await native_major_login(uid, password, region)
        if token_info:
            print(f"✅ Token generated via Garena: {region}")
            return token_info

        # 2. ShardWeb Token API (fallback)
        try:
            token_url = f"https://tokenapi.shardweb.app/token?uid={uid}&password={password}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(token_url, headers=headers)
                if resp.status_code == 200:
                    msg = resp.json()
                    tok = msg.get('token')
                    if tok and len(str(tok).split('.')) == 3:
                        server_url = msg.get('serverUrl') or msg.get('server_url') or (
                            'https://client.ind.freefiremobile.com' if region == 'IND' else 'https://client.us.freefiremobile.com'
                        )
                        token_info = {
                            'token': f"Bearer {tok}",
                            'region': msg.get('region') or region,
                            'server_url': server_url,
                            'expires_at': msg.get('expiry_time', time.time() + 25200)
                        }
                        print(f"✅ Token generated via ShardWeb: {region}")
                        return token_info
        except Exception as e:
            print(f"⚠️ ShardWeb token attempt error [{region}]: {e}")

        return None

    async def refresh_all_tokens(self):
        tasks = [self.get_token(r, force_refresh=True) for r in REGION_PRIORITY]
        await asyncio.gather(*tasks)
        self.save_tokens()

def get_token_manager():
    global token_manager
    if token_manager is None:
        token_manager = TokenManager()
    return token_manager

async def GetAccountInformation(uid, region, endpoint="/GetPlayerPersonalShow", max_retries=3):
    req = main_pb2.GetPlayerPersonalShow()
    req.a = int(uid)
    req.b = 1  # garena = 1 (OB55)
    data_enc = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, req.SerializeToString())

    tm = get_token_manager()
    for attempt in range(max_retries):
        force_new = (attempt > 0)
        token_info = await tm.get_token(region, force_refresh=force_new)
        if not token_info:
            continue
        token = token_info['token']
        server_url = token_info['server_url']

        headers = {
            'User-Agent': USERAGENT,
            'Connection': "Keep-Alive",
            'Accept': "*/*",
            'Accept-Encoding': "gzip",
            'Expect': "100-continue",
            'Authorization': token,
            'X-Unity-Version': "2018.4.12f1",
            'X-GA': "v1 1",
            'X-GA-SV': "1789638359",
            'ReleaseVersion': RELEASEVERSION,
            'Content-Type': "application/x-www-form-urlencoded"
        }

        try:
            print(f"📡 Requesting info for UID {uid} via {region} (attempt {attempt+1})...")
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(server_url + endpoint, data=data_enc, headers=headers)
                
                if resp.status_code in {401, 429}:
                    print(f"⚠️ Rate limit / auth {resp.status_code} for {region}, rotating account...")
                    with tm.lock:
                        tm.tokens.pop(region, None)
                    continue

                if resp.status_code != 200:
                    print(f"❌ API {resp.status_code} for {region}")
                    return None

                body = resp.content
                if resp.headers.get('content-encoding') == 'gzip' or (len(body) > 2 and body[0] == 0x1f and body[1] == 0x8b):
                    body = zlib.decompress(body, 16 + zlib.MAX_WBITS)

                account_info = AccountPersonalShow_pb2.AccountPersonalShowInfo()
                account_info.ParseFromString(body)
                result = json.loads(json_format.MessageToJson(account_info))
                if not result.get("basicInfo"):
                    print(f"⚠️ UID {uid} not found via {region}")
                    return None
                print(f"✅ Info received for UID {uid} from {region}")
                return result
        except Exception as e:
            print(f"❌ GetAccountInformation error attempt {attempt+1}: {e}")
            continue

    return None

def build_image_url(item_id):
    if item_id in (None, "", 0, "0"):
        return None
    return f"{IMAGE_BASE_URL}{item_id}.png"

def build_image_items(item_ids):
    if not isinstance(item_ids, list):
        return []
    return [
        {"id": str(item_id), "image": build_image_url(item_id)}
        for item_id in item_ids
        if item_id not in (None, "", 0, "0")
    ]

def format_response(data):
    if not data:
        return {"error": "No data"}
    basic   = data.get("basicInfo", {})
    profile = data.get("profileInfo", {})
    clan    = data.get("clanBasicInfo", {})
    social  = data.get("socialInfo", {})
    avatar_id = basic.get("headPic", "0")
    weapons = basic.get("weaponSkinShows", [])
    outfits = profile.get("clothes", [])
    return {
        "AccountInfo": {
            "AccountAvatarId":   str(avatar_id),
            "AccountAvatarImage": build_image_url(avatar_id),
            "AccountBPBadges":   str(basic.get("badgeCnt", "0")),
            "AccountBPID":       str(basic.get("badgeId", "0")),
            "AccountBannerId":   str(basic.get("bannerId", "0")),
            "AccountCreateTime": str(basic.get("createAt", "0")),
            "AccountEXP":        str(basic.get("exp", "0")),
            "AccountLastLogin":  str(basic.get("lastLoginAt", "0")),
            "AccountLevel":      str(basic.get("level", "0")),
            "AccountLikes":      str(basic.get("liked", "0")),
            "AccountName":       basic.get("nickname", "Unknown"),
            "AccountRegion":     basic.get("region", "Unknown"),
            "AccountSeasonId":   str(basic.get("seasonId", "0")),
            "AccountType":       str(basic.get("accountType", "0")),
            "BrMaxRank":         str(basic.get("maxRank", "0")),
            "BrRankPoint":       str(basic.get("rankingPoints", "0")),
            "CsMaxRank":         str(basic.get("csMaxRank", "0")),
            "CsRankPoint":       str(basic.get("csRankingPoints", "0")),
            "EquippedWeapon":    weapons,
            "EquippedWeaponImages": build_image_items(weapons),
            "ReleaseVersion":    basic.get("releaseVersion", RELEASEVERSION),
            "ShowBrRank":        str(basic.get("showBrRank", "0")),
            "ShowCsRank":        str(basic.get("showCsRank", "0")),
            "Title":             str(basic.get("title", "0"))
        },
        "AccountProfileInfo": {
            "EquippedOutfit": outfits,
            "EquippedOutfitImages": build_image_items(outfits),
            "EquippedSkills": profile.get("equipedSkills", [])
        },
        "GuildInfo": {
            "GuildCapacity": str(clan.get("capacity", "0")),
            "GuildID":       str(clan.get("clanId", "0")),
            "GuildLevel":    str(clan.get("clanLevel", "0")),
            "GuildMember":   str(clan.get("memberNum", "0")),
            "GuildName":     clan.get("clanName", "No Guild"),
            "GuildOwner":    str(clan.get("captainId", "0"))
        },
        "captainBasicInfo": data.get("captainBasicInfo", {}),
        "creditScoreInfo":  data.get("creditScoreInfo", {}),
        "petInfo":          data.get("petInfo", {}),
        "socialinfo": {
            "accountId": str(social.get("accountId", "0")),
            "language":  social.get("language", "en_US")
        }
    }

# === Routes ===
@app.route('/')
def home():
    return render_template('index.html')

async def find_account_across_regions(uid, regions, overall_timeout):
    semaphore = asyncio.Semaphore(4)
    timed_out = False

    async def attempt(region):
        async with semaphore:
            try:
                data = await asyncio.wait_for(
                    GetAccountInformation(uid, region),
                    timeout=12.0
                )
                return region, data
            except asyncio.TimeoutError:
                print(f"⏱️ Region {region} timed out")
                return region, None

    tasks = [asyncio.create_task(attempt(region)) for region in regions]
    try:
        for completed in asyncio.as_completed(tasks, timeout=overall_timeout):
            region, data = await completed
            if data:
                return data, region, False
    except asyncio.TimeoutError:
        timed_out = True
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    return None, None, timed_out

@app.route('/get')
def get_account_info():
    uid = request.args.get('uid')
    region_param = request.args.get('region', '').upper()
    if not uid:
        return jsonify({"error": "UID obrigatório"}), 400
    if region_param and region_param not in SUPPORTED_REGIONS:
        return jsonify({"error": "Região inválida"}), 400

    regions_to_try = [region_param] if region_param else REGION_PRIORITY
    overall_timeout = 15.0 if region_param else 25.0
    mode = region_param or "AUTOMÁTICA"
    print(f"\n🔍 Processing UID {uid} in mode {mode}")

    try:
        data, resolved_region, timed_out = asyncio.run(
            find_account_across_regions(uid, regions_to_try, overall_timeout)
        )
    except Exception as exc:
        print(f"❌ Search error: {exc}")
        return jsonify({"error": "Falha ao consultar o jogador"}), 500

    if data:
        response = format_response(data)
        response["SearchInfo"] = {
            "RequestedRegion": region_param or "AUTO",
            "ResolvedRegion": resolved_region
        }
        return jsonify(response)

    if timed_out:
        return jsonify({
            "error": "A busca demorou demais. Tente novamente ou selecione uma região específica."
        }), 504

    return jsonify({"error": "Jogador não encontrado nas regiões consultadas"}), 404

@app.route('/status')
def token_status():
    tm = get_token_manager()
    status = {}
    with tm.lock:
        tokens_copy = dict(tm.tokens)
    for region, info in tokens_copy.items():
        expires_in = info['expires_at'] - time.time()
        status[region] = {
            "has_token": True,
            "expires_in": f"{expires_in/3600:.1f} hours",
            "server_url": info['server_url'][:50] + "..."
        }
    return jsonify({
        "region_priority": REGION_PRIORITY,
        "total_tokens": len(tokens_copy),
        "tokens": status
    })

@app.route('/refresh')
def refresh_tokens():
    tm = get_token_manager()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(tm.refresh_all_tokens())
    loop.close()
    return jsonify({"status": "refreshed", "count": len(tm.tokens)})

@app.route('/test/<region>')
def test_region(region):
    region = region.upper()
    if region not in SUPPORTED_REGIONS:
        return jsonify({"error": f"Region {region} not supported"})
    tm = get_token_manager()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    token = loop.run_until_complete(tm.get_token(region))
    loop.close()
    if token:
        return jsonify({"region": region, "status": "Token ready",
                        "expires_in": f"{(token['expires_at']-time.time())/3600:.1f} hours"})
    return jsonify({"region": region, "status": "Token generation failed"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

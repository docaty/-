import json
import os
import urllib.parse
import urllib.request

NICO_USER_ID = "9940944"

API_URL = "https://live.nicovideo.jp/front/api/v2/user-broadcast-history"
STATE_FILE = "last_live.txt"

params = {
    "providerId": NICO_USER_ID,
    "providerType": "user",
    "isIncludeNonPublic": "false",
    "offset": 0,
    "limit": 10,
    "withTotalCount": "true",
}

url = API_URL + "?" + urllib.parse.urlencode(params)

request = urllib.request.Request(
    url,
    headers={
        "User-Agent": "Mozilla/5.0",
        "X-Frontend-Id": "9",
        "X-Frontend-Version": "0",
    },
)

with urllib.request.urlopen(request, timeout=15) as response:
    data = json.load(response)

programs = data.get("data", {}).get("programsList", [])

# 現在ON_AIRの番組を探す
live_program = next(
    (
        program
        for program in programs
        if program.get("program", {})
        .get("schedule", {})
        .get("status") == "ON_AIR"
    ),
    None,
)

# 現在放送していなければ終了
if live_program is None:
    print("現在放送していません")
    raise SystemExit

live_id = live_program.get("id", {}).get("value")

if not live_id:
    print("lv番号を取得できませんでした")
    raise SystemExit

# 前回通知したlv番号を読む
try:
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        last_live_id = f.read().strip()
except FileNotFoundError:
    last_live_id = ""

# 同じ放送なら何もしない
if live_id == last_live_id:
    print(f"{live_id} は通知済みです")
    raise SystemExit

live_url = f"https://live.nicovideo.jp/watch/{live_id}"

message = {
    "content": (
        "🔴 ニコニコ生放送が始まりました！\n"
        f"{live_url}"
    )
}

webhook_url = os.environ["DISCORD_WEBHOOK_URL"]

discord_request = urllib.request.Request(
    webhook_url,
    data=json.dumps(message, ensure_ascii=False).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "User-Agent": "NiconicoLiveNotifier",
    },
    method="POST",
)

with urllib.request.urlopen(discord_request, timeout=15):
    pass

# Discordへの送信に成功してから記録
with open(STATE_FILE, "w", encoding="utf-8") as f:
    f.write(live_id)

print(f"通知しました: {live_url}")

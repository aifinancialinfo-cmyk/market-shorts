"""今後の米国経済指標（日本時間・予想・前回）を取る。
データ元: Forex Factory のカレンダーJSON（無料・キー不要）。取れない日は空リストを返す。
"""
import datetime as dt, json, re, urllib.request
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
WD = "月火水木金土日"
URLS = ["https://nfs.faireconomy.media/ff_calendar_thisweek.json",
        "https://nfs.faireconomy.media/ff_calendar_nextweek.json"]

# よく出る指標の日本語名（左から順に部分一致で探す）
NAMES = [
    ("ADP Non-Farm", "ADP雇用統計", "エーディーピー雇用統計"),
    ("Non-Farm Employment Change", "米雇用統計（NFP）", "米雇用統計"),
    ("Unemployment Rate", "失業率", "失業率"),
    ("Unemployment Claims", "新規失業保険申請件数", "新規失業保険申請件数"),
    ("Average Hourly Earnings", "平均時給", "平均時給"),
    ("Core CPI", "コアCPI（消費者物価）", "コア消費者物価指数"),
    ("CPI", "CPI（消費者物価指数）", "消費者物価指数"),
    ("Core PPI", "コアPPI（生産者物価）", "コア生産者物価指数"),
    ("PPI", "PPI（生産者物価指数）", "生産者物価指数"),
    ("Core PCE", "コアPCE物価指数", "コアピーシーイー物価指数"),
    ("PCE", "PCE物価指数", "ピーシーイー物価指数"),
    ("ISM Services PMI", "ISMサービス業PMI", "アイエスエム非製造業景況指数"),
    ("ISM Manufacturing PMI", "ISM製造業PMI", "アイエスエム製造業景況指数"),
    ("Retail Sales", "小売売上高", "小売売上高"),
    ("Federal Funds Rate", "FOMC政策金利", "エフオーエムシーの政策金利"),
    ("FOMC", "FOMC", "エフオーエムシー"),
    ("Fed Chair", "パウエル議長発言", "FRB議長の発言"),
    ("Advance GDP", "GDP速報値", "GDP速報値"),
    ("GDP", "GDP", "GDP"),
    ("JOLTS", "JOLTS求人件数", "ジョルツ求人件数"),
    ("Trade Balance", "貿易収支", "貿易収支"),
    ("UoM Consumer Sentiment", "ミシガン大消費者信頼感", "ミシガン大学消費者信頼感指数"),
    ("UoM Inflation Expectations", "ミシガン大期待インフレ率", "ミシガン大学期待インフレ率"),
    ("CB Consumer Confidence", "消費者信頼感指数", "消費者信頼感指数"),
    ("Durable Goods", "耐久財受注", "耐久財受注"),
    ("Pending Home Sales", "中古住宅販売保留", "中古住宅販売保留"),
    ("Existing Home Sales", "中古住宅販売件数", "中古住宅販売件数"),
    ("New Home Sales", "新築住宅販売件数", "新築住宅販売件数"),
    ("Building Permits", "住宅着工許可件数", "住宅着工許可件数"),
    ("Housing Starts", "住宅着工件数", "住宅着工件数"),
    ("Philly Fed", "フィラデルフィア連銀景況指数", "フィラデルフィア連銀景況指数"),
    ("Empire State", "NY連銀製造業景気指数", "ニューヨーク連銀製造業景気指数"),
    ("Flash Services PMI", "サービス業PMI速報", "サービス業PMI速報"),
    ("Flash Manufacturing PMI", "製造業PMI速報", "製造業PMI速報"),
]
SKIP = re.compile(r"Election|Bank Holiday|Speaks|Treasury Sec|Bond Auction|Crude Oil Inventories", re.I)


def jp_name(title):
    for key, disp, speech in NAMES:
        if key.lower() in title.lower():
            m = re.search(r"\b([mqy])/\1\b", title)  # m/m, y/y
            suf = {"m": "（前月比）", "q": "（前期比）", "y": "（前年比）"}.get(m.group(1), "") if m else ""
            return disp + suf, speech
    return None, None


def jp_num(x):
    """197K→19.7万、7.15M→715万、-108.0B→-1080億"""
    m = re.fullmatch(r"(-?)([\d.]+)([KMB])", x or "")
    if not m: return x
    sign, v, u = m.group(1), float(m.group(2)), m.group(3)
    v = {"K": v / 10, "M": v * 100, "B": v * 10}[u]
    unit = "億" if u == "B" else "万"
    s = f"{v:,.1f}".rstrip("0").rstrip(".")
    return f"{sign}{s}{unit}"


def _load():
    out = []
    for u in URLS:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "market-shorts/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                out += json.loads(r.read().decode())
        except Exception as e:
            print("経済カレンダー取得失敗:", u, str(e)[:120])
    return out


def when_label(t, now):
    """日本時間の見せ方: 今夜22:30 / 明日0:00 / 11/7(金)22:30"""
    d = (t.date() - now.date()).days
    hm = f"{t.hour}:{t.minute:02d}"
    if d == 0:
        return ("今夜" if t.hour >= 17 else "本日") + hm
    if d == 1 and t.hour < 6:
        return "明日" + hm
    return f"{t.month}/{t.day}({WD[t.weekday()]}){hm}"


def upcoming(now=None, n=3):
    """投稿時点から先の米国の重要指標を最大 n 件。"""
    now = now or dt.datetime.now(JST)
    seen, items = set(), []
    for e in _load():
        if e.get("country") != "USD" or e.get("impact") not in ("High", "Medium"):
            continue
        if SKIP.search(e.get("title", "")):
            continue
        disp, speech = jp_name(e["title"])
        if not disp:
            continue
        t = dt.datetime.fromisoformat(e["date"]).astimezone(JST)
        if t <= now or t > now + dt.timedelta(days=4):
            continue
        k = (disp, t)
        if k in seen:
            continue
        seen.add(k)
        items.append({"t": t, "when": when_label(t, now), "name": disp, "speech": speech,
                      "forecast": jp_num((e.get("forecast") or "").strip()), "previous": jp_num((e.get("previous") or "").strip()),
                      "high": e.get("impact") == "High"})
    # 24時間以内（今夜〜明朝）を優先。足りなければその先の重要指標で埋める
    items.sort(key=lambda i: i["t"])
    soon = [i for i in items if i["t"] <= now + dt.timedelta(hours=24)]
    later = [i for i in items if i not in soon]
    if len(soon) > n:
        soon = sorted(soon, key=lambda i: (not i["high"], i["t"]))[:n]
    pool = soon + sorted(later, key=lambda i: (not i["high"], i["t"]))[:n - len(soon)]
    pool.sort(key=lambda i: i["t"])
    for i in pool:
        i["t"] = i["t"].isoformat()
    return pool


if __name__ == "__main__":
    for i in upcoming():
        print(i)

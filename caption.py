"""YouTube / Instagram 共通の投稿文。1行目で結論、次に「次に見る数字」、保存とコメントの呼びかけ。"""


def ev_line(e):
    extra = []
    if e.get("forecast"): extra.append(f"予想{e['forecast']}")
    if e.get("previous"): extra.append(f"前回{e['previous']}")
    return f"・{e['when']} {e['name']}" + (f"（{'、'.join(extra)}）" if extra else "")


def hook_line(d):
    h = d.get("hook") or {}
    if h:
        return f"【{d['date_speech']} NY】{h['big']}｜{h['small']}"
    dow = d["indices"][0]
    return f"【{d['date_speech']} NY】ダウ{int(abs(dow['chg'])):,}ドル{'高' if dow['chg'] > 0 else '安'}・{d['headline']['status']}"


def body(d, platform):
    L = [hook_line(d), ""]
    ev = d.get("events") or []
    if ev:
        tonight = ev[0]["when"].startswith(("今夜", "本日", "明日"))
        L.append("■今夜見る数字（日本時間）" if tonight else "■次に見る数字（日本時間）")
        L += [ev_line(e) for e in ev[:3]]
        L += ["", "🔖保存して、発表後の答え合わせに"]
    else:
        L += [f"■次の焦点：{' '.join(d['next'])}", ""]
    p = d.get("poll")
    if p:
        L += ["", f"💬{p['q']}", "  ".join(p["opts"]), "コメントでどうぞ"]
    L += ["", "■昨夜の終値"]
    for grp in ("indices", "rates_fx", "commodities"):
        for it in d[grp]:
            cl = it.get("chg_label") or f"{it['chg']:+,.2f} ({it['pct']:+.2f}%)"
            L.append(f"・{it['name']} {it['value']:,.{it['dec']}f}（{cl}）")
    L += ["", "※情報提供のみを目的としたもので、投資助言ではありません。予定・予想は変わることがあります。"]
    if platform == "youtube":
        L += ["※データ: Yahoo Finance、Forex Factory ほか", "", "#米国株 #NYダウ #ナスダック #ドル円 #経済指標 #市況 #shorts"]
    else:
        L += ["", "#米国株 #米国株投資 #経済指標 #NYダウ #ナスダック #ドル円 #新NISA #投資初心者 #資産運用"]
    return "\n".join(L)


def yt_title(d):
    return (hook_line(d) + " #shorts")[:100]

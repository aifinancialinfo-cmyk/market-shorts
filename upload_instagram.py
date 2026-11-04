#!/usr/bin/env python3
"""完成した動画をInstagramリールとして投稿する（Instagram API / Instagramログイン方式）。
必要な環境変数: IG_ACCESS_TOKEN, IG_USER_ID, VIDEO_URL
※IG_ACCESS_TOKEN は発行から約60日で期限切れ。期限前にMeta開発者画面で再発行して登録し直す
使い方: python3 upload_instagram.py data.json video.mp4
"""
import json, os, sys, time, urllib.parse, urllib.request
import caption as captions

API = "https://graph.instagram.com/v25.0"


def call(method, url, data=None, headers=None, body=None):
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {url.split('?')[0]} -> {e.code}: {e.read().decode()[:500]}")


def caption(d):
    return captions.body(d, "instagram")[:2100]


def main(dj, video):
    tok, uid = os.environ["IG_ACCESS_TOKEN"].strip(), os.environ["IG_USER_ID"].strip()

    d = json.load(open(dj))
    vurl = os.environ["VIDEO_URL"].strip()

    # 1) 公開URLの動画を指定してリール用コンテナを作成（Instagramが動画を取りに来る）
    c = call("POST", f"{API}/{uid}/media", {
        "media_type": "REELS", "video_url": vurl, "caption": caption(d),
        "share_to_feed": "true", "access_token": tok})
    cid = c["id"]
    print("コンテナ作成:", cid)

    # 2) Instagram側の処理完了を待つ（最大約10分）
    for _ in range(60):
        s = call("GET", f"{API}/{cid}?" + urllib.parse.urlencode({"fields": "status_code,status", "access_token": tok}))
        st = s.get("status_code")
        if st == "FINISHED":
            break
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram側の処理でエラー: {s}")
        time.sleep(10)
    else:
        raise RuntimeError("Instagram側の処理が10分以内に終わりませんでした")

    # 3) 公開
    p = call("POST", f"{API}/{uid}/media_publish", {"creation_id": cid, "access_token": tok})
    m = call("GET", f"{API}/{p['id']}?" + urllib.parse.urlencode({"fields": "permalink", "access_token": tok}))
    print("Instagram投稿完了:", m.get("permalink", p["id"]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

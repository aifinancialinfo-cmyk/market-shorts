#!/usr/bin/env python3
"""完成した動画をYouTubeに投稿する。
必要な環境変数: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
任意: YT_PRIVACY (public / unlisted / private, 既定 public)
使い方: python3 upload_youtube.py data.json video.mp4
"""
import json, os, sys
import caption
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def main(dj, video):
    d = json.load(open(dj))
    title = caption.yt_title(d)
    lines = [caption.body(d, "youtube")]
    creds = Credentials(None, refresh_token=os.environ["YT_REFRESH_TOKEN"],
                        client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
                        token_uri="https://oauth2.googleapis.com/token",
                        scopes=["https://www.googleapis.com/auth/youtube.upload"])
    yt = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {"title": title[:100], "description": "\n".join(lines)[:4900],
                    "tags": ["米国株", "市況", "NYダウ", "ナスダック", "S&P500", "ドル円", "金", "ビットコイン", "AI"],
                    "categoryId": "25", "defaultLanguage": "ja", "defaultAudioLanguage": "ja"},
        "status": {"privacyStatus": os.environ.get("YT_PRIVACY", "public"), "selfDeclaredMadeForKids": False,
                   "containsSyntheticMedia": True},
    }
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(video, mimetype="video/mp4", resumable=True))
    res = None
    while res is None:
        _, res = req.next_chunk()
    print("投稿完了: https://youtube.com/shorts/" + res["id"])

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

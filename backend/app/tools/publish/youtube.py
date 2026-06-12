"""Live publisher: YouTube Data API v3 resumable upload with installed-app OAuth.

First live run opens a browser consent flow once; the token is cached after.
"""
from pathlib import Path

from ...core.config import BACKEND_DIR, settings
from ...domain.models import PublishResult

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    token_path = BACKEND_DIR / settings.youtube_token_file
    secret_path = BACKEND_DIR / settings.youtube_client_secret_file

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), SCOPES)
        creds = flow.run_local_server(port=0)
    token_path.write_text(creds.to_json())
    return creds


def youtube_upload(video_path: Path, title: str, description: str, tags: list[str]) -> PublishResult:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    creds = _get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "28",  # Science & Technology
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = response["id"]
    return PublishResult(
        youtube_id=video_id,
        url=f"https://youtube.com/shorts/{video_id}",
        dry_run=False,
        metadata={"title": title, "tags": tags},
    )

import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

def get_youtube_client():
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError(
            "Set YOUTUBE_API_KEY in .env or your environment. "
            "Get a key at https://console.cloud.google.com/apis/credentials"
        )
    return build("youtube", "v3", developerKey=api_key)


def fetch_all_playlist_videos(youtube, playlist_id: str, since: datetime) -> list[dict]:
    
    # fetch all videos from a playlist since a certain date

    videos = []
    page_token = None

    while True:
        req = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=page_token,
        )
        resp = req.execute()

        items = resp.get("items", [])
        all_before_cutoff = True
        for item in items:
            snippet = item["snippet"]
            published_str = snippet.get("publishedAt")
            if not published_str:
                continue
            published = datetime.fromisoformat(
                published_str.replace("Z", "+00:00")
            )
            if published < since:
                continue
            all_before_cutoff = False
            videos.append({
                "video_id": snippet["resourceId"]["videoId"],
                "title": snippet["title"],
                "published_at": published,
            })

        if items and all_before_cutoff:
            break
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return videos


def fetch_video_statistics(youtube, video_ids: list[str]) -> dict[str, int]:
    # fetch view counts for a batch of video IDs
    if not video_ids:
        return {}
    req = youtube.videos().list(
        part="statistics",
        id=",".join(video_ids),
        maxResults=50,
    )
    resp = req.execute()
    out = {}
    for item in resp.get("items", []):
        vid = item["id"]
        out[vid] = int(item.get("statistics", {}).get("viewCount", 0))
    return out


def get_channel_videos(years_back: float = 2) -> list[dict]:
    # get all steve dangle videos from the last x years
    # will return all videos -> need to filter out non-lfr videos
    youtube = get_youtube_client()
    since = datetime.now(timezone.utc) - timedelta(days=years_back * 365)

    resp = youtube.channels().list(
        part="contentDetails",
        forHandle="SteveDangle",
    ).execute()
    items = resp.get("items", [])
    if not items:
        raise ValueError("No channel found for handle: SteveDangle")
    playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    videos = fetch_all_playlist_videos(youtube, playlist_id, since)

    all_views = {}
    for i in range(0, len(videos), 50):
        batch_ids = [v["video_id"] for v in videos[i : i + 50]]
        all_views.update(fetch_video_statistics(youtube, batch_ids))

    for v in videos:
        v["views"] = all_views.get(v["video_id"], 0)

    return sorted(videos, key=lambda x: x["published_at"], reverse=True)


def main():
    videos = get_channel_videos(years_back=6)

    print(len(videos))
    # for v in videos:
        # date_str = v["published_at"].strftime("%Y-%m-%d")
        # print(f"{date_str:<12} {v['views']:>12,}  {v['title'][:50]}")

    # then write CSV
    csv_path = os.path.join(os.path.dirname(__file__), "steve_dangle_videos.csv")
    with open(csv_path, "w") as f:
        f.write("date,views,title,video_id\n")
        for v in videos:
            title_escaped = v["title"].replace('"', '""')

            # skip non-lfr videos
            if title_escaped[0:3] != "LFR":
                continue
            f.write(f'{v["published_at"].strftime("%Y-%m-%d")},{v["views"]},"{title_escaped}",{v["video_id"]}\n')


if __name__ == "__main__":
    main()

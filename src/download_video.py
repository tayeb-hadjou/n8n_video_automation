import sys, json, yt_dlp
from config import YOUTUBE_URL, VIDEO_PATH, OUTPUT_DIR

def download_video(url):
    ydl_opts = {
        "format": "bv*[ext=mp4][height<=1080]+ba[ext=m4a]/b[ext=mp4]",
        "merge_output_format": "mp4",
        "outtmpl": VIDEO_PATH,
        "noplaylist": True,
        "ignoreerrors": True,
        "continuedl": True,
        "quiet": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return {"success": True, "path": VIDEO_PATH}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    sys.argv[1]
    result = download_video(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result["success"] else 1)

import os
import json
import subprocess
from typing import Tuple
from config import OUTPUT_DIR, VIDEO_PATH, REFINED_PATH, SRC_DIR


def run(cmd):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{proc.stderr}")
    return proc.stdout


def _ffprobe_dims(path: str) -> Tuple[int, int, float]:
    """Retourne (width, height, fps) via ffprobe."""
    out = run([
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,avg_frame_rate",
        "-of", "json",
        path,
    ])
    info = json.loads(out)
    stream = info.get("streams", [{}])[0]
    w = int(stream.get("width", 0))
    h = int(stream.get("height", 0))
    fr = str(stream.get("avg_frame_rate", "0/1"))
    fps = float(fr.split("/")[0]) / float(fr.split("/")[1]) if "/" in fr else float(fr or 0.0)
    return w, h, fps


def process_clip(tmp_clip, output_clip, zoom_factor=1.0, smart=True):
    """
    Met en forme une vidéo 9:16 avec avant-plan net + arrière-plan flou.

    Args:
        tmp_clip (str): chemin du clip d'entrée
        output_clip (str): chemin du clip de sortie
        zoom_factor (float): facteur de zoom (1.0 = normal, >1 = zoom)
        smart (bool): (non utilisé ici mais gardé pour compat)
    """
    # Dimensions source
    in_w, in_h, _ = _ffprobe_dims(tmp_clip)
    crop_w, crop_h = 1080, 1920

    # Filtre complexe FFmpeg :
    # - v0 = vidéo nette redimensionnée pour tenir dans 1080x1920
    # - v1 = vidéo floutée redimensionnée pour remplir 1080x1920
    # - overlay = v0 posé sur v1 (centre)
    vf_filter = (
        f"[0:v]scale={crop_w}:{crop_h}:force_original_aspect_ratio=decrease[v0];"
        f"[0:v]scale={crop_w}:{crop_h}:force_original_aspect_ratio=increase,"
        f"crop={crop_w}:{crop_h},boxblur=20:1[v1];"
        f"[v1][v0]overlay=(W-w)/2:(H-h)/2"
    )

    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", tmp_clip,
        "-filter_complex", vf_filter,
        "-r", "30",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",  # qualité haute
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_clip
    ])



def extract_clips():
    """
    Extrait des clips vidéo avec fond flouté.
    """
    clips_path = []
    with open(REFINED_PATH, "r", encoding="utf-8") as f:
        segments = json.load(f)

    for i, seg in enumerate(segments):
        start = max(0.0, float(seg["start"]))
        end = max(start, float(seg["end"]))
        duration = max(0.01, end - start)

        tmp_clip = os.path.join(SRC_DIR, OUTPUT_DIR, f"_tmp_origin_clip_{i}.mp4")
        output_clip = os.path.join(SRC_DIR, OUTPUT_DIR, f"clip_origine_{i}.mp4")

        # 1) Découpage rapide (stream copy)
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{start:.3f}",
            "-t", f"{duration:.3f}",
            "-i", VIDEO_PATH,
            "-c", "copy",
            tmp_clip
        ])
        print(f"🎬 Clip {i}: {tmp_clip} ({seg['start']:.2f}s → {seg['end']:.2f}s, score={seg.get('score')})")

        # 2) Mise en forme avec fond flouté
        process_clip(tmp_clip, output_clip)
        clips_path.append(output_clip)

        try:
            os.remove(tmp_clip)
        except Exception:
            pass

    # Sauvegarde des chemins de clips
    clips_json = {"clips": clips_path}
    clips_file = os.path.join(SRC_DIR, OUTPUT_DIR, "clips.json")
    with open(clips_file, "w", encoding="utf-8") as f:
        json.dump(clips_json, f, ensure_ascii=False, indent=2)

    print(f"✅ Clips sauvegardés dans {clips_file}")
    return clips_json


if __name__ == "__main__":
    result = extract_clips()
    print("Extraction terminée", result)

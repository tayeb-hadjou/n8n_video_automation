import os
import json
import subprocess
from config import OUTPUT_DIR, VIDEO_PATH, REFINED_PATH, SRC_DIR


def run(cmd):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{proc.stderr}")
    return proc.stdout


def process_clip(tmp_clip, output_clip, zoom_factor=1.0):
    """
    Met en forme une vidéo en 9:16 plein écran avec crop + zoom.
    
    Args:
        tmp_clip (str): chemin du clip d'entrée
        output_clip (str): chemin du clip de sortie
        zoom_factor (float): facteur de zoom (1.0 = normal, >1 = zoom)
    """
    # Filtre vidéo FFmpeg : scale + crop centré avec zoom
    vf_filter = (
        f"scale=-2:{int(1920*zoom_factor)},"
        f"crop=1080:1920:(in_w-1080)/2:(in_h-1920)/2"
    )

    run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", tmp_clip,
        "-vf", vf_filter,
        "-r", "30",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",  # 👈 qualité haute
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_clip
    ])


def extract_clips(zoom_factor=1.2):
    """
    Extrait des clips vidéo à partir d'une liste de segments.

    Args:
        zoom_factor (float): facteur de zoom appliqué lors du recadrage
    """
    clips_path = []
    with open(REFINED_PATH, "r", encoding="utf-8") as f:
        segments = json.load(f)

    for i, seg in enumerate(segments):
        start = max(0.0, float(seg["start"]))
        end = max(start, float(seg["end"]))
        duration = max(0.01, end - start)

        tmp_clip = os.path.join(SRC_DIR, OUTPUT_DIR, f"_tmp_clip_v1_{i}.mp4")
        output_clip = os.path.join(SRC_DIR, OUTPUT_DIR, f"clip_v1_{i}.mp4")

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

        # 2) Mise en forme finale avec zoom
        process_clip(tmp_clip, output_clip, zoom_factor=zoom_factor)

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
    result = extract_clips(zoom_factor=1.2)  # 👈 Ajuste ici (1.0 = normal, 1.5 = zoom fort)
    print("Extraction terminée", result)

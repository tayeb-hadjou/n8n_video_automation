import os
import json
import math
import subprocess
from typing import Optional, Tuple, List
from config import OUTPUT_DIR, VIDEO_PATH, REFINED_PATH, SRC_DIR

# OpenCV est optionnel: on bascule en recadrage centré si non installé
try:
    import cv2  # type: ignore
    _HAS_CV2 = True
except Exception:
    cv2 = None  # type: ignore
    _HAS_CV2 = False


def run(cmd):
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{proc.stderr}")
    return proc.stdout


def _ffprobe_dims(path: str) -> Tuple[int, int, float]:
    """Retourne (width, height, fps) du flux vidéo via ffprobe."""
    try:
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
        if "/" in fr:
            num, den = fr.split("/", 1)
            fps = float(num) / float(den) if float(den) != 0 else 0.0
        else:
            fps = float(fr or 0.0)
        return w, h, fps
    except Exception:
        return 0, 0, 0.0


def _detect_face_center(path: str, samples: int = 12) -> Optional[Tuple[float, float]]:
    """Détecte un centre de visage moyen (x,y) en pixels du flux source.
    Retourne None si aucune détection fiable.
    """
    if not _HAS_CV2:
        return None
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return None

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    if total <= 0 or w <= 0 or h <= 0:
        cap.release()
        return None

    # Cascade Haar incluse avec OpenCV
    try:
        cascade_path = getattr(cv2.data, "haarcascades") + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        if face_cascade.empty():
            cap.release()
            return None
    except Exception:
        cap.release()
        return None

    # Prélever des frames réparties sur la durée
    idxs: List[int] = []
    step = max(total // (samples + 1), 1)
    pos = step
    while pos < total and len(idxs) < samples:
        idxs.append(pos)
        pos += step

    centers: List[Tuple[float, float]] = []
    for i in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        if len(faces) == 0:
            continue
        # Prendre le plus grand visage
        x, y, fw, fh = max(faces, key=lambda b: b[2] * b[3])
        cx = float(x + fw / 2.0)
        cy = float(y + fh / 2.0)
        centers.append((cx, cy))

    cap.release()
    if not centers:
        return None
    # Médiane pour robustesse
    xs = sorted([c[0] for c in centers])
    ys = sorted([c[1] for c in centers])
    mx = xs[len(xs) // 2]
    my = ys[len(ys) // 2]
    return (mx, my)


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def process_clip(tmp_clip, output_clip, zoom_factor=1.0, smart=True):
    """
    Met en forme une vidéo en 9:16 plein écran avec crop + zoom.
    
    Args:
        tmp_clip (str): chemin du clip d'entrée
        output_clip (str): chemin du clip de sortie
        zoom_factor (float): facteur de zoom (1.0 = normal, >1 = zoom)
        smart (bool): active le zoom/cadrage intelligent (détection visage)
    """
    # Dimensions source
    in_w, in_h, _ = _ffprobe_dims(tmp_clip)
    scale_h = max(1920, int(1920 * float(zoom_factor)))
    # Après scale, la hauteur devient scale_h, la largeur suit le ratio
    scaled_w = int(round(in_w * (scale_h / max(in_h, 1)))) if in_w and in_h else 1080

    crop_w, crop_h = 1080, 1920

    # Par défaut: crop centré
    crop_x = max(0, (scaled_w - crop_w) // 2)
    crop_y = max(0, (scale_h - crop_h) // 2)

    if smart:
        center = _detect_face_center(tmp_clip)
        if center is not None and in_h > 0:
            cx, cy = center
            # Coords après scale
            scale_ratio = scale_h / float(in_h)
            cx_s = cx * scale_ratio
            cy_s = cy * scale_ratio
            crop_x = int(_clamp(cx_s - crop_w / 2.0, 0, max(scaled_w - crop_w, 0)))
            crop_y = int(_clamp(cy_s - crop_h / 2.0, 0, max(scale_h - crop_h, 0)))
            print(f"🔎 Smart crop autour du visage: x={crop_x}, y={crop_y}")
        else:
            if not _HAS_CV2:
                print("ℹ️ OpenCV non installé: recadrage centré.")
            else:
                print("ℹ️ Aucun visage détecté: recadrage centré.")

    # Filtre vidéo FFmpeg : scale + crop positionné
    vf_filter = (
        f"scale=-2:{scale_h},"
        f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}"
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



def extract_clips(zoom_factor=1.2, smart_zoom: bool = True):
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

        tmp_clip = os.path.join(SRC_DIR, OUTPUT_DIR, f"_tmp_clip_{i}.mp4")
        output_clip = os.path.join(SRC_DIR, OUTPUT_DIR, f"clip_{i}.mp4")

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

    # 2) Mise en forme finale avec zoom (intelligent si activé)
        process_clip(tmp_clip, output_clip, zoom_factor=zoom_factor, smart=smart_zoom)
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
    import argparse
    parser = argparse.ArgumentParser(description="Extraction de clips 9:16 avec zoom intelligent")
    parser.add_argument("--zoom", type=float, default=1.0, help="Facteur de zoom (1.0 = normal, >1 = zoom)")
    parser.add_argument("--no-smart", action="store_true", help="Désactive le zoom intelligent (détection visage)")
    args = parser.parse_args()
    result = extract_clips(zoom_factor=args.zoom, smart_zoom=not args.no_smart)
    print("Extraction terminée", result)

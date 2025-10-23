import json
import os
from config import OUTPUT_DIR, WINDOW_SIZE, STEP_SIZE, TRANSCRIPT_PATH,BLOCKS_PATH

def sliding_window_segments(segments, window_size=WINDOW_SIZE, step_size=STEP_SIZE):
    """
    Crée des fenêtres glissantes à partir de segments de transcription.

    Args:
        segments (list): liste de dicts {start, end, text}
        window_size (float): taille de la fenêtre en secondes
        step_size (float): pas du déplacement en secondes

    Returns:
        list: fenêtres glissantes [{start, end, text}]
    """
    try:
        print("🔍 Création des fenêtres glissantes...")
        grouped = []
        if not segments:
            return {"success": False, "error": "Aucun segment fourni"}

        video_end = segments[-1]["end"]
        t = 0.0
        while t < video_end:
            t2 = min(t + window_size, video_end)
            text = " ".join(
                s["text"] for s in segments if s["end"] >= t and s["start"] <= t2
            ).strip()
            if text:
                grouped.append({"start": t, "end": t2, "text": text})
            t += step_size

        # Sauvegarde dans un fichier JSON
        out_path = os.path.join(BLOCKS_PATH)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(grouped, f, ensure_ascii=False, indent=2)

        print(f"✅ Fenêtres enregistrées: {out_path}")
        return {"success": True, "count": len(grouped), "path": out_path}

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Exemple de test manuel
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    segments = data["segments"]
    result = sliding_window_segments(segments)
    print(json.dumps(result, ensure_ascii=False))


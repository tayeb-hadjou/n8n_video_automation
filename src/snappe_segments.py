import os
import json
from config import OUTPUT_DIR, SILENCE_SNAP_TOL,MERGE_THRESHOLD,SILENCE_MIN_GAP, TRANSCRIPT_PATH,SCORED_PATH, SNAPPED_PATH

def snap_segments(segments):
    """
    Ajuste les segments fusionnés aux silences détectés,
    ajoute un buffer, et reconstruit le texte.
    Sauvegarde le résultat dans snapped_segments.json.

    Args:
        segments (list): liste originale de segments [{start, end, text}]
        merged (list): segments fusionnés avec un score [{start, end, score}]

    Returns:
        list: segments ajustés [{start, end, text, score}]
    """
    try :
        print("🔇 Ajustement aux silences...")
        merged = merge_overlapping_segments(segments)
        snapped = []
        video_end = segments[-1]["end"]
        silences = detect_silences()

        for seg in merged:
            # garder seulement les segments pertinents
            if seg.get("score", 0) < 8:
                continue

            # ajoute 20 secondes à la fin
            seg["end"] += 20

            # ajuste sur silence
            newStart, newEnd = snap_to_silence(seg, silences, tol=SILENCE_SNAP_TOL)

            rs = clamp(newStart, 0.0, video_end)
            re = clamp(newEnd, 0.0, video_end)
            if re <= rs:
                continue

            # reconstitue le texte
            texts = [
                s["text"].strip()
                for s in segments
                if s.get("text") and s["end"] > rs and s["start"] < re
            ]
            combined_text = " ".join(texts).strip()

            snapped.append({
                "start": rs,
                "end": re,
                "text": combined_text,
                "score": seg.get("score", 0),
            })

        # sauvegarde
        with open(SNAPPED_PATH, "w", encoding="utf-8") as f:
            json.dump(snapped, f, ensure_ascii=False, indent=4)

        return {"success": True, "count": len(snapped)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def merge_overlapping_segments(segments, threshold=MERGE_THRESHOLD):
    print("🔗 Fusion des segments pertinents...")
    
    kept = [s for s in segments if s.get("score", 0) >= threshold]
    if not kept: 
        return []
    kept.sort(key=lambda s: (s["start"], s["end"]))
    merged = [kept[0].copy()]
    for seg in kept[1:]:
        last = merged[-1]
        if seg["start"] <= last["end"]:
            last["end"] = max(last["end"], seg["end"])
            last["text"] = (last["text"] + " " + seg["text"]).strip()
            last["score"] = max(last["score"], seg["score"])
        else:
            merged.append(seg.copy())
    return merged

def detect_silences(min_gap=SILENCE_MIN_GAP):
    #recup les segments
    with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    silences = []
    for i in range(1, len(data["segments"])):
        gap = data["segments"][i]["start"] - data["segments"][i-1]["end"]
        if gap >= min_gap:
            silences.append({"start": data["segments"][i-1]["end"], "end": data["segments"][i]["start"]})
    return silences

def snap_to_silence(segment, silences, tol=SILENCE_SNAP_TOL):
    #search for the first silence before start
    first = max((s for s in silences if s["end"] <= segment["start"] - tol), key=lambda s: s["end"], default=None)

    #search for the last silence before end
    last = min((s for s in silences if s["start"] >= segment["end"] + tol), key=lambda s: s["start"], default=None)
    if last and first:
        return first["start"],last["end"]
    #add a parts to the segment
    
    return segment["start"], segment["end"]

def clamp(x, a, b):
    return max(a, min(b, x))


if __name__ == "__main__":
    with open(SCORED_PATH, "r", encoding="utf-8") as f:
        segments = json.load(f)
    result = snap_segments(segments)
    print(result)

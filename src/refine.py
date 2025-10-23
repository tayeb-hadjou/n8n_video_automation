import json
import time
from config import MODEL_NAME, MARGIN, MISTRAL_KEY, OUTPUT_DIR, TRANSCRIPT_PATH, MARGIN,REFINED_PATH
from mistralai import Mistral

def refine_all_segments(client):
    """
    Raffine tous les segments en appelant un LLM pour
    détecter le véritable début et la véritable fin de chaque propos.
    """
    try:
        refined = []
        with open(OUTPUT_DIR + "/snapped.json", "r", encoding="utf-8") as f:
            snapped = json.load(f)

        with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
            segments = json.load(f)
            segments = segments["segments"]

        for seg in snapped:
            refined_seg = refine_timecodes_llm(client, seg, segments, margin=MARGIN)
            refined.append(refined_seg)

        #enregistrement des segments raffinés
        with open(REFINED_PATH, "w", encoding="utf-8") as f:
            json.dump(refined, f, ensure_ascii=False, indent=4)
        return {"success": True, "count": len(refined)}

    except Exception as e:
        return {"success": False, "error": str(e)}


def refine_timecodes_llm(client, candidate, full_segments, margin=MARGIN):
    """
    Raffine les timecodes d'un segment en appelant un LLM pour
    détecter le véritable début et la véritable fin d'un propos.

    Args:
        client: client LLM (ex: OpenAI, Mistral, etc.)
        candidate (dict): segment candidat {start, end, text, score}
        full_segments (list): transcription complète [{start, end, text}]
        margin (float): marge de temps ajoutée autour du candidat

    Returns:
        dict: segment raffiné {start, end, text, score}
    """
    print("🔧 Raffinage LLM")

    try:

        video_end = full_segments[-1]["end"]
        w_start = clamp(candidate["start"] - margin, 0.0, video_end)
        w_end   = clamp(candidate["end"] + margin, 0.0, video_end)

    except Exception as e:
        print(e)

    # isole les segments autour du candidat
    window_segments = [
        s for s in full_segments if s["end"] >= w_start and s["start"] <= w_end
    ]
    window_payload = json.dumps(window_segments, ensure_ascii=False)
    
    # prompt LLM
    prompt = f"""Tu es un assistant spécialisé dans la détection de débuts et fins de propos dans une transcription de vidéo.

Voici des segments consécutifs de transcription avec timecodes (en secondes) :
\"\"\"{window_payload}\"\"\"

Tâche :
- Ces segments forment une seule idée continue (un même propos).
- Détermine avec précision :
  - "start" = timecode du VÉRITABLE début du propos (le moment où une phrase ou une idée démarre clairement).
  - "end" = timecode de la FIN du propos (la dernière phrase qui conclut cette idée).
- Ne choisis pas un début ou une fin coupés au milieu d’une phrase.
- Ne propose pas d’introduction ou de sortie artificielle : colle uniquement au propos donné.
- IMPORTANT : le "start" et le "end" doivent être des timecodes PRÉCIS issus de la liste fournie (ne pas inventer d’autres valeurs).

Réponds UNIQUEMENT au format JSON strict :
{{
"start": <float>,
"end": <float>
}}"""

    # appel au modèle
    resp = client.chat.complete(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )

    # parsing du JSON
    raw = resp.choices[0].message.content.strip()
    data = json.loads(raw)

    rs, re = float(data["start"]), float(data["end"])

    # clamp & fallback
    rs, re = clamp(rs, 0.0, video_end), clamp(re, 0.0, video_end)
    if re <= rs:
        rs, re = w_start, w_end

    # anti-rate limit
    time.sleep(2)

    return {
        "start": rs,
        "end": re,
        "text": candidate.get("text", ""),
        "score": candidate.get("score", 0),
    }

def clamp(x, a, b):
    return max(a, min(b, x))


if __name__ == "__main__":
    client = Mistral(api_key=MISTRAL_KEY)
    result = refine_all_segments(client)
    print(result)

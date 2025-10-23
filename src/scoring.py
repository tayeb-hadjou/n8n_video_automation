import sys, json, os
from config import BLOCKS_PATH, SCORED_PATH, MISTRAL_KEY, MODEL_NAME, N_TOP_SEGMENTS 
from mistralai import Mistral
import time

def build_mistral_client():
    if not MISTRAL_KEY:
        raise RuntimeError("Définis MISTRAL_API_KEY dans l’environnement.")
    return Mistral(api_key=MISTRAL_KEY)

def score_segments():
    try:
        print("🧠 Évaluation des segments...")
        with open(BLOCKS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        segments = data
        client = build_mistral_client()
        out = []
        for s in segments:
            seg = score_one_segment(client, s)
            out.append(seg)
        #enrigster dans un fichier
        with open(SCORED_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        return {"success": True, "count": len(out)}

    except Exception as e:
        return {"success": False, "error": str(e)}

def score_one_segment(client, seg):
    try:
        prompt = f"""Tu es un expert en montage de vidéos courtes (TikTok/Shorts) et tu gères un compte sur le cinema.
        voici un passage d'une vidéo YouTube :
        Passage:
        \"{seg['text']}\"
                        Évalue ce passage pour son potentiel :
                        - Idée originale/surprenante
                        - Explication claire et digeste
                        - Émotion (inspiration)
                        - Pertinence grand public
                        - Potentiel de rétention
                        - moment “wow”

                        donne une note gobale de 1 à 10 et Réponds UNIQUEMENT par un nombre entiers rien d'autre sachant que un 8 signifie qui vas etre publie sur TikTok
                        voici un example de réponse :
                        8
                        Réponds uniquement avec le nombre absolument rien d'autre pas texte.
        """
        resp = client.chat.complete(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.choices[0].message.content.strip()
        score = int("".join(filter(str.isdigit, raw))) if raw else 5
        time.sleep(0.2)  # pour éviter les rate limits
    except Exception as e:
        print("⚠️ Scoring err:", e)
        score = -1
        time.sleep(5)  # pour éviter les rate limits
    seg["score"] = score
    return seg

if __name__ == "__main__":
    result = score_segments()
    print(json.dumps(result, ensure_ascii=False))

import sys, json, whisper, torch
from config import VIDEO_PATH, TRANSCRIPT_PATH

def transcribe():
    try:
        model = whisper.load_model("tiny")
        try:
            fp16 = torch.cuda.is_available()
        except Exception:
            fp16 = False
        result = model.transcribe(VIDEO_PATH, verbose=True, fp16=fp16)

        with open(TRANSCRIPT_PATH, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        return {"success": True, "path": TRANSCRIPT_PATH}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = transcribe()
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result["success"] else 1)

import os
SRC_DIR = "/home/massi/ai/python_ai/src"
OUTPUT_DIR = "/home/massi/ai/python_ai/src/output"
VIDEO_PATH = os.path.join(SRC_DIR, OUTPUT_DIR, "video.mkv")
TRANSCRIPT_PATH = os.path.join(SRC_DIR, OUTPUT_DIR, "video.json")
BLOCKS_PATH = os.path.join(SRC_DIR, OUTPUT_DIR, "blocks.json")
SCORED_PATH = os.path.join(SRC_DIR, OUTPUT_DIR, "scored.json")
CLIPS_JSON = os.path.join(SRC_DIR, OUTPUT_DIR, "clips.json")
SNAPPED_PATH = os.path.join(SRC_DIR, OUTPUT_DIR, "snapped.json")
REFINED_PATH = os.path.join(SRC_DIR, OUTPUT_DIR, "refined.json")


YOUTUBE_URL = "https://www.youtube.com/watch?v=X7aF3nZOS98&list=RDX2DTROC4JCI&index=32"

MAX_BLOCK_DURATION = 50.0
N_TOP_SEGMENTS = 3
WINDOW_SIZE = 20.0
WINDOW_SIZE = 50.0           # s
STEP_SIZE = 10.0             # s
SCORE_PARALLEL_WORKERS = 5   # threads LLM
MERGE_THRESHOLD = 8          # score mini à garder/fusionner
TOP_K = 3
MARGIN = 10.0                # s, marge auto avant/après un passage pertinent
SILENCE_MIN_GAP = 0.2        # s, silence “long” entre deux phrases
SILENCE_SNAP_TOL = 1.0 


# API LLM
MISTRAL_KEY = "sVyGpa0WRQU3vsPF5LQ9557MdQlDLuQe"
MODEL_NAME = "mistral-tiny-latest"
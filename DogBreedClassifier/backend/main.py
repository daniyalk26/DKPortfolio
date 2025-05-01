import os
import re, io, time, unicodedata
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np, requests, tensorflow as tf
from fastapi import FastAPI, File, HTTPException, UploadFile, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image




# ─────────── Config ───────────

MODEL_PATH, CLASS_FILE = "./backend/final_model.keras", "./backend/class_names.txt"
IMG_SIZE, TOP_K = (300, 300), 3
DOG_API_URL, NINJA_API_URL = "https://api.thedogapi.com/v1", "https://api.api-ninjas.com/v1/dogs"
DOG_API_KEY = os.getenv('DOG_API_KEY')
NINJA_API_KEY = os.getenv('NINJA_API_KEY')

# ───────── Emotion Model Config ─────────
EMOTION_MODEL_PATH   = "./backend/final_b3_model.keras"
EMOTION_IMG_SIZE     = (300, 300)
EMOTION_TOP_K        = 3

# Just embed your four emotion labels here:
EMOTION_CLASS_NAMES  = ['angry', 'happy', 'relaxed', 'sad']

# ───────── Load emotion model & classes ─────────
emotion_model   = tf.keras.models.load_model(EMOTION_MODEL_PATH, compile=False)
emotion_classes = EMOTION_CLASS_NAMES

# ───────── Load model & classes ─────────
model   = tf.keras.models.load_model(MODEL_PATH, compile=False)
classes = Path(CLASS_FILE).read_text().splitlines()

# ───────── Canonicalisation helpers ─────────
_rx_caps   = re.compile(r"([a-z])([A-Z])")
_rx_paren  = re.compile(r"\s*\(.*?\)\s*$")              # strip “( … )” suffixes

def _clean(label: str) -> str:                          # remove % etc. first
    return _rx_paren.sub("", label).strip()

def canon(raw: str) -> str:                             # then canonicalise
    s = unicodedata.normalize("NFKD", raw)
    s = _rx_caps.sub(r"\1 \2", s)
    s = re.sub(r"[’'`]", "", s).lower()
    s = s.replace("_", " ").replace("-", " ")
    s = re.sub(r"[()]", " ", s)
    s = " ".join(s.split())
    if s.endswith(" dog"):
        s = s[:-4]
    return s.strip()

def variants(label: str) -> List[str]:
    base  = canon(label)
    outs  = {base}
    parts = base.split()
    outs.update(parts)                       # each individual word
    if len(parts) == 2:
        outs.add(" ".join(parts[::-1]))      # reversed two‑word form
    tight = "".join(parts)
    outs.add(tight)
    outs.add(_rx_caps.sub(r"\1 \2", tight))
    return list(outs)

# ───────── Build API maps once ─────────
def fetch_all_dogapi() -> Dict[str, Dict]:
    hdr, mp = {"x-api-key": DOG_API_KEY}, {}
    for b in requests.get(f"{DOG_API_URL}/breeds", headers=hdr, timeout=10).json():
        for v in variants(b["name"]):
            mp[v] = b
    return mp

def fetch_all_ninja() -> Dict[str, Dict]:
    hdr, offset, mp = {"X-Api-Key": NINJA_API_KEY}, 0, {}
    while True:
        page = requests.get(
            NINJA_API_URL, headers=hdr,
            params={"offset": offset, "min_weight": 1}, timeout=5
        ).json()
        if not page:
            break
        for r in page:
            for v in variants(r["name"]):
                mp[v] = r
        offset += 20
        time.sleep(0.25)
    return mp

dogapi_map, ninja_map = fetch_all_dogapi(), fetch_all_ninja()

# ───────── Helpers ─────────
def _pick_image(dog_info: Dict, ninja_info: Dict) -> Optional[str]:
    if dog_info.get("id"):
        try:
            res = requests.get(
                f"{DOG_API_URL}/images/search",
                headers={"x-api-key": DOG_API_KEY},
                params={"breed_ids": dog_info["id"], "limit": 1}, timeout=3
            ).json()
            if res:
                return res[0]["url"]
        except Exception:
            pass
    return ninja_info.get("image_link")

# ───────── FastAPI setup ─────────
app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

class PredictResponse(BaseModel):
    top: str
    probs: List[float]
    labels: List[str]
    info: Dict
    image_url: Optional[str] = None

# ───────── breed_info endpoint ─────────
@app.get("/breed_info")
def breed_info(label: str = Query(..., description="Raw model label")):
    label      = _clean(label)
    key        = canon(label)
    dog_info   = dogapi_map.get(key, {})
    ninja_info = ninja_map.get(key, {})

    if not ninja_info:                              # live fallback
        try:
            resp = requests.get(
                NINJA_API_URL, headers={"X-Api-Key": NINJA_API_KEY},
                params={"name": label}, timeout=4
            ).json()
            if resp:
                ninja_info = resp[0]
        except Exception:
            pass

    return {
        "thedogapi":  dog_info,
        "api_ninjas": ninja_info,
        "image_url":  _pick_image(dog_info, ninja_info),
    }

# ───────── predict endpoint ─────────
@app.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)):
    if not file.content_type.startswith("image"):
        raise HTTPException(400, "Upload an image file")

    pil   = Image.open(io.BytesIO(await file.read()))
    arr   = np.array(pil.convert("RGB").resize(IMG_SIZE))
    inp   = tf.keras.applications.efficientnet.preprocess_input(arr)
    preds = model.predict(np.expand_dims(inp, 0))[0]

    idxs   = preds.argsort()[-TOP_K:][::-1]
    probs  = preds[idxs].round(4).tolist()
    labels = [_clean(classes[i]) for i in idxs]

    dog_info   = dogapi_map.get(canon(labels[0]), {})
    ninja_info = ninja_map .get(canon(labels[0]), {})
    image_url  = _pick_image(dog_info, ninja_info)

    return {
        "top":       labels[0],
        "probs":     probs,
        "labels":    labels,
        "info":      {"thedogapi": dog_info, "api_ninjas": ninja_info},
        "image_url": image_url,
    }

class EmotionPredictResponse(BaseModel):
    top: str
    probs: List[float]
    labels: List[str]

# ───────── predict_emotion endpoint ─────────
@app.post("/predict_emotion", response_model=EmotionPredictResponse)
async def predict_emotion(file: UploadFile = File(...)):
    # 1) Validate upload
    if not file.content_type.startswith("image"):
        raise HTTPException(400, "Upload an image file")

    # 2) Read image & preprocess
    data = await file.read()
    pil  = Image.open(io.BytesIO(data)).convert("RGB")
    arr  = np.array(pil.resize(EMOTION_IMG_SIZE))
    inp  = tf.keras.applications.efficientnet.preprocess_input(arr)

    # 3) Predict
    preds = emotion_model.predict(np.expand_dims(inp, 0))[0]

    # 4) Grab top-K
    idxs   = preds.argsort()[-EMOTION_TOP_K:][::-1]
    probs  = preds[idxs].round(4).tolist()
    labels = [_clean(emotion_classes[i]) for i in idxs]

    # 5) Return structured response
    return EmotionPredictResponse(
        top=labels[0],
        probs=probs,
        labels=labels
    )
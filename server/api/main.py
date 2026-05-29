"""Byulie FastAPI backend for the React web app and dev studio."""

from pathlib import Path
import sys
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from server.api import config_store, services
from server.api.services import EMOTIONS, WEB_AUDIO_DIR
from server.local_only import validate_config_urls
from server.paths import REPO_ROOT as ROOT

app = FastAPI(
    title="Byulie API",
    version="1.0.0",
    description="Local-only API. No paid or remote inference endpoints.",
)


@app.on_event("startup")
def validate_local_config():
    validate_config_urls(config_store.load_config())

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    model: str | None = None
    temperature: float | None = None
    max_output_tokens: int | None = None
    system_prompt: str | None = None
    emotion: str | None = "Neutral"
    tone: str | None = None


class ConfigPatch(BaseModel):
    character: dict | None = None
    history_file: str | None = None
    llm: dict | None = None
    asr: dict | None = None
    presets: dict | None = None
    tts: dict | None = None


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "character": config_store.get_character_name(),
        "ollama": services.check_ollama(),
        "tts": services.check_tts(),
    }


@app.get("/api/config")
def get_config():
    return config_store.load_config()


@app.put("/api/config")
def put_config(patch: ConfigPatch):
    data = patch.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No configuration fields provided.")
    config = config_store.update_config(data)
    services.apply_config_reload()
    return {"config": config, "reloaded": True}


@app.post("/api/config/reload")
def reload_config():
    services.apply_config_reload()
    return {"config": config_store.load_config(), "reloaded": True}


@app.get("/api/meta")
def meta():
    llm = config_store.get_llm_defaults()
    ollama = services.check_ollama()
    models = ollama.get("models", []) if ollama.get("ok") else []
    defaults = [llm.get("model", "qwen3:4b")]
    return {
        "character_name": config_store.get_character_name(),
        "emotions": EMOTIONS,
        "models": list(dict.fromkeys(defaults + models)),
        "repo_root": str(ROOT),
    }


@app.post("/api/chat")
def chat(body: ChatRequest):
    message = body.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    try:
        return services.run_chat_pipeline(
            message,
            model=body.model,
            temperature=body.temperature,
            max_output_tokens=body.max_output_tokens,
            system_prompt=body.system_prompt,
            emotion=body.emotion,
            tone=body.tone,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/api/chat/audio")
async def chat_audio(
    file: UploadFile = File(...),
    model: str | None = Form(None),
    temperature: float | None = Form(None),
    max_output_tokens: int | None = Form(None),
    system_prompt: str | None = Form(None),
    emotion: str | None = Form("Neutral"),
    tone: str | None = Form(None),
):
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        temp_path = Path(tmp.name)

    try:
        result = services.run_audio_pipeline(
            temp_path,
            model=model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_prompt=system_prompt,
            emotion=emotion,
            tone=tone,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        temp_path.unlink(missing_ok=True)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.get("/api/audio/{filename}")
def get_audio(filename: str):
    safe_name = Path(filename).name
    audio_path = WEB_AUDIO_DIR / safe_name
    if not audio_path.is_file():
        raise HTTPException(status_code=404, detail="Audio not found.")
    return FileResponse(audio_path, media_type="audio/wav")

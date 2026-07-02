#!/usr/bin/env python3
"""Tiny HTTP API for Qwen3-TTS 12Hz 0.6B CustomVoice."""

from __future__ import annotations

import io
import json
import os
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


HOST = os.environ.get("QWEN_TTS_HOST", "0.0.0.0")
PORT = int(os.environ.get("QWEN_TTS_PORT", "5010"))
MODEL_ID = os.environ.get("QWEN_TTS_MODEL", "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice")
DEFAULT_LANGUAGE = os.environ.get("QWEN_TTS_LANGUAGE", "Korean")
DEFAULT_SPEAKER = os.environ.get("QWEN_TTS_VOICE", "Sohee")
DEFAULT_INSTRUCT = os.environ.get(
    "QWEN_TTS_INSTRUCT",
    "Speak in Korean with a lively, expressive, slightly sassy YouTube narration tone.",
)

_MODEL: Any = None
_TORCH: Any = None
_SOUNDFILE: Any = None


def normalize_speaker(value: str) -> str:
    speaker = (value or DEFAULT_SPEAKER).strip()
    if speaker.lower() in {"yuna", "juna"} or speaker in {"유나", "준서"}:
        return "Sohee"
    return speaker or "Sohee"


def load_model() -> Any:
    global _MODEL, _TORCH, _SOUNDFILE
    if _MODEL is not None:
        return _MODEL

    import torch
    import soundfile as sf
    from qwen_tts import Qwen3TTSModel

    _TORCH = torch
    _SOUNDFILE = sf

    if torch.cuda.is_available():
        device_map = "cuda:0"
        dtype = torch.bfloat16
    else:
        device_map = "cpu"
        dtype = torch.float32

    print(f"Loading {MODEL_ID} on {device_map} ...", flush=True)
    _MODEL = Qwen3TTSModel.from_pretrained(
        MODEL_ID,
        device_map=device_map,
        dtype=dtype,
    )
    print("Qwen3-TTS model loaded.", flush=True)
    return _MODEL


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def wav_response(handler: BaseHTTPRequestHandler, wav_bytes: bytes) -> None:
    handler.send_response(200)
    handler.send_header("Content-Type", "audio/wav")
    handler.send_header("Content-Length", str(len(wav_bytes)))
    handler.end_headers()
    handler.wfile.write(wav_bytes)


class QwenTTSHandler(BaseHTTPRequestHandler):
    server_version = "Qwen3TTSApi/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"{self.address_string()} {fmt % args}", flush=True)

    def do_GET(self) -> None:
        if self.path == "/health":
            json_response(
                self,
                200,
                {
                    "status": "ok",
                    "engine": "qwen3-tts-12hz-0.6b",
                    "model": MODEL_ID,
                    "loaded": _MODEL is not None,
                },
            )
            return

        if self.path == "/voices":
            json_response(
                self,
                200,
                {
                    "engine": "qwen3-tts-12hz-0.6b",
                    "model": MODEL_ID,
                    "voices": [
                        {
                            "name": "Sohee",
                            "language": "ko-KR",
                            "style": "warm Korean female voice with rich emotion",
                            "default": True,
                        }
                    ],
                },
            )
            return

        json_response(self, 404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/tts":
            json_response(self, 404, {"error": "not_found"})
            return

        try:
            payload = read_json(self)
        except json.JSONDecodeError:
            json_response(self, 400, {"error": "invalid_json"})
            return

        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            json_response(self, 400, {"error": "text is required"})
            return

        speaker = normalize_speaker(str(payload.get("speaker", payload.get("voice", DEFAULT_SPEAKER))))
        language = str(payload.get("language", DEFAULT_LANGUAGE) or DEFAULT_LANGUAGE)
        instruct = str(payload.get("instruct", DEFAULT_INSTRUCT) or DEFAULT_INSTRUCT)

        try:
            model = load_model()
            wavs, sample_rate = model.generate_custom_voice(
                text=text,
                language=language,
                speaker=speaker,
                instruct=instruct,
            )
            buffer = io.BytesIO()
            _SOUNDFILE.write(buffer, wavs[0], sample_rate, format="WAV")
            wav_response(self, buffer.getvalue())
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            json_response(
                self,
                500,
                {
                    "error": "qwen3_tts_failed",
                    "detail": str(exc),
                    "engine": "qwen3-tts-12hz-0.6b",
                    "model": MODEL_ID,
                },
            )


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), QwenTTSHandler)
    print(f"Qwen3-TTS API listening on http://{HOST}:{PORT}", flush=True)
    print(f"Model: {MODEL_ID}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

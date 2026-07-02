#!/usr/bin/env python3
"""Small stdlib API wrapper for the selected local Ollama model."""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse
from typing import Any


HOST = os.environ.get("LOCAL_LLM_API_HOST", "127.0.0.1")
PORT = int(os.environ.get("LOCAL_LLM_API_PORT", "8088"))
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.environ.get("LOCAL_LLM_MODEL", "local-qwen-4b")
DEFAULT_SYSTEM_PROMPT = os.environ.get(
    "LOCAL_LLM_SYSTEM_PROMPT",
    "You are a helpful local assistant. Answer in Korean unless the user asks otherwise. "
    "This server has a local AI TTS API that creates audio files on the host machine. "
    "Do not suggest Google TTS, gTTS, Amazon Polly, or cloud TTS unless the user explicitly asks for cloud services. "
    "If the user asks to make speech or TTS, provide the text to synthesize and rely on the host API to create the audio file.",
)
ROOT_DIR = pathlib.Path(__file__).resolve().parent
TTS_OUTPUT_DIR = pathlib.Path(os.environ.get("LOCAL_LLM_TTS_OUTPUT_DIR", ROOT_DIR / "tts_output")).resolve()
PIPER_DIR = pathlib.Path(os.environ.get("PIPER_DIR", ROOT_DIR / "piper")).resolve()
PIPER_EXE = pathlib.Path(os.environ.get("PIPER_EXE", PIPER_DIR / "piper" / "piper.exe")).resolve()
if not PIPER_EXE.exists():
    for alt_piper in (
        PIPER_DIR / "piper" / "piper" / "piper.exe",
        PIPER_DIR / "piper" / "piper",
        PIPER_DIR / "piper" / "piper" / "piper",
    ):
        if alt_piper.exists():
            PIPER_EXE = alt_piper.resolve()
            break
PIPER_MODEL = pathlib.Path(
    os.environ.get("PIPER_MODEL", PIPER_DIR / "voices" / "en_US-lessac-medium.onnx")
).resolve()
PIPER_CONFIG = pathlib.Path(os.environ.get("PIPER_CONFIG", f"{PIPER_MODEL}.json")).resolve()
TTS_ENGINE = os.environ.get("LOCAL_TTS_ENGINE", "qwen3").lower()
QWEN_TTS_BASE_URL = os.environ.get("QWEN_TTS_BASE_URL", "http://127.0.0.1:5010")
QWEN_TTS_MODEL = os.environ.get("QWEN_TTS_MODEL", "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice")
QWEN_TTS_VOICE = os.environ.get("QWEN_TTS_VOICE", "Sohee")
QWEN_TTS_LANGUAGE = os.environ.get("QWEN_TTS_LANGUAGE", "Korean")
QWEN_TTS_INSTRUCT = os.environ.get(
    "QWEN_TTS_INSTRUCT",
    "Speak in Korean with a lively, expressive, slightly sassy YouTube narration tone.",
)
ORPHEUS_TTS_BASE_URL = os.environ.get("ORPHEUS_TTS_BASE_URL", "http://127.0.0.1:5005")
ORPHEUS_TTS_MODEL = os.environ.get("ORPHEUS_TTS_MODEL", "orpheus-3b-korean")
ORPHEUS_TTS_VOICE = os.environ.get("ORPHEUS_TTS_VOICE", "유나")
ORPHEUS_TTS_RESPONSE_FORMAT = os.environ.get("ORPHEUS_TTS_RESPONSE_FORMAT", "wav")
EDGE_TTS_VOICE = os.environ.get("EDGE_TTS_VOICE", "ko-KR-SunHiNeural")
EDGE_TTS_RATE = os.environ.get("EDGE_TTS_RATE", "+8%")
EDGE_TTS_PITCH = os.environ.get("EDGE_TTS_PITCH", "+6Hz")


def tts_engine_name() -> str:
    return TTS_ENGINE


def content_type_for(path: pathlib.Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".wav":
        return "audio/wav"
    if suffix == ".mp3":
        return "audio/mpeg"
    if suffix in {".aiff", ".aif"}:
        return "audio/aiff"
    return "application/octet-stream"


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def file_response(handler: BaseHTTPRequestHandler, status: int, path: pathlib.Path, content_type: str) -> None:
    data = path.read_bytes()
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


def post_ollama(path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{OLLAMA_BASE_URL.rstrip('/')}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, {"error": body}
    except urllib.error.URLError as exc:
        return 502, {"error": f"Ollama is not reachable: {exc.reason}"}


def run_powershell(args: list[str], timeout: int = 180) -> tuple[int, str, str]:
    powershell = os.environ.get("LOCAL_LLM_POWERSHELL", "powershell.exe")
    result = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def list_tts_voices() -> tuple[int, dict[str, Any]]:
    if TTS_ENGINE in {"qwen", "qwen3", "qwen3-tts"}:
        return 200, {
            "engine": "qwen3-tts-12hz-0.6b",
            "base_url": QWEN_TTS_BASE_URL,
            "model": QWEN_TTS_MODEL,
            "language": QWEN_TTS_LANGUAGE,
            "default_voice": QWEN_TTS_VOICE,
            "default_instruct": QWEN_TTS_INSTRUCT,
            "voices": [
                {
                    "name": "Sohee",
                    "language": "ko-KR",
                    "style": "warm Korean female voice with rich emotion",
                    "default": QWEN_TTS_VOICE == "Sohee",
                },
            ],
        }

    if TTS_ENGINE == "orpheus":
        return 200, {
            "engine": "orpheus-3b-korean",
            "base_url": ORPHEUS_TTS_BASE_URL,
            "model": ORPHEUS_TTS_MODEL,
            "default_voice": ORPHEUS_TTS_VOICE,
            "voices": [
                {
                    "name": "유나",
                    "language": "ko-KR",
                    "style": "bright expressive Korean female voice",
                    "default": ORPHEUS_TTS_VOICE == "유나",
                },
                {
                    "name": "준서",
                    "language": "ko-KR",
                    "style": "expressive Korean male voice",
                    "default": ORPHEUS_TTS_VOICE == "준서",
                },
            ],
            "emotion_tags": ["<laugh>", "<chuckle>", "<sigh>", "<cough>", "<sniffle>", "<groan>", "<yawn>", "<gasp>"],
        }

    if TTS_ENGINE == "edge":
        return 200, {
            "engine": "edge-tts",
            "voices": [
                {
                    "name": "ko-KR-SunHiNeural",
                    "language": "ko-KR",
                    "gender": "Female",
                    "style": "bright Korean neural voice",
                    "default": EDGE_TTS_VOICE == "ko-KR-SunHiNeural",
                },
                {
                    "name": "ko-KR-InJoonNeural",
                    "language": "ko-KR",
                    "gender": "Male",
                    "style": "Korean neural voice",
                    "default": EDGE_TTS_VOICE == "ko-KR-InJoonNeural",
                },
            ],
        }

    return 200, {
        "engine": tts_engine_name(),
        "piper_exe": str(PIPER_EXE),
        "voices": [
            {
                "name": PIPER_MODEL.stem,
                "model": str(PIPER_MODEL),
                "config": str(PIPER_CONFIG),
                "available": PIPER_EXE.exists() and PIPER_MODEL.exists(),
            }
        ],
    }


def synthesize_tts(text: str, voice: str = "", rate: int = 0, volume: int = 100) -> tuple[int, dict[str, Any]]:
    if not text.strip():
        return 400, {"error": "text is required"}

    if TTS_ENGINE in {"qwen", "qwen3", "qwen3-tts"}:
        TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        audio_id = uuid.uuid4().hex
        output_path = TTS_OUTPUT_DIR / f"{audio_id}.wav"
        selected_voice = voice or QWEN_TTS_VOICE
        if selected_voice.lower() in {"yuna", "유나", "juna", "준서"}:
            selected_voice = "Sohee"
        request_payload = {
            "text": text,
            "speaker": selected_voice,
            "language": QWEN_TTS_LANGUAGE,
            "instruct": QWEN_TTS_INSTRUCT,
            "rate": rate,
        }
        data = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{QWEN_TTS_BASE_URL.rstrip('/')}/tts",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                output_path.write_bytes(response.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return exc.code, {
                "error": "qwen3_tts_failed",
                "engine": "qwen3-tts-12hz-0.6b",
                "detail": detail,
            }
        except urllib.error.URLError as exc:
            return 502, {
                "error": "qwen3_tts_not_reachable",
                "engine": "qwen3-tts-12hz-0.6b",
                "detail": f"Start Qwen3-TTS server first, then set QWEN_TTS_BASE_URL. Reason: {exc.reason}",
                "base_url": QWEN_TTS_BASE_URL,
            }

        if not output_path.exists() or output_path.stat().st_size == 0:
            return 500, {
                "error": "qwen3_tts_empty_audio",
                "engine": "qwen3-tts-12hz-0.6b",
                "base_url": QWEN_TTS_BASE_URL,
            }

        return 200, {
            "audio_id": audio_id,
            "audio_url": f"/audio/{output_path.name}",
            "audio_path": str(output_path),
            "content_type": content_type_for(output_path),
            "engine": "qwen3-tts-12hz-0.6b",
            "model": QWEN_TTS_MODEL,
            "voice": selected_voice,
            "language": QWEN_TTS_LANGUAGE,
            "rate": rate,
            "volume": volume,
        }

    if TTS_ENGINE == "orpheus":
        TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        audio_id = uuid.uuid4().hex
        response_format = ORPHEUS_TTS_RESPONSE_FORMAT.lower().lstrip(".")
        if response_format not in {"wav", "mp3"}:
            response_format = "wav"
        output_path = TTS_OUTPUT_DIR / f"{audio_id}.{response_format}"
        selected_voice = voice or ORPHEUS_TTS_VOICE
        speed = 1.0 + (max(-50, min(50, rate)) / 100.0)
        request_payload = {
            "model": ORPHEUS_TTS_MODEL,
            "input": text,
            "voice": selected_voice,
            "response_format": response_format,
            "speed": speed,
        }
        data = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{ORPHEUS_TTS_BASE_URL.rstrip('/')}/v1/audio/speech",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                output_path.write_bytes(response.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return exc.code, {
                "error": "orpheus_tts_failed",
                "engine": "orpheus-3b-korean",
                "detail": detail,
            }
        except urllib.error.URLError as exc:
            return 502, {
                "error": "orpheus_tts_not_reachable",
                "engine": "orpheus-3b-korean",
                "detail": f"Start Orpheus-FastAPI first, then set ORPHEUS_TTS_BASE_URL. Reason: {exc.reason}",
                "base_url": ORPHEUS_TTS_BASE_URL,
            }

        if not output_path.exists() or output_path.stat().st_size == 0:
            return 500, {
                "error": "orpheus_tts_empty_audio",
                "engine": "orpheus-3b-korean",
                "base_url": ORPHEUS_TTS_BASE_URL,
            }

        return 200, {
            "audio_id": audio_id,
            "audio_url": f"/audio/{output_path.name}",
            "audio_path": str(output_path),
            "content_type": content_type_for(output_path),
            "engine": "orpheus-3b-korean",
            "model": ORPHEUS_TTS_MODEL,
            "voice": selected_voice,
            "rate": rate,
            "speed": speed,
            "volume": volume,
        }

    if TTS_ENGINE == "edge":
        TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        audio_id = uuid.uuid4().hex
        output_path = TTS_OUTPUT_DIR / f"{audio_id}.mp3"
        selected_voice = voice or EDGE_TTS_VOICE

        if rate:
            rate_arg = f"{max(-50, min(50, rate)):+d}%"
        else:
            rate_arg = EDGE_TTS_RATE

        args = [
            sys.executable,
            "-m",
            "edge_tts",
            "--voice",
            selected_voice,
            "--rate",
            rate_arg,
            "--pitch",
            EDGE_TTS_PITCH,
            "--text",
            text,
            "--write-media",
            str(output_path),
        ]

        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        if result.returncode != 0 or not output_path.exists():
            return 500, {
                "error": "tts_failed",
                "engine": "edge-tts",
                "detail": result.stderr.strip() or result.stdout.strip(),
            }

        return 200, {
            "audio_id": audio_id,
            "audio_url": f"/audio/{output_path.name}",
            "audio_path": str(output_path),
            "content_type": content_type_for(output_path),
            "engine": "edge-tts",
            "voice": selected_voice,
            "rate": rate_arg,
            "pitch": EDGE_TTS_PITCH,
            "volume": volume,
        }

    if not PIPER_EXE.exists():
        return 500, {
            "error": "piper_not_installed",
            "detail": "Run local-llm\\Install-Piper.ps1 on Windows or ./local-llm/install-piper.sh on macOS/Linux.",
            "piper_exe": str(PIPER_EXE),
        }
    if not PIPER_MODEL.exists():
        return 500, {
            "error": "piper_model_missing",
            "detail": "Download a Piper .onnx model and set PIPER_MODEL, or run the install script.",
            "model": str(PIPER_MODEL),
        }

    TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    audio_id = uuid.uuid4().hex
    output_path = TTS_OUTPUT_DIR / f"{audio_id}.wav"
    args = [
        str(PIPER_EXE),
        "--model",
        str(PIPER_MODEL),
        "--output_file",
        str(output_path),
    ]
    if PIPER_CONFIG.exists():
        args.extend(["--config", str(PIPER_CONFIG)])

    result = subprocess.run(
        args,
        input=text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    if result.returncode != 0 or not output_path.exists():
        return 500, {
            "error": "tts_failed",
            "detail": result.stderr.strip() or result.stdout.strip(),
        }

    return 200, {
        "audio_id": audio_id,
        "audio_url": f"/audio/{output_path.name}",
        "audio_path": str(output_path),
        "content_type": content_type_for(output_path),
        "engine": tts_engine_name(),
        "voice": voice or PIPER_MODEL.stem,
        "model": str(PIPER_MODEL),
        "rate": rate,
        "volume": volume,
    }


class LocalLLMHandler(BaseHTTPRequestHandler):
    server_version = "LocalLLMApi/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {self.address_string()} {fmt % args}")

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            payload = {
                "status": "ok",
                "model": DEFAULT_MODEL,
                "ollama_base_url": OLLAMA_BASE_URL,
                "tts": {
                    "engine": tts_engine_name(),
                    "output_dir": str(TTS_OUTPUT_DIR),
                },
            }
            json_response(self, 200, payload)
            return

        if path == "/tts/voices":
            status, payload = list_tts_voices()
            json_response(self, status, payload)
            return

        if path.startswith("/audio/"):
            filename = pathlib.Path(unquote(path.removeprefix("/audio/"))).name
            audio_path = (TTS_OUTPUT_DIR / filename).resolve()
            try:
                audio_path.relative_to(TTS_OUTPUT_DIR)
            except ValueError:
                json_response(self, 400, {"error": "invalid_audio_path"})
                return
            if not audio_path.exists() or audio_path.suffix.lower() not in {".wav", ".mp3", ".aiff", ".aif"}:
                json_response(self, 404, {"error": "audio_not_found"})
                return
            file_response(self, 200, audio_path, content_type_for(audio_path))
            return

        if path == "/v1/models":
            payload = {
                "object": "list",
                "data": [
                    {
                        "id": DEFAULT_MODEL,
                        "object": "model",
                        "created": 0,
                        "owned_by": "local",
                    }
                ],
            }
            json_response(self, 200, payload)
            return

        json_response(self, 404, {"error": "not_found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            payload = read_json(self)
        except json.JSONDecodeError:
            json_response(self, 400, {"error": "invalid_json"})
            return

        if path == "/v1/chat/completions":
            payload.setdefault("model", DEFAULT_MODEL)
            status, response = post_ollama("/v1/chat/completions", payload)
            json_response(self, status, response)
            return

        if path == "/tts":
            text = payload.get("text")
            if not isinstance(text, str):
                json_response(self, 400, {"error": "text is required"})
                return
            status, response = synthesize_tts(
                text=text,
                voice=str(payload.get("voice", "")),
                rate=int(payload.get("rate", 0)),
                volume=int(payload.get("volume", 100)),
            )
            json_response(self, status, response)
            return

        if path == "/chat":
            message = payload.get("message")
            if not isinstance(message, str) or not message.strip():
                json_response(self, 400, {"error": "message is required"})
                return

            request = {
                "model": payload.get("model", DEFAULT_MODEL),
                "messages": [
                    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                "stream": False,
            }
            status, response = post_ollama("/v1/chat/completions", request)
            if status >= 400:
                json_response(self, status, response)
                return

            content = response["choices"][0]["message"]["content"]
            json_response(self, 200, {"model": request["model"], "response": content})
            return

        if path == "/chat/tts":
            message = payload.get("message")
            if not isinstance(message, str) or not message.strip():
                json_response(self, 400, {"error": "message is required"})
                return

            request = {
                "model": payload.get("model", DEFAULT_MODEL),
                "messages": payload.get("messages")
                or [
                    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                "stream": False,
            }
            status, response = post_ollama("/v1/chat/completions", request)
            if status >= 400:
                json_response(self, status, response)
                return

            content = response["choices"][0]["message"]["content"]
            tts_status, tts_response = synthesize_tts(
                text=content,
                voice=str(payload.get("voice", "")),
                rate=int(payload.get("rate", 0)),
                volume=int(payload.get("volume", 100)),
            )
            if tts_status >= 400:
                json_response(self, tts_status, {"model": request["model"], "response": content, "tts": tts_response})
                return

            json_response(self, 200, {"model": request["model"], "response": content, "tts": tts_response})
            return

        json_response(self, 404, {"error": "not_found"})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), LocalLLMHandler)
    print(f"Local LLM API listening on http://{HOST}:{PORT}")
    print(f"Proxying Ollama at {OLLAMA_BASE_URL} with default model {DEFAULT_MODEL}")
    server.serve_forever()


if __name__ == "__main__":
    main()

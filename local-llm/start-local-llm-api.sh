#!/usr/bin/env bash
set -euo pipefail

export LOCAL_LLM_API_HOST="${LOCAL_LLM_API_HOST:-127.0.0.1}"
export LOCAL_LLM_API_PORT="${LOCAL_LLM_API_PORT:-8088}"
export LOCAL_LLM_MODEL="${LOCAL_LLM_MODEL:-local-qwen-4b}"
export OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://127.0.0.1:11434}"
export LOCAL_TTS_ENGINE="${LOCAL_TTS_ENGINE:-qwen3}"
export QWEN_TTS_BASE_URL="${QWEN_TTS_BASE_URL:-http://127.0.0.1:5010}"
export QWEN_TTS_MODEL="${QWEN_TTS_MODEL:-Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice}"
export QWEN_TTS_VOICE="${QWEN_TTS_VOICE:-Sohee}"
export ORPHEUS_TTS_BASE_URL="${ORPHEUS_TTS_BASE_URL:-http://127.0.0.1:5005}"
export ORPHEUS_TTS_MODEL="${ORPHEUS_TTS_MODEL:-orpheus-3b-korean}"
export ORPHEUS_TTS_VOICE="${ORPHEUS_TTS_VOICE:-유나}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python_bin="${PYTHON:-python3}"
exec "$python_bin" "$script_dir/api_server.py"

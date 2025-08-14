#!/usr/bin/env python3
"""
Transcriptor offline (Vosk - Español) a partir de MP3.
- Usa FFmpeg portatil en tools/ffmpeg/**/bin/ffmpeg.exe
- Convierte MP3 a WAV mono 16 kHz
- Transcribe localmente con Vosk (sin APIs)

Uso: python transcribir_mp3_vosk.py
"""

import os
import sys
import time
import json
import wave
import zipfile
import subprocess
from pathlib import Path

try:
    import requests
except Exception:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "--quiet"], check=False)
    import requests

VIDEO_STEM = "CUANTT - Sales Force - Sesión de Marketing, Comunicación y Cuidado Preventivo-20250811"
MP3_FILE = f"{VIDEO_STEM}.mp3"
WORKDIR = Path.cwd()
TOOLS_DIR = WORKDIR / "tools"
FFMPEG_ROOT = TOOLS_DIR / "ffmpeg"
MODELS_DIR = WORKDIR / "models"
VOSK_MODEL_NAME = "vosk-model-small-es-0.42"
VOSK_MODEL_ZIP = MODELS_DIR / f"{VOSK_MODEL_NAME}.zip"
VOSK_MODEL_DIR = MODELS_DIR / VOSK_MODEL_NAME
WAV_FILE = WORKDIR / f"{VIDEO_STEM}_16k_mono.wav"
OUTPUT_FILE = WORKDIR / f"{VIDEO_STEM}_transcripcion_vosk.txt"

FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def log(msg: str) -> None:
    # Evitar caracteres no ASCII por codificacion cp1252 en algunas consolas
    print(f"{time.strftime('%H:%M:%S')} - {msg}")


def ensure_dirs() -> None:
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    FFMPEG_ROOT.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest: Path) -> None:
    log(f"Descargando: {url}")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
    log(f"Descargado en: {dest}")


def ensure_ffmpeg() -> Path:
    # Buscar ffmpeg.exe existente en tools/ffmpeg
    for exe in FFMPEG_ROOT.rglob("ffmpeg.exe"):
        log(f"FFmpeg localizado: {exe}")
        return exe
    # Si no existe, descargar y extraer
    zip_path = FFMPEG_ROOT / "ffmpeg-release-essentials.zip"
    if not zip_path.exists():
        download_file(FFMPEG_URL, zip_path)
    log("Extrayendo FFmpeg...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(FFMPEG_ROOT)
    for exe in FFMPEG_ROOT.rglob("ffmpeg.exe"):
        log(f"FFmpeg localizado: {exe}")
        return exe
    raise FileNotFoundError("No se encontro ffmpeg.exe tras la extraccion")


def convert_mp3_to_wav(ffmpeg_exe: Path, input_mp3: Path, output_wav: Path) -> None:
    if not input_mp3.exists():
        raise FileNotFoundError(f"No existe el MP3: {input_mp3}")
    if output_wav.exists():
        log("WAV ya existe, se reutiliza")
        return
    log("Convirtiendo MP3 a WAV mono 16kHz...")
    cmd = [
        str(ffmpeg_exe),
        "-y",
        "-i", str(input_mp3),
        "-ac", "1",
        "-ar", "16000",
        str(output_wav)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log(result.stderr.strip())
        raise RuntimeError("Fallo la conversion con FFmpeg")
    log("Conversion completada")


def ensure_vosk_installed() -> None:
    try:
        import vosk  # noqa: F401
        return
    except Exception:
        log("Instalando paquete vosk...")
        subprocess.run([sys.executable, "-m", "pip", "install", "vosk", "--quiet"], check=True)
        return


def ensure_vosk_model() -> Path:
    if VOSK_MODEL_DIR.exists() and any(VOSK_MODEL_DIR.iterdir()):
        log(f"Modelo Vosk listo: {VOSK_MODEL_DIR}")
        return VOSK_MODEL_DIR
    if not VOSK_MODEL_ZIP.exists():
        url = f"https://alphacephei.com/vosk/models/{VOSK_MODEL_NAME}.zip"
        download_file(url, VOSK_MODEL_ZIP)
    log("Extrayendo modelo Vosk...")
    with zipfile.ZipFile(VOSK_MODEL_ZIP, 'r') as z:
        z.extractall(MODELS_DIR)
    if VOSK_MODEL_DIR.exists():
        return VOSK_MODEL_DIR
    # fallback: buscar carpeta parecida
    for d in MODELS_DIR.iterdir():
        if d.is_dir() and d.name.startswith("vosk-model-small-es"):
            return d
    raise FileNotFoundError("No se encontro la carpeta del modelo Vosk tras la extraccion")


def transcribe_with_vosk(wav_path: Path, model_dir: Path) -> str:
    import vosk
    from vosk import KaldiRecognizer
    log("Cargando modelo Vosk (puede tardar)...")
    model = vosk.Model(model_dir.as_posix())
    with wave.open(str(wav_path), "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            raise ValueError("WAV debe ser mono 16-bit 16000Hz")
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)
        results = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if 'text' in res:
                    results.append(res['text'])
        res = json.loads(rec.FinalResult())
        if 'text' in res:
            results.append(res['text'])
    return " ".join(x.strip() for x in results if x.strip()).strip()


def main() -> None:
    log("Transcriptor offline Vosk - Espanol")
    if not Path(MP3_FILE).exists():
        log(f"No se encontro el MP3: {MP3_FILE}")
        return

    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        ffmpeg_exe = ensure_ffmpeg()
    except Exception as e:
        log(f"Error preparando FFmpeg: {e}")
        return

    try:
        convert_mp3_to_wav(ffmpeg_exe, Path(MP3_FILE), WAV_FILE)
    except Exception as e:
        log(f"Error de conversion: {e}")
        return

    try:
        ensure_vosk_installed()
        model_dir = ensure_vosk_model()
    except Exception as e:
        log(f"Error preparando Vosk: {e}")
        return

    try:
        text = transcribe_with_vosk(WAV_FILE, model_dir)
        if not text:
            log("Aviso: No se obtuvo texto. Verifique la claridad del audio.")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("TRANSCRIPCION (Vosk - Espanol)\n")
            f.write("================================\n\n")
            f.write(text + "\n")
        log(f"Transcripcion guardada: {OUTPUT_FILE}")
        log(f"Caracteres: {len(text)}")
    except Exception as e:
        log(f"Error durante la transcripcion: {e}")
        return

    log("Proceso completado")


if __name__ == "__main__":
    main()


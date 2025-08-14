#!/usr/bin/env python3
"""
Conversor MP4 a MP3 sin instalación (Windows)
- Descarga FFmpeg portátil (zip) localmente la primera vez
- Convierte el MP4 a MP3 usando libmp3lame
- No requiere privilegios de administrador ni que FFmpeg esté en PATH

Uso: python convert_mp4_to_mp3.py
"""

import os
import sys
import time
import zipfile
import subprocess
from pathlib import Path

try:
    import requests
except Exception:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "--quiet"], check=False)
    import requests

VIDEO_FILE = "CUANTT - Sales Force - Sesión de Marketing, Comunicación y Cuidado Preventivo-20250811.mp4"
WORKDIR = Path.cwd()
TOOLS_DIR = WORKDIR / "tools"
FFMPEG_ROOT = TOOLS_DIR / "ffmpeg"
FFMPEG_ZIP = FFMPEG_ROOT / "ffmpeg-release-essentials.zip"
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def log(msg: str) -> None:
    # Sin emojis para evitar UnicodeEncodeError en Windows cp1252
    print(f"{time.strftime('%H:%M:%S')} - {msg}")


def ensure_dirs() -> None:
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    FFMPEG_ROOT.mkdir(parents=True, exist_ok=True)


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
    # Buscar ffmpeg.exe si ya existe extraído
    for exe in FFMPEG_ROOT.rglob("ffmpeg.exe"):
        log(f"FFmpeg localizado: {exe}")
        return exe
    # Descargar y extraer
    if not FFMPEG_ZIP.exists():
        download_file(FFMPEG_URL, FFMPEG_ZIP)
    log("Extrayendo FFmpeg...")
    with zipfile.ZipFile(FFMPEG_ZIP, 'r') as z:
        z.extractall(FFMPEG_ROOT)
    for exe in FFMPEG_ROOT.rglob("ffmpeg.exe"):
        log(f"FFmpeg localizado: {exe}")
        return exe
    raise FileNotFoundError("No se pudo localizar ffmpeg.exe tras la extracción")


def convert_mp4_to_mp3(input_mp4: Path, ffmpeg_exe: Path) -> Path:
    if not input_mp4.exists():
        raise FileNotFoundError(f"No existe el archivo: {input_mp4}")
    output_mp3 = input_mp4.with_suffix("")
    output_mp3 = Path(str(output_mp3) + ".mp3")

    log("Iniciando conversión MP4 -> MP3 (libmp3lame, 192 kbps)...")
    cmd = [
        str(ffmpeg_exe),
        "-y",
        "-i", str(input_mp4),
        "-vn",
        "-acodec", "libmp3lame",
        "-b:a", "192k",
        str(output_mp3)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log(result.stderr.strip())
        raise RuntimeError("Fallo la conversión con FFmpeg")
    if not output_mp3.exists():
        raise RuntimeError("La conversión finalizó sin crear el archivo MP3")
    log("Conversión completada")
    return output_mp3


def main() -> None:
    log("Conversor MP4 a MP3 (FFmpeg portátil)")
    input_mp4 = WORKDIR / VIDEO_FILE
    if not input_mp4.exists():
        log(f"No se encontró el archivo MP4 esperado: {input_mp4.name}")
        log("Coloca el MP4 en esta carpeta o renombra VIDEO_FILE en el script")
        return

    ensure_dirs()
    try:
        ffmpeg_exe = ensure_ffmpeg()
    except Exception as e:
        log(f"Error preparando FFmpeg: {e}")
        return

    try:
        out = convert_mp4_to_mp3(input_mp4, ffmpeg_exe)
        log(f"Archivo MP3 creado: {out}")
    except Exception as e:
        log(f"Error en la conversión: {e}")
        return

    log("Proceso finalizado")


if __name__ == "__main__":
    main()


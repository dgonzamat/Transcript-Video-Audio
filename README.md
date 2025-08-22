# Transcript Video - Offline

Conversión y transcripción offline (sin APIs) para Windows.

## Requisitos
- Python 3.10+ (probado en 3.13)
- Conexión a Internet solo la primera vez (descargas automáticas)

## Scripts
- `convert_mp4_to_mp3.py`: Convierte MP4 -> MP3 usando FFmpeg portátil (descarga automática).
- `transcribir_mp3_vosk.py`: Convierte MP3 -> WAV 16kHz mono y transcribe con Vosk (modelo español pequeño).

## Uso
1. Coloca tu video en la carpeta del proyecto con el nombre:
   `CUANTT - Sales Force - Sesión de Marketing, Comunicación y Cuidado Preventivo-20250811.mp4`

2. Convertir a MP3:
   ```bash
   python convert_mp4_to_mp3.py
   ```
   Salida: `...20250811.mp3`

3. Transcribir (offline, sin APIs):
   ```bash
   python transcribir_mp3_vosk.py
   ```
   - Descarga `FFmpeg` portátil si no existe (en `tools/`)
   - Descarga el modelo `vosk-model-small-es-0.42` (en `models/`)
   - Genera: `..._transcripcion_vosk.txt`

## Notas
- El modelo "small" es más rápido pero menos preciso. Puedes cambiar `VOSK_MODEL_NAME` por un modelo más grande de español desde `https://alphacephei.com/vosk/models`.
- No se suben a git los binarios (`tools/`), modelos (`models/`) ni archivos grandes (`.mp4`, `.mp3`, `.wav`).
- Si cambias el nombre del video, actualiza las variables en los scripts.

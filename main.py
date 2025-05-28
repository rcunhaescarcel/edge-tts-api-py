import uuid
import subprocess
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/speak")
async def speak(
    text: str,
    background_tasks: BackgroundTasks,
    voice: str = "pt-BR-AntonioNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    format: str = "audio-16khz-128kbitrate-mono-mp3"
):
    """
    Gera um MP3 usando edge-tts CLI no formato desejado (sem FFmpeg).
    Query params:
      - text:   texto a ser falado (obrigatório)
      - voice:  voz neural (ex: pt-BR-AntonioNeural)
      - rate:   velocidade (ex: +20%, -10%)
      - pitch:  tom em Hz (ex: +100Hz, -50Hz)
      - format: formato direto de saída (padrão MP3 mono 16kHz)
    """
    if not text:
        raise HTTPException(status_code=400, detail="O parâmetro 'text' é obrigatório.")

    # Normaliza rate → [+|-]<número>%
    r = rate.strip().rstrip("%").strip()
    if not r.startswith(("+", "-")):
        r = "+" + r
    rate_sanitized = r + "%"

    # Normaliza pitch → [+|-]<número>Hz
    p = pitch.strip().rstrip("Hz").strip()
    if not p.startswith(("+", "-")):
        p = "+" + p
    pitch_sanitized = p + "Hz"

    # Nome temporário único
    tmp_filename = f"/tmp/voice-{uuid.uuid4()}.mp3"

    # Monta comando edge-tts, incluindo --format para MP3 direto
    cmd = [
        "edge-tts",
        f"--voice={voice}",
        f"--text={text}",
        f"--rate={rate_sanitized}",
        f"--pitch={pitch_sanitized}",
        f"--format={format}",
        f"--write-media={tmp_filename}"
    ]

    # Executa o edge-tts
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        detail = e.stderr.decode(errors="ignore")
        raise HTTPException(status_code=500, detail=f"Erro edge-tts: {detail}")

    # Confere geração do arquivo
    if not os.path.isfile(tmp_filename):
        raise HTTPException(status_code=500, detail="Não foi possível gerar o áudio.")

    # Agenda remoção do arquivo temporário após enviar
    background_tasks.add_task(os.remove, tmp_filename)

    # Retorna o MP3 ao cliente
    return FileResponse(
        path=tmp_filename,
        media_type="audio/mpeg",
        filename="voz.mp3",
        headers={"Content-Disposition": 'inline; filename="voz.mp3"'}
    )

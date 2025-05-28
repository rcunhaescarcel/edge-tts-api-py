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
    pitch: str = "+0Hz"
):
    """
    Gera um MP3 com edge-tts CLI e remove o arquivo temporário após enviar.
    Query params:
      - text:  texto a ser falado (obrigatório)
      - voice: voz neural (ex: pt-BR-AntonioNeural)
      - rate:  velocidade em %, aceita 5, +5, 5%, -5, -5% (é convertido para +5% ou -5%)
      - pitch: tom em Hz, aceita 100, +100, 100Hz, -50, -50Hz (é convertido para +100Hz ou -50Hz)
    """
    if not text:
        raise HTTPException(status_code=400, detail="O parâmetro 'text' é obrigatório.")

    # Normalização do rate → [+|-]<número>%
    r = rate.strip().rstrip("%").strip()
    if not r.startswith(("+", "-")):
        r = "+" + r
    rate_sanitized = r + "%"

    # Normalização do pitch → [+|-]<número>Hz
    p = pitch.strip().rstrip("Hz").strip()
    if not p.startswith(("+", "-")):
        p = "+" + p
    pitch_sanitized = p + "Hz"

    # Nome único para o arquivo temporário
    tmp_filename = f"/tmp/voice-{uuid.uuid4()}.mp3"

    # Monta o comando da CLI edge-tts
    cmd = [
        "edge-tts",
        "--voice", voice,
        "--text", text,
        "--rate", rate_sanitized,
        "--pitch", pitch_sanitized,
        "--write-media", tmp_filename
    ]

    # Executa o edge-tts para gerar o MP3
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        detail = e.stderr.decode(errors="ignore")
        raise HTTPException(status_code=500, detail=f"Erro edge-tts: {detail}")

    # Verifica se o arquivo foi gerado
    if not os.path.isfile(tmp_filename):
        raise HTTPException(status_code=500, detail="Não foi possível gerar o áudio.")

    # Agenda a remoção do arquivo após o envio
    background_tasks.add_task(os.remove, tmp_filename)

    # Retorna o MP3 ao cliente
    return FileResponse(
        path=tmp_filename,
        media_type="audio/mpeg",
        filename="voz.mp3",
        headers={"Content-Disposition": 'inline; filename="voz.mp3"'}
    )

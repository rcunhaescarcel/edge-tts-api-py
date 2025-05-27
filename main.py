import uuid
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os

app = FastAPI()

@app.get("/speak")
async def speak(
    text: str,
    voice: str = "pt-BR-AntonioNeural",
    rate: str = "0%",
    pitch: str = "0st"
):
    """
    Gera um arquivo MP3 usando edge-tts CLI.

    Query params:
    - text:  texto a ser falado (obrigatório)
    - voice: voz neural (padrão pt-BR-AntonioNeural)
    - rate:  velocidade (+/- %, ex: +20%, -10%) — padrão 0%
    - pitch: tom em semitons (+/- st, ex: +2st, -3st) — padrão 0st
    """
    if not text:
        raise HTTPException(status_code=400, detail="O parâmetro 'text' é obrigatório.")

    # Nome temporário único
    tmp_filename = f"/tmp/voice-{uuid.uuid4()}.mp3"

    # Monta o comando da CLI edge-tts
    cmd = [
        "edge-tts",
        "--voice", voice,
        "--text", text,
        "--rate", rate,
        "--pitch", pitch,
        "--write-media", tmp_filename
    ]

    # Executa o processo
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        detail = e.stderr.decode(errors="ignore")
        raise HTTPException(status_code=500, detail=f"Erro edge-tts: {detail}")

    # Verifica se o arquivo foi gerado
    if not os.path.isfile(tmp_filename):
        raise HTTPException(status_code=500, detail="Não foi possível gerar o áudio.")

    # Retorna o MP3 ao cliente
    return FileResponse(
        path=tmp_filename,
        media_type="audio/mpeg",
        filename="voz.mp3",
        headers={"Content-Disposition": 'inline; filename="voz.mp3"'}
    )

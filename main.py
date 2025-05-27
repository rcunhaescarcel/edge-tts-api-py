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
    rate: str = "+0%",      # velocidade: +0% por padrão
    pitch: str = "+0Hz"     # tom: +0Hz por padrão
):
    if not text:
        raise HTTPException(status_code=400, detail="O parâmetro 'text' é obrigatório.")

    tmp_filename = f"/tmp/voice-{uuid.uuid4()}.mp3"

    cmd = [
        "edge-tts",
        "--voice", voice,
        "--text", text,
        "--rate", rate,
        "--pitch", pitch,
        "--write-media", tmp_filename
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        detail = e.stderr.decode(errors="ignore")
        raise HTTPException(status_code=500, detail=f"Erro edge-tts: {detail}")

    if not os.path.isfile(tmp_filename):
        raise HTTPException(status_code=500, detail="Não foi possível gerar o áudio.")

    return FileResponse(
        path=tmp_filename,
        media_type="audio/mpeg",
        filename="voz.mp3",
        headers={"Content-Disposition": 'inline; filename="voz.mp3"'}
    )

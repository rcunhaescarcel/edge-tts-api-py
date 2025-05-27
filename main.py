import uuid
import subprocess
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/speak")
async def speak(
    text: str,
    voice: str = "pt-BR-AntonioNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    background_tasks: BackgroundTasks
):
    """
    Gera um MP3 com edge-tts CLI e remove o arquivo temporário após enviar.
    Query params:
      - text:  texto a ser falado (obrigatório)
      - voice: voz neural (ex: pt-BR-AntonioNeural)
      - rate:  velocidade (ex: +20%, -10%)
      - pitch: tom em Hz (ex: +100Hz, -50Hz)
    """
    if not text:
        raise HTTPException(status_code=400, detail="O parâmetro 'text' é obrigatório.")

    # Gera nome único para o arquivo temporário
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

    # Executa o edge-tts
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        detail = e.stderr.decode(errors="ignore")
        raise HTTPException(status_code=500, detail=f"Erro edge-tts: {detail}")

    # Verifica se o arquivo foi gerado
    if not os.path.isfile(tmp_filename):
        raise HTTPException(status_code=500, detail="Não foi possível gerar o áudio.")

    # Agenda a remoção do MP3 assim que responder
    background_tasks.add_task(os.remove, tmp_filename)

    # Retorna o MP3 ao cliente
    return FileResponse(
        path=tmp_filename,
        media_type="audio/mpeg",
        filename="voz.mp3",
        headers={"Content-Disposition": 'inline; filename="voz.mp3"'}
    )

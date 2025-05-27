import uuid
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os

app = FastAPI()

@app.get("/speak")
async def speak(text: str, voice: str = "pt-BR-AntonioNeural"):
    if not text:
        raise HTTPException(status_code=400, detail="O parâmetro 'text' é obrigatório.")

    # Cria um nome único pra não ter conflito
    tmp_filename = f"/tmp/voice-{uuid.uuid4()}.mp3"

    # Monta o comando da CLI do edge-tts
    cmd = [
        "edge-tts",
        "--voice", voice,
        "--text", text,
        "--write-media", tmp_filename
    ]

    # Executa o comando (bloqueante, mas simples)
    try:
        completed = subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        # Se der erro no edge-tts, devolve 500 com a mensagem do stderr
        raise HTTPException(status_code=500, detail=e.stderr.decode())

    # Verifica se o arquivo foi criado
    if not os.path.isfile(tmp_filename):
        raise HTTPException(status_code=500, detail="Não foi possível gerar o áudio.")

    # Responde com o arquivo .mp3
    return FileResponse(
        path=tmp_filename,
        media_type="audio/mpeg",
        filename="voz.mp3",
        headers={"Content-Disposition": "inline; filename=voz.mp3"}
    )

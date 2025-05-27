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

    background_tasks.add_task(os.remove, tmp_filename)

    return FileResponse(
        path=tmp_filename,
        media_type="audio/mpeg",
        filename="voz.mp3",
        headers={"Content-Disposition": 'inline; filename="voz.mp3"'}
    )

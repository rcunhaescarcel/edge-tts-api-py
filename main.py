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
    rate: str = "+0%",    # aceita 5, +5, 5%, -5, -5%
    pitch: str = "+0Hz"   # aceita 100, +100, 100Hz, -50, -50Hz
):
    if not text:
        raise HTTPException(400, "O parâmetro 'text' é obrigatório.")

    # 1) Normaliza rate → [+|-]<número>%
    r = rate.strip().rstrip("%").strip()
    if not r.startswith(("+", "-")):
        r = "+" + r
    rate_sanitized = r + "%"

    # 2) Normaliza pitch → [+|-]<número>Hz
    p = pitch.strip().rstrip("Hz").strip()
    if not p.startswith(("+", "-")):
        p = "+" + p
    pitch_sanitized = p + "Hz"

    # 3) Arquivo temporário
    tmp_filename = f"/tmp/voice-{uuid.uuid4()}.mp3"

    # 4) Monta comando: para negativos, usamos --rate=-5% (num único argumento)
    cmd = [
        "edge-tts",
        f"--voice={voice}",
        f"--text={text}",
        f"--rate={rate_sanitized}",
        f"--pitch={pitch_sanitized}",
        f"--write-media={tmp_filename}"
    ]

    # 5) Executa
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        detail = e.stderr.decode(errors="ignore")
        raise HTTPException(500, f"Erro edge-tts: {detail}")

    # 6) Verifica
    if not os.path.isfile(tmp_filename):
        raise HTTPException(500, "Não foi possível gerar o áudio.")

    # 7) Agenda remoção
    background_tasks.add_task(os.remove, tmp_filename)

    # 8) Retorna MP3
    return FileResponse(
        path=tmp_filename,
        media_type="audio/mpeg",
        filename="voz.mp3",
        headers={"Content-Disposition": 'inline; filename="voz.mp3"'}
    )

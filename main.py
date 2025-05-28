import uuid
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import edge_tts

app = FastAPI()

@app.get("/speak")
async def speak(
    text: str,
    background_tasks: BackgroundTasks,
    voice: str = "pt-BR-AntonioNeural",
    rate: str = "+0%",
    pitch: str = "+0Hz",
    # este parâmetro agora só controla diretamente o formato saído
    output_format: str = "audio-16khz-128kbitrate-mono-mp3"
):
    if not text:
        raise HTTPException(400, "O parâmetro 'text' é obrigatório.")

    # 1) normaliza rate → [+|-]número%
    r = rate.strip().rstrip("%").strip()
    if not r.startswith(("+", "-")):
        r = "+" + r
    rate_sanitized = r + "%"

    # 2) normaliza pitch → [+|-]númeroHz
    p = pitch.strip().rstrip("Hz").strip()
    if not p.startswith(("+", "-")):
        p = "+" + p
    pitch_sanitized = p + "Hz"

    # 3) arquivo temporário
    tmp = f"/tmp/voice-{uuid.uuid4()}.mp3"

    # 4) configura o Communicate para gerar MP3 direto
    communicator = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate_sanitized,
        pitch=pitch_sanitized,
        format=output_format
    )

    # 5) roda e salva
    try:
        await communicator.save(tmp)
    except Exception as e:
        # se falhar, devolve o stderr ou mensagem de erro da lib
        raise HTTPException(500, f"Erro edge-tts: {e}")

    if not os.path.isfile(tmp):
        raise HTTPException(500, "Não foi possível gerar o áudio.")

    # 6) agenda remoção do arquivo
    background_tasks.add_task(os.remove, tmp)

    # 7) retorna ao cliente
    return FileResponse(
        path=tmp,
        media_type="audio/mpeg",
        filename="voz.mp3",
        headers={"Content-Disposition": 'inline; filename="voz.mp3"'}
    )

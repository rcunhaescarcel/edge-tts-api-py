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
    rate: str  = "+0%",
    pitch: str = "+0Hz"
):
    """
    → /speak?text=Olá&voice=pt-BR-AntonioNeural&rate=-10%&pitch=+20Hz
    """
    if not text:
        raise HTTPException(400, "O parâmetro 'text' é obrigatório.")

    # 1) Sanitiza rate: assegura [+|-]número%
    r = rate.strip().rstrip("%").strip()
    if not r.startswith(("+", "-")):
        r = "+" + r
    rate_sanitized = r + "%"

    # 2) Sanitiza pitch: assegura [+|-]númeroHz
    p = pitch.strip().rstrip("Hz").strip()
    if not p.startswith(("+", "-")):
        p = "+" + p
    pitch_sanitized = p + "Hz"

    # 3) Caminho temporário para o MP3
    tmp_file = f"/tmp/voice-{uuid.uuid4()}.mp3"

    # 4) Gera o MP3 diretamente pela lib edge-tts (sem CLI, sem FFmpeg)
    try:
        # text, voice são posicionais; rate e pitch são keywords
        communicate = edge_tts.Communicate(
            text,
            voice,
            rate=rate_sanitized,
            pitch=pitch_sanitized
        )
        # salva direto no tmp_file em MP3
        await communicate.save(tmp_file)
    except Exception as e:
        # devolve mensagem de erro vinda da lib
        raise HTTPException(500, f"Erro edge-tts: {e}")

    # 5) Confere se o arquivo foi gerado
    if not os.path.isfile(tmp_file):
        raise HTTPException(500, "Não foi possível gerar o áudio.")

    # 6) Agenda remoção do temp file depois do envio
    background_tasks.add_task(os.remove, tmp_file)

    # 7) Retorna o MP3 ao cliente
    return FileResponse(
        path=tmp_file,
        media_type="audio/mpeg",
        filename="voz.mp3",
        headers={"Content-Disposition": 'inline; filename="voz.mp3"'}
    )

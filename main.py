from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import edge_tts
import asyncio

app = FastAPI()

@app.get("/speak")
async def speak(text: str, voice: str = "pt-BR-AntonioNeural"):
    if not text:
        raise HTTPException(status_code=400, detail="Texto vazio.")

    try:
        communicate = edge_tts.Communicate(text=text, voice=voice)
        gen = communicate.stream()
        # Junta o áudio em memória
        audio_bytes = b"".join([await chunk.async_read() async for chunk in gen])

        return StreamingResponse(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": 'inline; filename="voz.mp3"'
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

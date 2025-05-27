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
        communicate = edge_tts.Communicate(text, voice)  # ⚠️ argumentos posicionais
        audio_bytes = b""

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]

        return StreamingResponse(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": 'inline; filename="voz.mp3"'
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

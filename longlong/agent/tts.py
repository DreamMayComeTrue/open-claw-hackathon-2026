"""
TTS — Streaming Edge TTS
Splits response into sentences and speaks each one immediately.
龙龙 starts talking before finishing the full response — like a real conversation.
"""

import io
import asyncio
import re
import threading
import pygame
from utils.display import print_status

VOICE_ZH = "zh-CN-XiaoxiaoNeural"
VOICE_EN = "en-US-AriaNeural"

# Split on sentence endings — speaks each chunk as soon as it's ready
SENTENCE_SPLIT = re.compile(r'(?<=[。！？.!?])\s*')


class ElevenLabsTTS:
    def __init__(self):
        self._lock = threading.Lock()
        try:
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=256)
            print_status("pygame mixer ready ✅", "green")
        except Exception as e:
            print_status(f"pygame init failed: {e}", "yellow")

    def _detect_voice(self, text: str) -> str:
        cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        return VOICE_ZH if cjk > len(text) * 0.2 else VOICE_EN

    def speak_sync(self, text: str):
        """
        Stream TTS sentence by sentence.
        First sentence plays in ~300ms — feels like instant response.
        """
        with self._lock:
            sentences = [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]
            if not sentences:
                return

            voice = self._detect_voice(text)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._stream_sentences(sentences, voice))
            finally:
                loop.close()

    async def _stream_sentences(self, sentences: list, voice: str):
        """Fetch and play each sentence in order — overlaps fetch+play."""
        import edge_tts

        for i, sentence in enumerate(sentences):
            if not sentence:
                continue
            try:
                communicate = edge_tts.Communicate(sentence, voice, rate="+15%")
                audio_buf = b""
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_buf += chunk["data"]

                if audio_buf:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self._play_mp3, audio_buf
                    )
            except Exception as e:
                print_status(f"TTS chunk failed: {e}", "yellow")
                if i == 0:
                    self._pyttsx3_play(sentence)

    def _play_mp3(self, mp3_bytes: bytes):
        try:
            sound = pygame.mixer.Sound(io.BytesIO(mp3_bytes))
            channel = sound.play()
            while channel and channel.get_busy():
                pygame.time.wait(10)
        except Exception as e:
            print_status(f"pygame play failed: {e}", "yellow")

    async def speak(self, text: str):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.speak_sync, text)

    def _pyttsx3_play(self, text: str):
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 175)
            engine.setProperty("volume", 0.9)
            for v in engine.getProperty("voices"):
                if any(x in v.name.lower() for x in ["chinese", "huihui", "kangkang"]):
                    engine.setProperty("voice", v.id)
                    break
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print_status(f"pyttsx3 failed: {e}", "red")

    def play_activation_sound(self):
        try:
            import numpy as np, math
            rate = 22050
            t = np.linspace(0, 0.12, int(rate * 0.12), False)
            wave = (np.sin(2 * math.pi * 880 * t) * 0.3 * 32767).astype(np.int16)
            stereo = np.column_stack([wave, wave])
            sound = pygame.sndarray.make_sound(stereo)
            sound.play()
            pygame.time.wait(130)
        except Exception:
            pass

    def __del__(self):
        try:
            pygame.mixer.quit()
        except Exception:
            pass
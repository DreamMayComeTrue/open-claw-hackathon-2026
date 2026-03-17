"""
TTS — Edge TTS with pygame playback (fast, clean audio)
Auto-detects Chinese vs English and picks the right neural voice.
"""

import io
import asyncio
import tempfile
import os
import threading
from utils.display import print_status

VOICE_ZH = "zh-CN-XiaoxiaoNeural"
VOICE_EN = "en-US-AriaNeural"


class ElevenLabsTTS:
    def __init__(self):
        self._lock = threading.Lock()
        # Pre-init pygame mixer once at startup for speed
        try:
            import pygame
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)
            self._pygame_ready = True
            print_status("pygame mixer ready ✅", "green")
        except Exception as e:
            print_status(f"pygame init failed: {e}", "yellow")
            self._pygame_ready = False

    def speak_sync(self, text: str):
        with self._lock:
            cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
            voice = VOICE_ZH if cjk > len(text) * 0.2 else VOICE_EN
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._edge_speak(text, voice))
            finally:
                loop.close()

    async def speak(self, text: str):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.speak_sync, text)

    async def _edge_speak(self, text: str, voice: str):
        try:
            import edge_tts

            print_status(f"TTS → {voice}", "blue")

            # Stream directly into buffer — no disk write needed
            communicate = edge_tts.Communicate(text, voice, rate="+10%")
            audio_buffer = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer += chunk["data"]

            if not audio_buffer:
                raise Exception("Empty audio")

            self._play_mp3_bytes(audio_buffer)
            print_status("TTS ✅", "green")

        except Exception as e:
            print_status(f"Edge TTS failed ({e}) — using pyttsx3", "yellow")
            self._pyttsx3_play(text)

    def _play_mp3_bytes(self, mp3_bytes: bytes):
        """Play MP3 bytes via pygame — fastest path, no temp file."""
        try:
            import pygame
            sound = pygame.mixer.Sound(io.BytesIO(mp3_bytes))
            channel = sound.play()
            while channel.get_busy():
                pygame.time.wait(10)
        except Exception as e:
            print_status(f"pygame Sound failed ({e}) — trying file method", "yellow")
            # Fallback: save to temp file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(mp3_bytes)
                tmp = f.name
            try:
                import pygame
                pygame.mixer.music.load(tmp)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            finally:
                os.unlink(tmp)

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
        """Quick beep using pygame."""
        try:
            import pygame
            import numpy as np, math
            rate = 22050
            t = np.linspace(0, 0.12, int(rate * 0.12), False)
            wave = (np.sin(2 * math.pi * 880 * t) * 0.3 * 32767).astype(np.int16)
            stereo = np.column_stack([wave, wave])
            sound = pygame.sndarray.make_sound(stereo)
            sound.play()
            pygame.time.wait(150)
        except Exception:
            pass

    def __del__(self):
        try:
            import pygame
            pygame.mixer.quit()
        except Exception:
            pass
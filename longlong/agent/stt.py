"""
STT — Deepgram primary, Google free fallback
Faster silence detection for snappy responses.
"""

import pyaudio
import numpy as np
import wave
import io
from config import DEEPGRAM_API_KEY
from utils.display import print_status

RATE = 16000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK = 1024
SILENCE_THRESHOLD = 350     # lower = picks up quieter speech
SILENCE_DURATION = 0.8      # reduced from 1.5s → 0.8s — feels much snappier
MAX_RECORD_SECONDS = 10     # reduced from 15s


class DeepgramSTT:
    def __init__(self):
        self.api_key = DEEPGRAM_API_KEY

    def record_and_transcribe(self) -> str:
        audio_bytes = self._record_until_silence()
        if not audio_bytes:
            return ""
        wav_bytes = self._to_wav(audio_bytes)
        transcript = self._try_deepgram(wav_bytes)
        if transcript:
            return transcript
        print_status("Deepgram empty — trying Google STT", "yellow")
        return self._try_google(wav_bytes)

    def _record_until_silence(self) -> bytes:
        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=RATE, channels=CHANNELS,
            format=FORMAT, input=True,
            frames_per_buffer=CHUNK,
        )
        frames = []
        silent_chunks = 0
        silence_limit = int(RATE / CHUNK * SILENCE_DURATION)
        max_chunks = int(RATE / CHUNK * MAX_RECORD_SECONDS)
        has_speech = False

        print_status("Recording...", "cyan")
        for _ in range(max_chunks):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            rms = np.sqrt(np.mean(
                np.frombuffer(data, dtype=np.int16).astype(np.float32) ** 2
            ))
            if rms > SILENCE_THRESHOLD:
                has_speech = True
                silent_chunks = 0
            elif has_speech:
                silent_chunks += 1
                if silent_chunks >= silence_limit:
                    break

        stream.stop_stream()
        stream.close()
        pa.terminate()
        return b"".join(frames)

    def _to_wav(self, pcm_bytes: bytes) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(pcm_bytes)
        return buf.getvalue()

    def _try_deepgram(self, wav_bytes: bytes) -> str:
        try:
            import requests
            resp = requests.post(
                "https://api.deepgram.com/v1/listen",
                params={
                    "model": "nova-2",
                    "language": "en",
                    "punctuate": "true",
                    "smart_format": "true",
                },
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": "audio/wav",
                },
                data=wav_bytes,
                timeout=8,
            )
            resp.raise_for_status()
            transcript = resp.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
            if transcript.strip():
                print_status(f"Deepgram: {transcript}", "blue")
                return transcript
        except Exception as e:
            print_status(f"Deepgram error: {e}", "yellow")
        return ""

    def _try_google(self, wav_bytes: bytes) -> str:
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
                audio = recognizer.record(source)
            for lang in ["zh-CN", "en-US"]:
                try:
                    text = recognizer.recognize_google(audio, language=lang)
                    if text.strip():
                        print_status(f"Google STT ({lang}): {text}", "blue")
                        return text
                except sr.UnknownValueError:
                    continue
        except Exception as e:
            print_status(f"Google STT error: {e}", "red")
        return ""
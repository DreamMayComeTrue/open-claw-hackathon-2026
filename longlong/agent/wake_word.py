"""
Wake Word Detection — 小龙小龙
- Uses VAD (voice activity detection) instead of fixed time window
- Waits until you finish speaking before processing
- Persistent listening mode until 拜拜小龙
"""

import pyaudio
import numpy as np
import threading
import time
import io
import wave
from utils.display import print_status

WAKE_PHRASES = [
    "小龙小龙", "xiao long xiao long", "小龙", "long long", "龙龙",
]

GOODBYE_PHRASES = [
    "拜拜小龙", "拜拜龙龙", "拜拜", "bye bye long", "goodbye long",
    "bye long", "再见小龙", "再见龙龙", "再见",
]

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
ENERGY_THRESHOLD = 400      # tuned for your mic
SILENCE_DURATION = 0.8      # seconds of silence = end of speech
PRE_SPEECH_WINDOW = 0.3     # seconds to keep before speech starts
MAX_DURATION = 8.0          # max seconds to record


class WakeWordDetector:
    def __init__(self, wake_phrase: str, command_queue):
        self.wake_phrase = wake_phrase
        self.command_queue = command_queue
        self._running = False
        self._active_mode = False

    def start(self, stt, brain, tts, is_listening: threading.Event):
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = ENERGY_THRESHOLD
        recognizer.dynamic_energy_threshold = False  # fixed threshold, no drift

        pa = pyaudio.PyAudio()
        self._running = True
        print_status("Listening for '小龙小龙'...", "blue")

        while self._running:
            if is_listening.is_set():
                time.sleep(0.05)
                continue

            try:
                # Record using VAD — waits for full utterance
                audio_bytes = self._record_vad(pa)
                if not audio_bytes:
                    continue

                wav_bytes = self._to_wav(audio_bytes)

                # Recognise
                with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
                    audio = recognizer.record(source)

                text = ""
                for lang in ["zh-CN", "en-US"]:
                    try:
                        result = recognizer.recognize_google(audio, language=lang)
                        if result.strip():
                            text = result.lower()
                            break
                    except sr.UnknownValueError:
                        continue
                    except Exception:
                        continue

                if not text:
                    continue

                print_status(f"Heard: '{text}'", "blue")

                # Goodbye — exit active mode
                if self._active_mode and any(p in text for p in GOODBYE_PHRASES):
                    self._active_mode = False
                    is_listening.set()
                    cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
                    farewell = "再见！有需要再叫我哦 👋" if cjk > 0 else "Goodbye! Call me anytime 👋"
                    print_status(f"龙龙: {farewell}", "green")
                    tts.speak_sync(farewell)
                    is_listening.clear()
                    print_status("Sleeping... say '小龙小龙' to wake me", "blue")
                    continue

                # Wake word — enter active mode
                if not self._active_mode and any(p in text for p in WAKE_PHRASES):
                    self._active_mode = True
                    is_listening.set()
                    cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
                    greeting = "嘿，我在！" if cjk > 0 else "Hey, I'm here!"
                    print_status(f"🎙️  Wake word detected! → '{greeting}'", "cyan")
                    tts.speak_sync(greeting)
                    is_listening.clear()
                    print_status("Active — say your command...", "cyan")
                    continue

                # Active mode — process as command
                if self._active_mode and not is_listening.is_set():
                    if any(p in text for p in WAKE_PHRASES):
                        continue
                    is_listening.set()
                    self._handle_command(text, brain, tts, is_listening)

            except Exception as e:
                print_status(f"Wake loop error: {e}", "red")
                time.sleep(0.2)

        pa.terminate()

    def _record_vad(self, pa) -> bytes:
        """
        Record using Voice Activity Detection.
        Starts capturing when you speak, stops when you go silent.
        Returns raw PCM bytes of the full utterance.
        """
        stream = pa.open(
            rate=RATE, channels=CHANNELS,
            format=FORMAT, input=True,
            frames_per_buffer=CHUNK,
        )

        frames = []
        pre_buffer = []     # rolling buffer before speech starts
        pre_buf_size = int(RATE / CHUNK * PRE_SPEECH_WINDOW)
        silent_chunks = 0
        silence_limit = int(RATE / CHUNK * SILENCE_DURATION)
        max_chunks = int(RATE / CHUNK * MAX_DURATION)
        speech_started = False
        total_chunks = 0

        while total_chunks < max_chunks:
            data = stream.read(CHUNK, exception_on_overflow=False)
            total_chunks += 1

            rms = np.sqrt(np.mean(
                np.frombuffer(data, dtype=np.int16).astype(np.float32) ** 2
            ))

            if not speech_started:
                # Keep a rolling pre-speech buffer
                pre_buffer.append(data)
                if len(pre_buffer) > pre_buf_size:
                    pre_buffer.pop(0)

                if rms > ENERGY_THRESHOLD:
                    # Speech started — include pre-buffer for natural start
                    speech_started = True
                    frames.extend(pre_buffer)
                    frames.append(data)
                    silent_chunks = 0
            else:
                frames.append(data)
                if rms < ENERGY_THRESHOLD:
                    silent_chunks += 1
                    if silent_chunks >= silence_limit:
                        break   # silence after speech = end of utterance
                else:
                    silent_chunks = 0

        stream.stop_stream()
        stream.close()

        if not speech_started or len(frames) < 3:
            return b""

        return b"".join(frames)

    def _to_wav(self, pcm_bytes: bytes) -> bytes:
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(pcm_bytes)
        return buf.getvalue()

    def _handle_command(self, transcript: str, brain, tts, is_listening: threading.Event):
        import asyncio
        try:
            tts.play_activation_sound()
            print_status(f"You said: {transcript}", "white")

            loop = asyncio.new_event_loop()
            response = loop.run_until_complete(brain.process(transcript))
            loop.close()

            print_status(f"龙龙: {response}", "green")
            tts.speak_sync(response)

        except Exception as e:
            print_status(f"Command error: {e}", "red")
            tts.speak_sync("抱歉出错了 / Sorry, something went wrong.")
        finally:
            is_listening.clear()
            if self._active_mode:
                print_status("Active — say your next command...", "cyan")

    def stop(self):
        self._running = False
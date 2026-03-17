"""
Mic Debug — shows your real RMS levels so we can tune the threshold
python debug_mic.py
Speak normally and watch the numbers — note the range when talking vs silent
"""

import pyaudio
import numpy as np
import time

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

pa = pyaudio.PyAudio()

print("\n🎙️  Mic Level Monitor")
print("=" * 50)
print("Stay SILENT for 3 seconds first...")
print("Then speak NORMALLY and watch the levels")
print("Press Ctrl+C to stop\n")

stream = pa.open(
    rate=RATE, channels=CHANNELS,
    format=FORMAT, input=True,
    frames_per_buffer=CHUNK,
)

silent_levels = []
collecting_silent = True
start = time.time()

try:
    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        rms = int(np.sqrt(np.mean(
            np.frombuffer(data, dtype=np.int16).astype(np.float32) ** 2
        )))

        # Visual bar
        bar_len = min(50, rms // 20)
        bar = "█" * bar_len
        tag = ""

        elapsed = time.time() - start
        if elapsed < 3:
            silent_levels.append(rms)
            tag = "← silent"
        elif elapsed == 3 or (elapsed > 3 and not collecting_silent):
            if collecting_silent:
                collecting_silent = False
                avg_silent = int(np.mean(silent_levels)) if silent_levels else 0
                print(f"\n✅ Silent baseline RMS: ~{avg_silent}")
                print(f"   Recommended threshold: {avg_silent * 3} – {avg_silent * 5}")
                print("\nNow SPEAK and check your voice level:\n")
            tag = "← speak now"

        print(f"\rRMS: {rms:5d}  {bar:<50} {tag}    ", end="", flush=True)

except KeyboardInterrupt:
    print("\n\nDone!")

stream.stop_stream()
stream.close()
pa.terminate()

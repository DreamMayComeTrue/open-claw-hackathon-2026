"""
龙龙 - Bilingual Voice AI Agent (Chinese + English)
Hackathon Edition — Windows
"""

import asyncio
import threading
import queue
import sys
from agent.wake_word import WakeWordDetector
from agent.stt import DeepgramSTT
from agent.brain import XiaoBaoBrain
from agent.tts import ElevenLabsTTS
from utils.display import print_banner, print_status


async def main():
    print_banner()

    # Shared state
    gesture_queue = asyncio.Queue()
    is_listening = threading.Event()

    # Init all components
    stt = DeepgramSTT()
    brain = XiaoBaoBrain()
    tts = ElevenLabsTTS()

    # Skip MediaPipe for now — focus on voice
    print_status("Vision/MediaPipe disabled — voice-only mode", "yellow")

    wake_detector = WakeWordDetector(
        wake_phrase="小龙小龙",
        command_queue=None,
    )

    print_status("龙龙 is ready! Say 小龙小龙 to start...", "green")

    # Run wake word loop in background thread
    wake_thread = threading.Thread(
        target=wake_detector.start,
        args=(stt, brain, tts, is_listening),
        daemon=True,
    )
    wake_thread.start()

    # Keep main loop alive, handle clean shutdown
    try:
        while wake_thread.is_alive():
            await asyncio.sleep(0.5)
    except (KeyboardInterrupt, asyncio.CancelledError):
        print_status("\n龙龙 shutting down. 再见! 👋", "yellow")
        sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n龙龙 stopped. 再见! 👋")
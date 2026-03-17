"""
MediaPipe Vision — Hand gesture + face detection
Runs in background thread, puts gesture events into queue
"""

import threading
import queue
import time
from utils.display import print_status


class MediaPipeVision:
    def __init__(self, gesture_queue: queue.Queue):
        self.gesture_queue = gesture_queue
        self._running = False
        self._last_gesture = None
        self._gesture_cooldown = 2.0  # seconds between repeat gestures

    def start(self):
        """Blocking — run in a thread."""
        try:
            import cv2
            import mediapipe as mp

            self._running = True
            mp_hands = mp.solutions.hands
            mp_face = mp.solutions.face_detection
            mp_draw = mp.solutions.drawing_utils

            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print_status("No webcam found — MediaPipe disabled", "yellow")
                return

            print_status("MediaPipe vision active 👁️", "green")

            hands = mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.6,
            )
            face_det = mp_face.FaceDetection(min_detection_confidence=0.6)

            last_gesture_time = 0

            while self._running:
                ret, frame = cap.read()
                if not ret:
                    continue

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                hand_results = hands.process(frame_rgb)

                gesture = None

                if hand_results.multi_hand_landmarks:
                    for hand_lm in hand_results.multi_hand_landmarks:
                        gesture = self._classify_gesture(hand_lm)
                        mp_draw.draw_landmarks(
                            frame, hand_lm, mp_hands.HAND_CONNECTIONS
                        )
                        break

                # Put gesture in queue (with cooldown to avoid spam)
                now = time.time()
                if (
                    gesture
                    and gesture != self._last_gesture
                    and (now - last_gesture_time) > self._gesture_cooldown
                ):
                    self.gesture_queue.put(gesture)
                    self._last_gesture = gesture
                    last_gesture_time = now
                    print_status(f"👋 Gesture: {gesture}", "cyan")

                # Show overlay window (comment out for headless/demo mode)
                cv2.putText(
                    frame,
                    f"Gesture: {gesture or 'none'}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 100),
                    2,
                )
                cv2.imshow("小宝 Vision", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            cap.release()
            cv2.destroyAllWindows()
            hands.close()
            face_det.close()

        except ImportError:
            print_status(
                "mediapipe/opencv not installed — vision disabled\n"
                "Install with: pip install mediapipe opencv-python",
                "yellow",
            )
        except Exception as e:
            print_status(f"Vision error: {e}", "red")

    def _classify_gesture(self, hand_landmarks) -> str | None:
        """
        Classify hand gesture from MediaPipe landmarks.
        Returns gesture name or None.
        """
        import mediapipe as mp
        lm = hand_landmarks.landmark
        mp_hands = mp.solutions.hands

        # Helper: is finger extended?
        def finger_up(tip, pip):
            return lm[tip].y < lm[pip].y

        thumb_up = lm[4].x < lm[3].x  # thumb tip left of knuckle (right hand)
        index_up = finger_up(8, 6)
        middle_up = finger_up(12, 10)
        ring_up = finger_up(16, 14)
        pinky_up = finger_up(20, 18)

        fingers = [index_up, middle_up, ring_up, pinky_up]
        all_up = all(fingers)
        all_down = not any(fingers)

        # Thumbs up: only thumb extended, others curled
        if thumb_up and all_down:
            return "thumbs_up"

        # Thumbs down: thumb extended downward
        if not thumb_up and lm[4].y > lm[3].y and all_down:
            return "thumbs_down"

        # Open palm: all fingers extended
        if all_up:
            return "open_palm"

        # Peace / V sign: index + middle only
        if index_up and middle_up and not ring_up and not pinky_up:
            return "peace"

        # Pointing: only index up
        if index_up and not middle_up and not ring_up and not pinky_up:
            return "pointing"

        return None

    def stop(self):
        self._running = False

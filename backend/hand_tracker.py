# hand_tracker.py
import cv2
import mediapipe as mp
import subprocess
import time
import ctypes
import win32gui
import win32con

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.8)
mp_draw = mp.solutions.drawing_utils

last_trigger_time = 0  # cooldown timer
prev_x = [None]  # for swipe detection

def count_raised_fingers(landmarks):
    finger_tips = [8, 12, 16, 20]
    finger_pips = [6, 10, 14, 18]
    count = 0
    for tip, pip in zip(finger_tips, finger_pips):
        if landmarks[tip][1] < landmarks[pip][1]:
            count += 1
    return count

def launch_whatsapp():
    global last_trigger_time
    current_time = time.time()
    if current_time - last_trigger_time > 5:
        try:
            subprocess.Popen([
                'explorer', 'shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App'
            ], shell=True)
            print("[INFO] WhatsApp launched")
            last_trigger_time = current_time
        except Exception as e:
            print("[ERROR] Launch failed:", e)

def snap_window_right():
    hwnd = win32gui.GetForegroundWindow()
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.MoveWindow(hwnd, screen_width // 2, 0, screen_width // 2, screen_height, True)
    print("[INFO] Snapped window to right")

def snap_window_left():
    hwnd = win32gui.GetForegroundWindow()
    screen_width = ctypes.windll.user32.GetSystemMetrics(0)
    screen_height = ctypes.windll.user32.GetSystemMetrics(1)
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.MoveWindow(hwnd, 0, 0, screen_width // 2, screen_height, True)
    print("[INFO] Snapped window to left")

def get_hand_landmarks(frame):
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    output = []

    if results.multi_hand_landmarks and results.multi_handedness:
        for i, (hand_landmarks, handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):
            label = handedness.classification[0].label
            landmarks = []
            for lm in hand_landmarks.landmark:
                landmarks.append([lm.x, lm.y, lm.z])

            raised = count_raised_fingers(landmarks)
            gesture_label = f"{raised} fingers"

            if raised == 2:
                gesture_label = "Open WhatsApp"
                launch_whatsapp()

            if raised == 4:
                x_pos = landmarks[8][0]

                if prev_x[0] is not None:
                    delta = x_pos - prev_x[0]
                    print(f"[DEBUG] 4-Finger Swipe: x_prev={prev_x[0]:.3f}, x_now={x_pos:.3f}, delta={delta:.3f}")

                    if delta > 0.15:
                        gesture_label = "Swipe 4 → Snap Right"
                        print("[INFO] Swipe right detected → snapping window right")
                        snap_window_right()
                    elif delta < -0.15:
                        gesture_label = "Swipe 4 ← Snap Left"
                        print("[INFO] Swipe left detected → snapping window left")
                        snap_window_left()
                    else:
                        print("[INFO] Swipe movement too small")
                else:
                    print("[DEBUG] Starting swipe tracking...")

                prev_x[0] = x_pos
            else:
                prev_x[0] = None

            output.append({
                "hand": label,
                "gesture": gesture_label,
                "landmarks": landmarks
            })

    return output

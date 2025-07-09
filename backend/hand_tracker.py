# hand_tracker.py
import cv2
import mediapipe as mp
import subprocess
import time
import ctypes
import win32gui
import win32con
import math

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.8)
mp_draw = mp.solutions.drawing_utils

last_trigger_time = 0  # cooldown timer
prev_x = [None]  # for horizontal swipe detection
prev_y = [None]  # for vertical swipe detection
pinching = False  # To track pinch state

def is_pinching(landmarks):
    thumb_tip = landmarks[4]
    index_tip = landmarks[8]
    middle_tip = landmarks[12]
    ring_tip = landmarks[16]
    pinky_tip = landmarks[20]

    # Calculate distance between thumb and other fingertips
    index_dist = math.sqrt((thumb_tip[0] - index_tip[0])**2 + (thumb_tip[1] - index_tip[1])**2)
    middle_dist = math.sqrt((thumb_tip[0] - middle_tip[0])**2 + (thumb_tip[1] - middle_tip[1])**2)
    ring_dist = math.sqrt((thumb_tip[0] - ring_tip[0])**2 + (thumb_tip[1] - ring_tip[1])**2)
    pinky_dist = math.sqrt((thumb_tip[0] - pinky_tip[0])**2 + (thumb_tip[1] - pinky_tip[1])**2)

    # Check if only index and thumb are pinching
    return index_dist < 0.05 and middle_dist > 0.1 and ring_dist > 0.1 and pinky_dist > 0.1

def is_thumb_closed(landmarks):
    thumb_tip = landmarks[4]
    index_finger_base = landmarks[5]
    distance = math.sqrt((thumb_tip[0] - index_finger_base[0])**2 + (thumb_tip[1] - index_finger_base[1])**2)
    return distance < 0.1 # Thumb closed threshold

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
                'explorer', 'shell:AppsFolder\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App'
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

def minimize_window():
    hwnd = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
    print("[INFO] Window minimized")

def maximize_window():
    hwnd = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
    print("[INFO] Window maximized")

def get_hand_landmarks(frame):
    global pinching
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

            pinch_status = "Not Pinching"
            if is_pinching(landmarks):
                if not pinching:
                    minimize_window()
                    pinching = True
                pinch_status = "Pinching"
            else:
                if pinching:
                    maximize_window()
                    pinching = False
                pinch_status = "Not Pinching"
            
            thumb_status = "Thumb Open"
            if is_thumb_closed(landmarks):
                thumb_status = "Thumb Closed"


            if raised == 2:
                gesture_label = "Open WhatsApp"
                launch_whatsapp()

            if raised == 1:
                x_pos = landmarks[8][0]  # for left/right
                y_pos = landmarks[8][1]  # for up/down

                if prev_x[0] is not None and prev_y[0] is not None:
                    delta_x = x_pos - prev_x[0]
                    delta_y = y_pos - prev_y[0]

                    print(f"[DEBUG] Swipe: x_prev={prev_x[0]:.3f}, x_now={x_pos:.3f}, delta_x={delta_x:.3f}, y_prev={prev_y[0]:.3f}, y_now={y_pos:.3f}, delta_y={delta_y:.3f}")

                    if delta_x > 0.15:
                        gesture_label = "Swipe 1 → Snap Right"
                        print("[INFO] Swipe right detected → snapping window right")
                        snap_window_right()
                    elif delta_x < -0.15:
                        gesture_label = "Swipe 1 ← Snap Left"
                        print("[INFO] Swipe left detected → snapping window left")
                        snap_window_left()
                    elif delta_y > 0.15:
                        gesture_label = "Swipe 1 ↓ Minimize"
                        print("[INFO] Swipe down detected → minimizing window")
                        minimize_window()
                    elif delta_y < -0.15:
                        gesture_label = "Swipe 1 ↑ Maximize"
                        print("[INFO] Swipe up detected → maximizing window")
                        maximize_window()
                    else:
                        print("[INFO] Swipe movement too small")
                else:
                    print("[DEBUG] Starting swipe tracking...")

                prev_x[0] = x_pos
                prev_y[0] = y_pos
            else:
                prev_x[0] = None
                prev_y[0] = None

            output.append({
                "hand": label,
                "gesture": gesture_label,
                "pinch_status": pinch_status,
                "thumb_status": thumb_status,
                "landmarks": landmarks
            })

    return output


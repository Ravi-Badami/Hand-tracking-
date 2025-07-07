import cv2
import mediapipe as mp
import subprocess
import time

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.8)
mp_draw = mp.solutions.drawing_utils

last_trigger_time = 0  # cooldown timer

def count_raised_fingers(landmarks):
    finger_tips = [8, 12, 16, 20]
    finger_pips = [6, 10, 14, 18]

    count = 0
    for tip, pip in zip(finger_tips, finger_pips):
        if landmarks[tip][1] < landmarks[pip][1]:  # tip is above pip
            count += 1
    return count

def launch_whatsapp():
    global last_trigger_time
    current_time = time.time()

    if current_time - last_trigger_time > 5:  # cooldown of 5 seconds
        try:
            subprocess.Popen(
                ['explorer', 'shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App'],
                shell=True
            )
            print("[INFO] WhatsApp launched via shell")
            last_trigger_time = current_time
        except Exception as e:
            print("[ERROR] Failed to launch WhatsApp:", e)

def get_hand_landmarks(frame):
    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)
    output = []

    if results.multi_hand_landmarks and results.multi_handedness:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            label = handedness.classification[0].label  # "Left" or "Right"
            landmarks = []

            for lm in hand_landmarks.landmark:
                landmarks.append([lm.x, lm.y, lm.z])

            raised = count_raised_fingers(landmarks)
            gesture_label = f"{raised} fingers"

            if raised == 2:
                gesture_label = "Open WhatsApp"
                launch_whatsapp()

            output.append({
                "hand": label,
                "gesture": gesture_label,
                "landmarks": landmarks
            })

    return output

from flask import Flask, jsonify, Response
import cv2
import threading
from hand_tracker import get_hand_landmarks, hands, mp_draw, mp_hands

app = Flask(__name__)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
latest_frame = None

def capture_frames():
    global latest_frame
    while True:
        ret, frame = cap.read()
        if ret:
            latest_frame = cv2.flip(frame, 1)

threading.Thread(target=capture_frames, daemon=True).start()

@app.route('/landmarks')
def stream_landmarks():
    if latest_frame is None:
        return jsonify([])
    data = get_hand_landmarks(latest_frame)
    return jsonify(data)

@app.route('/video')
def video_feed():
    def generate():
        while True:
            if latest_frame is not None:
                frame = latest_frame.copy()
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(img_rgb)
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

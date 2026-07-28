import matplotlib.pyplot as plt
from sports.tennis.ball_tracking.tracker import Tracker
import cv2 as cv

tracker = Tracker()

y_pos = []
x = []

frame_sequence = []
cap = cv.VideoCapture("test_videos/video4.mp4")

n_preds = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv.resize(frame, (640, 360))
    frame_sequence.append(frame)

    if len(frame_sequence) >= 3:
        frame_sequence = frame_sequence[-3:]

        tracker.track(frame_sequence)

        coords = tracker.tracking_history[-1]

        if coords != (-1, -1):
            cx, cy = coords
            y_pos.append(cy)
            x.append(n_preds)
            n_preds += 1

cap.release()

print(f"detections: {len(y_pos)}")

plt.figure(figsize=(10, 5))
plt.plot(x, y_pos, marker="o", markersize=2)
plt.title("graph of ball y position over time")
plt.xlabel("n ball detections")
plt.ylabel("ball y coordinate (pixels)")
plt.grid(True)
plt.show()
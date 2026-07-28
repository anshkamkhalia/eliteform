# dataset creator for fine-tuning tracknet

# steps:
# load video
# read frame
# run yolo tracker
# if no detection: run TrackNet (coreml) on the frame to get a suggested
#   ball center, pre-fill it in the review UI so you can just verify
#   (space), correct (click then space), or skip (s)
# save frames and object center (they need to match positions)
# save on .npy file per video (video_n.npy, centers_n.npy)

import cv2 as cv
import os
from ultralytics import YOLO
import numpy as np
import coremltools as ct

VIDEO_DATA_PATH = "sports/tennis/ball_tracking/tracknet/tracknet_videos"
OUTPUT_DATA_PATH = "sports/tennis/ball_tracking/tracknet/dataset"
os.makedirs(OUTPUT_DATA_PATH, exist_ok=True)
# videos = os.listdir(VIDEO_DATA_PATH)
videos = ["video2.mp4", "video3.mp4", "video4.mp4"]

tracker = YOLO("sports/tennis/models/tracker.pt")

DISPLAY_WIDTH = 1600
DISPLAY_HEIGHT = 900

TRACKNET_MODEL_PATH = "sports/tennis/models/TrackNetFTV1.mlpackage"
TRACKNET_WIDTH = 640
TRACKNET_HEIGHT = 360
TRACKNET_INPUT_NAME = "video_frames"

tracknet_model = ct.models.MLModel(TRACKNET_MODEL_PATH)

def build_tracknet_input(frame_curr, frame_prev, frame_preprev):
    x = np.concatenate((frame_curr, frame_prev, frame_preprev), axis=2)
    x = np.transpose(x, (2, 0, 1))
    x = np.ascontiguousarray(x, dtype=np.float32) / 255.0
    return np.expand_dims(x, axis=0)

def decode_tracknet_output(probs):
    heatmap = np.argmax(probs[0], axis=0).astype(np.uint8)
    heatmap = heatmap.reshape(TRACKNET_HEIGHT, TRACKNET_WIDTH)
    ys, xs = np.nonzero(heatmap > 127)
    if len(xs) == 0:
        return None
    weights = heatmap[ys, xs].astype(np.float32)
    cx = float(np.average(xs, weights=weights))
    cy = float(np.average(ys, weights=weights))
    return cx, cy

def run_tracknet(frame_curr, frame_prev, frame_preprev):
    x = build_tracknet_input(frame_curr, frame_prev, frame_preprev)
    prediction = tracknet_model.predict({TRACKNET_INPUT_NAME: x})
    output_name = list(prediction.keys())[0]
    probs = prediction[output_name]
    pred = decode_tracknet_output(probs)
    if pred is None:
        return None
    return pred

clicked_point = {"pt": None}

def click_center(event, x, y, flags, param):
    if event == cv.EVENT_LBUTTONDOWN:
        try:
            scale = param
            clicked_point["pt"] = (int(x / scale), int(y / scale))
        except Exception as e:
            print(f"[click_center] EXCEPTION: {e}")  # DEBUG

WINDOW_NAME = "review frame"
cv.namedWindow(WINDOW_NAME, cv.WINDOW_NORMAL)
cv.resizeWindow(WINDOW_NAME, DISPLAY_WIDTH, DISPLAY_HEIGHT)

def process_video(video_path, video_n):

    # data collection
    X_frames = []
    y_centers = []

    review_frame = False

    frame_history = []

    cap = cv.VideoCapture(os.path.join(VIDEO_DATA_PATH, video_path)) # read video
    while True:
        ret, frame = cap.read()
        if not ret: break

        frame_history.append(frame)
        if len(frame_history) > 3:
            frame_history.pop(0)

        results = tracker.predict(
            source=frame,
            stream=False,
            verbose=False,
        )[0].boxes

        if len(results) != 1:
            review_frame = True

        else:
            x1, y1, x2, y2 = results.xyxy[0]
            cx, cy = int((x1+x2)//2), int((y1+y2)//2)
            y_centers.append(np.array([cx, cy], dtype=np.int16))
            X_frames.append(frame)

        cv.waitKey(1)

        if review_frame:
            suggestion = None
            if len(frame_history) == 3:
                frame_h, frame_w = frame.shape[:2]
                frame_preprev, frame_prev, frame_curr = frame_history

                tn_curr = cv.resize(frame_curr, (TRACKNET_WIDTH, TRACKNET_HEIGHT))
                tn_prev = cv.resize(frame_prev, (TRACKNET_WIDTH, TRACKNET_HEIGHT))
                tn_preprev = cv.resize(frame_preprev, (TRACKNET_WIDTH, TRACKNET_HEIGHT))

                tn_pred = run_tracknet(tn_curr, tn_prev, tn_preprev)

                if tn_pred is not None:

                    sx = frame_w / TRACKNET_WIDTH
                    sy = frame_h / TRACKNET_HEIGHT
                    suggestion = (int(tn_pred[0] * sx), int(tn_pred[1] * sy))

            clicked_point["pt"] = suggestion

            frame_h, frame_w = frame.shape[:2]
            scale = min(DISPLAY_WIDTH / frame_w, DISPLAY_HEIGHT / frame_h)
            disp_w, disp_h = int(frame_w * scale), int(frame_h * scale)

            cv.setMouseCallback(WINDOW_NAME, click_center, scale)

            while True:
                display = cv.resize(frame, (disp_w, disp_h))

                if clicked_point["pt"] is not None:
                    draw_pt = (
                        int(clicked_point["pt"][0] * scale),
                        int(clicked_point["pt"][1] * scale),
                    )
                    cv.circle(display, draw_pt, 8, (0, 0, 255), -1)

                cv.imshow(WINDOW_NAME, display)

                key = cv.waitKey(1)

                # press space to save the clicked point
                if key == 32 and clicked_point["pt"] is not None:
                    X_frames.append(frame)
                    y_centers.append(np.array(clicked_point["pt"], dtype=np.int16))
                    break

                # press s to skip
                elif key == ord("s"):
                    X_frames.append(frame)
                    y_centers.append(np.array([-1, -1], dtype=np.int16))
                    break

        review_frame = False

    # write file
    X_frames = np.array(X_frames)
    y_centers = np.array(y_centers)

    np.save(f"{OUTPUT_DATA_PATH}/video_{video_n}.npy", X_frames)
    np.save(f"{OUTPUT_DATA_PATH}/centers_{video_n}.npy", y_centers)

video_path = f"video3.mp4"
video_n = 3

process_video(video_path=video_path, video_n=video_n)

cv.destroyAllWindows()
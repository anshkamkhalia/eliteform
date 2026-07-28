# new and improved tracknet version

import cv2 as cv
import numpy as np
import coremltools as ct

class Tracker:

    def __init__(self):

        self.model = ct.models.MLModel("sports/tennis/models/TrackNetFTV2.mlpackage") # load coreml model
        self.tracking_history = []

    def build_input(self, frame_list):
        frame_curr, frame_prev, frame_prevprev = frame_list[-1], frame_list[1], frame_list[0]
        x = np.concatenate((frame_curr, frame_prev, frame_prevprev), axis=2)
        x = np.transpose(x, (2,0,1))
        x = np.ascontiguousarray(x, dtype=np.float32) / 255.0
        return np.expand_dims(x, axis=0)

    def decode_prediction(self, probs):
        heatmap = np.argmax(probs[0], axis=0).astype(np.uint8)
        heatmap = heatmap.reshape(360, 640)
        ys, xs = np.nonzero(heatmap > 127)
        if len(xs) == 0:
            return None # no ball detected
        weights = heatmap[ys, xs].astype(np.float32)
        cx = float(np.average(xs, weights=weights))
        cy = float(np.average(ys, weights=weights))
        return cx, cy # ball center

    def track(self, frame_sequence):

        input_data = self.build_input(frame_sequence)
        prediction = self.model.predict({"video_frames": input_data})
        output_name = list(prediction.keys())[0]
        probs = prediction[output_name] # get probabilities
        pred = self.decode_prediction(probs)
        if pred is not None:
            self.tracking_history.append(pred) # (cx, cy)
        else:
            self.tracking_history.append((-1, -1)) # no ball in frame
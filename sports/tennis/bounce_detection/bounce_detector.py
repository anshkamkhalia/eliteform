import numpy as np
import pandas as pd

# TRUE -> increasing
# FALSE -> decreasing

class BounceDetector:

    def __init__(self):
        self.y_vec = [] # stores all y positions
        self.prev_vector_increasing = None

        # this is used to determine the minimum amount of pixel difference to be considered a directional change
        self.min_change = 10 # tweak this value

    def detect_bounces(self, bounce_detection_frames):

        bounce_idxs = []

        # this is ran once at the end after all coordinates are detected
        for i in range(len(self.y_vec)):

            # initial setup
            if self.prev_vector_increasing is None:
                if not self.prev_vector_increasing and i == 0:
                    continue
                else:
                    self.prev_vector_increasing = True if (self.y_vec[i] - self.y_vec[i-1]) >= 0 else False
                    continue

            # get current direction
            self.curr_direction = True if (self.y_vec[i] - self.y_vec[i-1]) >= 0 else False\
            
            if self.curr_direction != self.prev_vector_increasing:

                if abs(self.y_vec[i] - self.y_vec[i-1]) >= self.min_change:

                    self.prev_vector_increasing = self.curr_direction # change direction

                    bounce_idxs.append(i)

                else:

                    self.prev_vector_increasing = self.prev_vector_increasing # keep the same

        bounce_frames = [bounce_detection_frames[i] for i in bounce_idxs]
        return bounce_frames
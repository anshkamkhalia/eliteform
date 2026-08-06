import cv2 as cv
import numpy as np

class CourtDetector:
    def __init__(self):
        pass

    def calculate_angle(self, line):
        x1, y1, x2, y2 = line
        angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
        return angle

    def merge_horizontal_lines(self, lines, threshold=10):
        merged = []

        # group lines that have similar y positions
        groups = []

        for line in lines:
            x1, y1, x2, y2 = tuple(line)
            y = (y1 + y2) / 2

            found = False

            for group in groups:
                group_y = np.mean([g[4] for g in group])

                if abs(y - group_y) < threshold:
                    group.append([x1, y1, x2, y2, y])
                    found = True
                    break

            if not found:
                groups.append([[x1, y1, x2, y2, y]])

        # combine each group into one long line
        for group in groups:
            points = []

            for x1, y1, x2, y2, _ in group:
                points.append((x1, y1))
                points.append((x2, y2))

            xs = [p[0] for p in points]
            ys = [p[1] for p in points]

            merged.append([
                min(xs),
                int(np.mean(ys)),
                max(xs),
                int(np.mean(ys))
            ])

        return merged

    def x_at_y(self, line, y):
        x1, y1, x2, y2 = line

        if y2 == y1:
            return None

        return x1 + (y - y1) * (x2 - x1) / (y2 - y1)

    def merge_slanted_lines(self, lines, threshold=20):
        merged = []

        # group lines that have similar x positions
        groups = []

        ref_y = 300

        for line in lines:
            x = self.x_at_y(line, ref_y)

            if x is None:
                continue

            found = False

            for group in groups:
                group_x = np.mean([g[4] for g in group])

                if abs(x - group_x) < threshold:
                    group.append([*line, x])
                    found = True
                    break

            if not found:
                groups.append([[*line, x]])

        # combine each group into one line
        for group in groups:
            points = []

            for x1, y1, x2, y2, _ in group:
                points.append((x1, y1))
                points.append((x2, y2))

            xs = [p[0] for p in points]
            ys = [p[1] for p in points]

            vx, vy, x0, y0 = cv.fitLine(
                np.array(points),
                cv.DIST_L2,
                0,
                0.01,
                0.01
            )

            vx = vx.item()
            vy = vy.item()
            x0 = x0.item()
            y0 = y0.item()

            left_y = 0
            right_y = 10000

            left_x = int(x0 - (y0 - left_y) * vx / vy)
            right_x = int(x0 - (y0 - right_y) * vx / vy)

            merged.append([
                left_x,
                left_y,
                right_x,
                right_y
            ])

        return merged

    def detect_court(self, frame):

        filtered_lines = []
        left_lines = [] # left lines have a positive slope
        right_lines = [] # right lines have a negative slope
        horizontal_lines = [] # horizontal lines have a slope close to 0

        output = frame.copy()

        # convert to hsv
        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

        # get mask for whiteish color
        lower_white = np.array([0,   0, 180])
        upper_white = np.array([180, 10, 255])

        # get only whiteish colors
        mask = cv.inRange(hsv, lower_white, upper_white)

        # run canny edge detection
        edges = cv.Canny(mask, 50, 150)

        # run hough lines
        lines = cv.HoughLinesP(
            edges, 1, np.pi / 180, threshold=100, minLineLength=60, maxLineGap=50
        )
    
        h = frame.shape[0]
        cutoff = int(h * 0.25)

        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line

                mid_y = (y1 + y2) / 2

                if mid_y < cutoff:
                    continue

                filtered_lines.append([x1, y1, x2, y2])

                angle = self.calculate_angle([x1, y1, x2, y2])

                if abs(angle) < 10: # close to 0 means horizontal
                    horizontal_lines.append([x1, y1, x2, y2])

                elif angle > 0: # positive slope
                    right_lines.append([x1, y1, x2, y2])

                else: # negative slope
                    left_lines.append([x1, y1, x2, y2])

        # merge detected line segments into actual court lines
        horizontal_lines = self.merge_horizontal_lines(horizontal_lines)
        left_lines = self.merge_slanted_lines(left_lines)
        right_lines = self.merge_slanted_lines(right_lines)

        return output
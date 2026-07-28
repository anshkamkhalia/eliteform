import torch
import numpy as np
import os

class TrackNetDataset(torch.utils.data.Dataset):
    def __init__(self):
        super().__init__()

        self.data_path = "sports/tennis/ball_tracking/tracknet/dataset"

        self.frames = []
        self.centers = []
        self.samples = []

        for i in range(1, len(os.listdir(self.data_path))//2+1):
            self.frames.append(np.load(os.path.join(self.data_path, f"video_{i}.npy")))
            self.centers.append(np.load(os.path.join(self.data_path, f"centers_{i}.npy")))

            for j in range(2, len(self.frames[-1])):
                self.samples.append((i - 1, j))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):

        video_idx, frame_idx = self.samples[index]
        frames = self.frames[video_idx]
        centers = self.centers[video_idx]

        frame_preprev = frames[frame_idx - 2]
        frame_prev = frames[frame_idx - 1]
        frame_curr = frames[frame_idx]

        x = np.concatenate((frame_curr, frame_prev, frame_preprev), axis=2)
        x = np.transpose(x, (2, 0, 1))
        x = x.astype(np.float32) / 255.0

        # create 360x640 gaussian heatmap
        heatmap = np.zeros((360, 640), dtype=np.float32)

        cx, cy = centers[frame_idx]

        if cx >= 0 and cy >= 0:
            cx, cy = int(round(cx)), int(round(cy))

            sigma = 2.5
            radius = int(3 * sigma)

            x0 = max(0, cx - radius)
            x1 = min(640, cx + radius + 1)
            y0 = max(0, cy - radius)
            y1 = min(360, cy + radius + 1)

            xx, yy = np.meshgrid(
                np.arange(x0, x1),
                np.arange(y0, y1)
            )

            heatmap[y0:y1, x0:x1] = np.exp(
                -((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma ** 2)
            )

        # convert heatmap intensity to 0-255 classes
        heatmap = (heatmap * 255).astype(np.uint8)

        # flatten pixels
        heatmap = heatmap.reshape(-1)

        label = heatmap.astype(np.int64)

        return (
            torch.from_numpy(x),
            torch.from_numpy(label)
        )
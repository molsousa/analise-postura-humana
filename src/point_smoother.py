import time
from src.one_euro_filter import OneEuroFilter

class PointSmoother:
    def __init__(self, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.filters = {}
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff

    def smooth(self, points):
        t = time.time()
        smoothed_points = []

        if not points:
            return []

        for i, point in enumerate(points):
            px, py, pz, visibility = point

            if i not in self.filters:
                self.filters[i] = {
                    'x': OneEuroFilter(t, self.min_cutoff, self.beta, self.d_cutoff),
                    'y': OneEuroFilter(t, self.min_cutoff, self.beta, self.d_cutoff),
                    'z': OneEuroFilter(t, self.min_cutoff, self.beta, self.d_cutoff),
                }

            smooth_x = self.filters[i]['x'].process(t, px)
            smooth_y = self.filters[i]['y'].process(t, py)
            smooth_z = self.filters[i]['z'].process(t, pz)

            smoothed_points.append((smooth_x, smooth_y, smooth_z, visibility))
            
        return smoothed_points

import math

# ==============================================================================
# The following code is a Python implementation of the 1€ filter.
# The 1€ filter is a simple algorithm to filter noisy signals for high
# performance and responsiveness.
#
# The algorithm is described in the following paper:
# "1 Euro Filter: A Simple Speed-based Low-pass Filter for Noisy Input"
# by Gery Casiez, Nicolas Roussel, and Daniel Vogel.
#
# This implementation is based on the C++ implementation by Gery Casiez.
# Link: https://gery.casiez.net/1euro/
# ==============================================================================

class LowPassFilter:
    def __init__(self, alpha):
        self.alpha = alpha
        self.y = None
        self.s = None

    def process(self, x):
        if self.y is None:
            self.s = x
        else:
            self.s = self.alpha * x + (1.0 - self.alpha) * self.s
        self.y = x
        return self.s


class OneEuroFilter:
    def __init__(self, freq, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.freq = freq
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_filter = LowPassFilter(self._alpha(min_cutoff))
        self.dx_filter = LowPassFilter(self._alpha(d_cutoff))
        self.last_time = None

    def _alpha(self, cutoff):
        te = 1.0 / self.freq
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / te)

    def process(self, t, x):
        if self.last_time is not None and t is not None:
            self.freq = 1.0 / (t - self.last_time)
        self.last_time = t

        # Estimate the derivative of the signal
        prev_x = self.x_filter.y
        if prev_x is None:
            dx = 0.0
        else:
            dx = (x - prev_x) * self.freq

        # Filter the derivative to get a smooth estimate
        edx = self.dx_filter.process(dx)

        # Use the derivative to adjust the cutoff frequency
        cutoff = self.min_cutoff + self.beta * abs(edx)
        alpha = self._alpha(cutoff)
        self.x_filter.alpha = alpha

        # Filter the signal
        return self.x_filter.process(x)

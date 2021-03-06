import wpilib
from wpilib.interfaces import PIDSource


class RangeFinder:

    def __init__(self, dio_number=0):
        self.range_finder_counter = wpilib.Counter(dio_number)
        self.range_finder_counter.setSemiPeriodMode(highSemiPeriod=True)
        self._smoothed_d = 0.0

    def _getDistance(self):
        return self.range_finder_counter.getPeriod() * 1000000 / 1000  # 10 usec is 1cm, return as metres

    def getPIDSourceType(self):  # pragma: no cover
        return PIDSource.PIDSourceType.kDisplacement

    def pidGet(self):
        return self._smoothed_d

    def execute(self):
        # get the distance and smooth it
        alpha = 0.7
        d = self._getDistance()
        if d > 40:  # Max range is around 40m
            d = 40
        self._smoothed_d = alpha * d + (1.0 - alpha) * self._smoothed_d

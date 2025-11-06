from enum import IntEnum


class Orientation(IntEnum):
    UPRIGHT = 0
    ROTATE_90_CW = 1
    ROTATE_180 = 2
    ROTATE_90_CCW = 3

    @property
    def description(self):
        return {
            Orientation.UPRIGHT: "Image is correctly oriented (0°).",
            Orientation.ROTATE_90_CW: "Image needs to be rotated 90° Clockwise to be correct.",
            Orientation.ROTATE_180: "Image needs to be rotated 180° to be correct.",
            Orientation.ROTATE_90_CCW: "Image needs to be rotated 90° Counter-Clockwise to be correct.",
        }[self]

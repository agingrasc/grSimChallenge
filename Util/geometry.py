import math as m

from RULEngine.Util.Position import Position

__author__ = 'jbecirovski'

def get_distance(position_1, position_2):
    """
    Distance between two positions.
    :param position_1: Position
    :param position_2: Position
    :return: float - distance in millimeter
    """
    assert(isinstance(position_1, Position))
    assert(isinstance(position_2, Position))
    return m.sqrt((position_2.x - position_1.x) ** 2 + (position_2.y - position_1.y) ** 2)


def get_angle(main_position, other):
    """
    Angle between position1 and position2 between -pi and pi
    :param main_position: Position of reference
    :param other: Position of object
    :return: float angle between two positions in radians
    """
    assert isinstance(main_position, Position), "TypeError main_position"
    assert isinstance(other, Position), "TypeError other"

    position_x = float(other.x - main_position.x)
    position_y = float(other.y - main_position.y)
    return m.atan2(position_y, position_x)


def cvt_angle_360(orientation):
    """
    Convert radians angle to 0-360 degrees
    :param orientation: float angle in radians
    :return: int angle with 0 to 360 range.
    """
    assert isinstance(orientation, (int, float)), "TypeError orientation"
    orientation = m.degrees(orientation)

    if orientation < 0:
        while True:
            if orientation >= 0:
                break
            else:
                orientation += 360
    elif orientation > 359:
        while True:
            if orientation < 360:
                break
            else:
                orientation -= 360
    return int(orientation)


def cvt_angle_180(orientation):
    """
    Convert radians angle to -180-180 degrees (same as m.degrees())
    :param orientation: float angle in radians
    :return: int angle with 180 to -179 range.
    """
    assert isinstance(orientation, (int, float)), "TypeError orientation"

    orientation = cvt_angle_360(orientation)
    if orientation > 180:
        return orientation-360
    elif orientation <= -180:
        return orientation+360
    else:
        return int(orientation)



import logging

from RULEngine.Game.Player import Player
from RULEngine.Util.Pose import Pose
from RULEngine.Util.Position import Position
from Util.geometry import get_distance
from .constante import *

logging.basicConfig(filename='debug.log', level=logging.DEBUG,
                    format='%(asctime)s %(message)s')

__author__ = 'jbecirovski' and 'agingras-courchesne'

def isInsideCircle(iPosition, iCenter, iRadius):
    '''
    isInsideCircle retourne True si la iPosition se trouve à l'intérieur
    de la zone circulaire de iCenter de rayon iRayon
    :param iPosition: object Position (RULEngine.Util.Position)
    :param iCenter: object Position (RULEngine.Util.Position)
    :param iRadius: int / float
    :return: bool
    '''
    assert(isinstance(iPosition, Position))
    assert(isinstance(iCenter, Position))
    assert(isinstance(iRadius, (int, float)))
    assert(iRadius >= 0)

    if get_distance(iPosition, iCenter) < iRadius:
        return True
    else:
        return False


def isOutsideCircle(iPosition, iCenter, iRadius):
    '''
    isOutsideCircle retourne False si la iPosition se trouve à l'intérieur
    de la zone circulaire de iCenter de rayon iRayon
    :param iPosition: object Position (RULEngine.Util.Position)
    :param iCenter: object Position (RULEngine.Util.Position)
    :param iRadius: int / float
    :return: bool
    '''
    return not isInsideCircle(iPosition, iCenter, iRadius)


def isInsideSquare(iPosition, Y_TOP, Y_BOTTOM, X_LEFT, X_RIGHT):
    '''
    isInsideSquare retourne True si la iPosition se trouve à l'intérieur
    de la zone rectangulaire ayant Y_TOP, X_LEFT, Y_BOTTOM et X_RIGHT.
    :param iPosition: object Position (RULEngine.Util.Position)
    :param Y_TOP: int, float
    :param Y_BOTTOM: int, float
    :param X_LEFT: int, float
    :param X_RIGHT: int, float
    :return: bool
    '''
    assert(isinstance(iPosition, Position))
    assert(isinstance(Y_TOP, (int, float)))
    assert(isinstance(Y_BOTTOM, (int, float)))
    assert(isinstance(X_LEFT, (int, float)))
    assert(isinstance(X_RIGHT, (int, float)))
    assert(Y_TOP > Y_BOTTOM)
    assert(X_RIGHT > X_LEFT)

    if not Y_BOTTOM < iPosition.y < Y_TOP:
        return False
    if not X_LEFT < iPosition.x < X_RIGHT:
        return False
    return True


def isOutsideSquare(position, X_TOP, X_BOTTOM, Y_LEFT, Y_RIGHT):
    '''
    isOutsideSquare retourne False si la iPosition se trouve à l'intérieur
    de la zone rectangulaire ayant Y_TOP, X_LEFT, Y_BOTTOM et X_RIGHT.
    :param position: object Position (RULEngine.Util.Position)
    :param X_TOP: int, float
    :param X_BOTTOM: int, float
    :param Y_LEFT: int, float
    :param Y_RIGHT: int, float
    :return: bool
    '''
    return not isInsideSquare(position, X_TOP, X_BOTTOM, Y_LEFT, Y_RIGHT)


class Collision:
    def __init__(self, objs):
        if isinstance(objs[0], Position):
            self.field_objects = objs
            logging.info('Receive position list')
        elif isinstance(objs[0], Pose):
            self.field_objects = []
            for i in objs:
                self.field_objects.append(i.position)
        elif isinstance(objs[0], Player):
            self.field_objects = []
            for i in objs:
                self.field_objects.append(i.pose.position)

    def check_collision(self):
        self._is_collision()

    def collision(self, pos):
        """ Retourne True si la position ou les positions projete provoque une
        collision. Envoyer la position actuelle du robot retourne True """
        if isinstance(pos, list):
            for i in pos:
                if self._collision(i):
                    return True
            return False
        else:
            return self._collision(pos)

    def _collision(self, pos, pos2=None, max_distance=ROBOT_RADIUS):
        """ Logique pour la collision. """
        logging.info('Number of object to check: %d', len(self.field_objects))
        if pos2 is None:
            for i in self.field_objects:
                obj_pos = i
                distance = get_distance(pos, obj_pos)
                logging.info('Distance is %d', distance)
                if distance < 2*max_distance:
                    return True
            return False
        else:
            distance = get_distance(pos, pos2)
            if distance < 2*max_distance:
                return True
            else:
                return False

    def _is_collision(self):
        """ Verifie si un objet dans la liste est en collision, retourne la liste
        des tuples des Position en collision """
        logging.info('Checking for collisions')
        ret = []
        l_objs = self.field_objects
        for i in self.field_objects:
            for j in l_objs:
                if self._collision(i, j):
                    ret.append((i, j))
        return ret

#!/usr/bin/python

import xml.etree.ElementTree as ET
from collections import namedtuple

Robot = namedtuple('Robot', ['id', 'x', 'y', 'theta'])
Ball = namedtuple('Ball', ['x', 'y', 'vx', 'vy'])

class Challenge:

    def __init__(self, node):
        self.name = node.find('Name').text
        self.description = node.find('Description').text
        self.yellow = self._loadTeam(node.find('Robots').find('TeamYellow'))
        self.blue = self._loadTeam(node.find('Robots').find('TeamBlue'))
        self.ball = self._loadBall(node.find('Ball'))

    def _loadBall(self, ball_node):

        x = float(ball_node.attrib['x'])
        y = float(ball_node.attrib['y'])
        try:
            vx = float(ball_node.attrib['vy'])
        except KeyError:
            vx = 0
        try:
            vy = float(ball_node.attrib['vy'])
        except KeyError:
            vy = 0

        return Ball(x, y, vx, vy)

    def _loadTeam(self, team_node):
        team = {}
        for robot in team_node.findall('Robot'):
            id = int(robot.attrib['id'])
            x = float(robot.attrib['x'])
            y = float(robot.attrib['y'])
            try:
                theta = float(robot.attrib['theta'])
            except KeyError:
                theta = 0
            team[id] = Robot(id, x, y, theta)

        return team


def load_challenges(path):
        tree = ET.parse(path)
        root = tree.getroot()
        return [Challenge(node) for node in root.iter('Challenge')]

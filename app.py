#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt4.QtGui import QApplication, QWidget, QMainWindow
from PyQt4.QtGui import QIcon
from PyQt4.uic import loadUi
from challenge import load_challenges
from communication.grSimRemote import grSimRemote
from RULEngine.Framework import Framework
from ChallengeStrategy import ChallengeStrategy
from RULEngine.Game.Referee import Command as RefCommand
import game_launcher
import defi1, defi2, defi3
import importlib

def reload_defis():
    defis = {}

    importlib.reload(defi1)
    importlib.reload(defi2)
    importlib.reload(defi3)

    defis['Defi1'] = defi1.Defi1
    defis['Defi2'] = defi2.Defi2
    defis['Defi3'] = defi3.Defi3

    return defis

class CompetitionGUI(QMainWindow):

    def __init__(self):
        super().__init__()

        self.remote = grSimRemote("127.0.0.1", 20011)

        self.framework_player = None
        self.challenge = None
        self.framework_ai = Framework(is_team_yellow = True)
        self.framework_ai.start_game(ChallengeStrategy, async=True)
        self.strategie = self.framework_ai.strategy

        loadUi("roboul_main.ui", self)

        self.challenges = load_challenges("challenges.xml")

        self.defis_comboBox.currentIndexChanged.connect(self.change_challenge_box)
        for challenge in self.challenges:
            self.defis_comboBox.addItem(challenge.name, challenge)

        self.resetButton.clicked.connect(self.reset)
        self.startButton.toggled.connect(self.startstop)

        self.show()

    def reset(self):
        self.change_challenge(self.defis_comboBox.currentIndex())

    def startstop(self, start):
        if isinstance(self.framework_player, Framework):
            self.framework_player.stop_game()

        if start:
            command = "NORMAL_START"
            defis = reload_defis()
            if self.challenge:
                self.framework_player = game_launcher.start_game(defis[self.challenge]())
                self.framework_player.game.referee.command = RefCommand(command)
        else:
            command = "HALT"

        self.framework_ai.game.referee.command = RefCommand(command)

    def change_challenge_box(self, challenge_index):
        self.startstop(False)
        self.startButton.setChecked(False)
        self.change_challenge(challenge_index)

    def change_challenge(self, challenge_index):

        #This does not stop the framework_player

        challenge = self.defis_comboBox.itemData(challenge_index)
        challenge.reload()

        self.remote.start_batch()

        for robot_id, robot in challenge.blue.items():
            self.remote.place_player(robot.id, False,
                                     robot.x, robot.y, robot.theta)

        for robot_id, robot in challenge.yellow.items():
            self.remote.place_player(robot.id, True,
                                     robot.x, robot.y, robot.theta)
        ball = challenge.ball
        self.remote.place_ball(ball.x, ball.y, ball.vx, ball.vy)

        self.remote.end_batch()

        self.description_label.setText(challenge.description)

        self.strategie.set_mode(challenge.strategy)

        self.challenge = challenge.deficlass

    def closeEvent(self,event):
        self.framework_ai.stop_game()
        if isinstance(self.framework_player, Framework):
            self.framework_player.stop_game()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    roboul_main = CompetitionGUI()
    sys.exit(app.exec_())

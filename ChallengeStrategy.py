from RULEngine.Strategy.Strategy import Strategy
from RULEngine.Command import Command
from RULEngine.Util.Pose import Pose
from RULEngine.Util.Position import Position
import sys, time

__author__ = 'jbecirovski'

class ChallengeStrategy(Strategy):
    def __init__(self, field, referee, team, opponent_team, is_team_yellow=False):
        Strategy.__init__(self, field, referee, team, opponent_team)

        self.team.is_team_yellow = is_team_yellow
        self.on_start = self.halt

    def set_mode(self, value):
        self.on_start = getattr(self, value, self.halt)

    def halt(self):
        pass

    def center(self):
        self._send_command(Command.MoveTo(self.team.players[0], self.team, Position(0,0)))

    def on_halt(self):
        self.on_start()

    def on_stop(self):
        self.on_start()

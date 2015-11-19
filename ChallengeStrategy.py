from RULEngine.Strategy.Strategy import Strategy
from RULEngine.Command import Command
import sys, time

__author__ = 'jbecirovski'

class ChallengeStrategy(Strategy):
    def __init__(self, field, referee, team, opponent_team, is_team_yellow=False):
        Strategy.__init__(self, field, referee, team, opponent_team)

        self.team.is_team_yellow = is_team_yellow

    def on_start(self):
        pass

    def on_halt(self):
        self.on_start()

    def on_stop(self):
        self.on_start()

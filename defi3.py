#!/usr/bin/python
import game_launcher
from game_launcher import Defi
from RULEngine.Util.Pose import Pose
from RULEngine.Util.Position import Position
from RULEngine.Game.Player import Player

class Defi3(Defi):

    def initialiser(self, coach, terrain, etats, equipe_bleu, equipe_jaune):
        self.etat = self.passer

    def passer(self, coach, terrain, etats, equipe_bleu, equipe_jaune):
        coach.bouger(0, Position(3000, 0))

    def passer2(self, coach, terrain, etats, equipe_bleu, equipe_jaune):
        self.prochain_etat(self.termine)

    def termine(self, coach, terrain, etats, equipe_bleu, equipe_jaune):
        pass
import math as m
import time

from RULEngine.Command import Command
from RULEngine.Framework import Framework
from RULEngine.Game.Ball import Ball
from RULEngine.Game.Player import Player
from RULEngine.Strategy.Strategy import Strategy
from RULEngine.Util import geometry
from RULEngine.Util.Pose import Pose
from RULEngine.Util.Position import Position
from RULEngine.Util.constant import *
from RULEngine.Util.Vector import Vector

from Util.gameLogic import Collision

EVENT_SUCCEED = "success"
EVENT_TIMEOUT = "timeout"
EVENT_FAIL = "rate"
EVENT_WIP = "inprogress"
NOUS = 'blue'
EUX = 'yellow'
BOUNDING_BOX_DELTA = ROBOT_RADIUS * 2

def getStrategy(defi):
    class DefiStrategy(Strategy):
            def __init__(self, field, referee, team, opponent_team, is_team_yellow=False):
                Strategy.__init__(self, field, referee, team, opponent_team)

                self.team.is_team_yellow = is_team_yellow

                self.robot_states = [self._idle for robot in team.players]
                self.robot_events = [EVENT_SUCCEED for robot in team.players]
                self.robot_goals = [Position() for robot in team.players] #Position vide. Position visée
                self.robot_aim = [Position() for robot in team.players] #Position vide. Position visée
                self.robot_kick_force = [0 for robot in team.players] #Force de kick
                self.robot_kick_times = [0 for robot in team.players] #Nombre de kick
                self.robot_pass_target = [0 for robot in team.players] #Robot à qui faire la passe

                self.old_ball_speed = 0
                self.collider = Collision(team.players + opponent_team.players)
                self.collision_warning = []
                self.last_time_kick = time.time()

            def on_start(self):
                defi.etat(self, self.field, self.robot_events, self.team.players, self.opponent_team.players)
                self.collider = Collision(self.team.players + self.opponent_team.players)
                self.execute()

            def execute(self):
                for index, state in enumerate(self.robot_states):
                    state(index)

            def on_halt(self):
                self.on_stop()

            def on_stop(self):
                for player in self.team.players:
                    pose = player.pose
                    command = Command.MoveToAndRotate(player, self.team, pose)
                    self._send_command(command)

            def _convertirPosition(self, position):
                """ position represente un objet (player, ball, etc.), on extrait
                la position et on la retourne """
                if isinstance(position, Player):
                    return position.pose.position
                elif isinstance(position, Ball):
                    return position.position
                elif isinstance(position, Position):
                    return position

            def checkedNextStep(self, state, joueur):
                if self.robot_events[joueur] == EVENT_SUCCEED:
                    self.robot_events[joueur] = EVENT_WIP
                    self.robot_states[joueur] = state




            # ----------Private---------

            def _succeed(self, joueur):
                self.robot_events[joueur] = EVENT_SUCCEED
                self.robot_states[joueur] = self._idle

            def _fail(self, joueur):
                self.robot_events[joueur] = EVENT_FAIL
                self.robot_states[joueur] = self._idle

            def _timeout(self, joueur):
                self.robot_events[joueur] = EVENT_TIMEOUT
                self.robot_states[joueur] = self._idle

            def _getDeadZone(self, posType):
                if isinstance(posType, Player):
                    return 225
                elif isinstance(posType, Ball):
                    return 225
                elif isinstance(posType, Position):
                    return 50

            def _bouger(self, joueur):
                #TODO: ajuster la deadzone en fonction du type du goal
                position = self._convertirPosition(self.robot_goals[joueur])
                player = self.team.players[joueur]
                dist = geometry.get_distance(player.pose.position, position)
                deadzone = self._getDeadZone(self.robot_goals[joueur])

                if dist < deadzone: # si la distance est exactement 0, la position n'est pas bonne
                    self._succeed(joueur)
                else:
                    orientation = player.pose.orientation
                    command = Command.MoveToAndRotate(player, self.team,
                                                      Pose(position, orientation))
                    self._send_command(command)

            def _bougerPlusAim(self, joueur, deadzone=None):
                destination = self._convertirPosition(self.robot_goals[joueur])
                cible = self._convertirPosition(self.robot_aim[joueur])
                if not deadzone:
                    deadzone = self._getDeadZone(self.robot_goals[joueur])
                player = self.team.players[joueur]
                dist = geometry.get_distance(player.pose.position, destination)
                angle = m.fabs(geometry.get_angle(player.pose.position, cible) - player.pose.orientation)  #angle between the robot and the ball
                if(dist <= deadzone and angle <= 0.01):  #0.087 rad = 5 deg : marge d'erreur de l'orientation
                    self._succeed(joueur)
                elif(dist > deadzone and angle <= 0.01):
                    command = Command.MoveTo(player, self.team, destination)
                    self._send_command(command)
                elif(dist <= deadzone and angle > 0.01):
                    orientation = geometry.get_angle(player.pose.position, cible)
                    command = Command.Rotate(player, self.team, orientation)
                    self._send_command(command)
                else:
                    orientation = geometry.get_angle(player.pose.position, cible)
                    command = Command.MoveToAndRotate(player, self.team, Pose(destination, orientation))
                    self._send_command(command)

            def _passer(self, joueur):
                self.robot_goals[joueur] = self._lance_position(joueur)
                coequipier = self.robot_pass_target[joueur]
                self._bougerPlusAim(joueur)
                self.robot_states[joueur] = self._passer
                self.robot_kick_times[joueur] = 100
                self.old_ball_speed = m.sqrt(self.field.ball.velocity.x**2 + self.field.ball.velocity.y**2)
                if self.robot_events[joueur] == EVENT_SUCCEED and self.robot_events[coequipier] == EVENT_SUCCEED:
                    self.robot_events[joueur] = EVENT_WIP
                    self.robot_states[joueur] = self._lancer_p2
                    self.robot_events[coequipier] = EVENT_WIP
                    self.robot_states[coequipier] = self._recevoirPasse

            def _recevoirPasse(self, joueur):
                receveur = self.team.players[joueur].pose.position
                balle = self.field.ball.position
                a = self.field.ball.velocity.y/self.field.ball.velocity.x
                b = balle.y - a*balle.x
                self.robot_goals[joueur] = Position(receveur.x, a*receveur.x+b)
                self._bougerPlusAim(joueur)

            def _lancer(self, joueur):
                self.robot_goals[joueur] = self._lance_position(joueur)
                self._bougerPlusAim(joueur)
                self.robot_kick_times[joueur] = 100
                self.old_ball_speed = m.sqrt(self.field.ball.velocity.x**2 + self.field.ball.velocity.y**2)
                self.checkedNextStep(self._lancer_p2, joueur)

            def _lancer_p2(self, joueur):
                self.robot_goals[joueur] = self.field.ball
                player = self.team.players[joueur]
                new_ball_speed = m.sqrt(self.field.ball.velocity.x**2 + self.field.ball.velocity.y**2)
                if self.robot_kick_times[joueur] > 0:
                    command = Command.Kick(player, self.team, self.robot_kick_force[joueur])
                    self._send_command(command)
                    self.robot_kick_times[joueur] -= 1
                    self.old_ball_speed = new_ball_speed
                elif new_ball_speed > 1000:
                    self._succeed(joueur)
                else:
                    self._fail(joueur)

            def _lance_position(self, joueur):
                player = self.team.players[joueur]
                robot = self._convertirPosition(player)
                balle = self._convertirPosition(self.field.ball)
                cible = self._convertirPosition(self.robot_aim[joueur])
                dist = geometry.get_distance(robot, balle)
                lim_dist = dist*0.5
                deadzone = lim_dist if lim_dist > 125 else 60
                angle = m.fabs(geometry.get_angle(robot, cible) - player.pose.orientation)
                if angle > 0.3:
                    deadzone = max(deadzone, 200)

                #print(deadzone)

                angle = m.atan2(robot.y-cible.y,
                                robot.x-cible.x)
                x = balle.x + deadzone*m.cos(angle)
                y = balle.y + deadzone*m.sin(angle)
                return Position(x, y)

            def _idle(self, joueur):
                player = self.team.players[joueur]
                pose = player.pose
                command = Command.MoveToAndRotate(player, self.team, pose)
                self._send_command(command)


            # ----------Public----------
            def bouger(self, joueur, position, cible=None):
                """
                :param joueur: Le numéro du robot
                :param position: La position à atteindre
                :param cible: La cible du robot
                :return: Rien, cette fonction modifie l'état des robots
                """
                assert(isinstance(joueur, int))
                assert(isinstance(position, (Position, Player, Ball)))
                self.robot_goals[joueur] = position
                if cible:
                    assert(isinstance(cible, (Position, Player, Ball)))
                    self.robot_aim[joueur] = cible
                    self.robot_states[joueur] = self._bougerPlusAim
                else:
                    self.robot_states[joueur] = self._bouger
                self.robot_events[joueur] = EVENT_WIP

            def passe(self, joueur1, joueur2, force=3):
                """
                :param joueur1: Le numéro du robot affectuant la passe
                :param joueur2: Le numéro du robot recevant la passe
                :param force: La force de la passe
                :return: Rien, cette fonction modifie l'état des robots
                """
                assert(isinstance(joueur1, int))
                assert(isinstance(joueur2, int))
                assert(isinstance(force, int))
                self.robot_kick_force[joueur1] = force
                self.robot_pass_target[joueur1] = joueur2
                self.robot_pass_target[joueur2] = joueur1
                position = self._lance_position(joueur1)
                self.bouger(joueur1, position, cible=self.team.players[joueur2])
                self.bouger(joueur2, self.team.players[joueur2].pose.position, cible=self.field.ball.position)
                self.robot_states[joueur1] = self._passer
                self.robot_events[joueur1] = EVENT_WIP
                self.robot_states[joueur2] = self._bougerPlusAim
                self.robot_events[joueur2] = EVENT_WIP

            def lancer(self, joueur, cible, force=3):
                """
                :param joueur: Le numéro du joueur affectuant le lancer
                :param cible: La cible du robot
                :param force: La force du lancer
                :return: Rien, cette fonction modifie l'état des robots
                """
                assert(isinstance(joueur, int))
                assert(isinstance(cible, (Position, Player, Ball)))
                assert(isinstance(force, int))
                self.robot_kick_force[joueur] = force
                position = self._lance_position(joueur)
                self.bouger(joueur, position, cible=cible)
                self.robot_states[joueur] = self._lancer
                self.robot_events[joueur] = EVENT_WIP

            def chercher_balle(self, joueur):
                """
                :param joueur: Le numéro du robot
                """
                assert(isinstance(joueur, int))
                ballPosition = self.field.ball
                self.bouger(joueur, ballPosition, cible=self.field.ball)

            def positionner_entre_deux_ennemis(self, joueur, ennemi1, ennemi2, cible=None):
                """
                :param joueur: Le numéro du robot à déplacer
                :param ennemi1: Le numéro du premier robot ennemi
                :param ennemi2: Le numéro du deuxième robot ennemi
                :param cible: La cible du robot à déplacer
                :return: Rien, cette fonction modifie l'état des robots
                """
                assert(isinstance(joueur, int))
                assert(isinstance(ennemi1, int))
                assert(isinstance(ennemi2, int))
                assert(isinstance(cible, (Position, Player, Ball)))
                position1 = self.opponent_team.players[ennemi1].pose.position
                position2 = self.opponent_team.players[ennemi2].pose.position

                x = (position1.x + position2.x)/2
                y = (position1.y + position2.y)/2
                position = Position(x,y)
                self.bouger(joueur, position, cible)

            def positionner_entre_ami_et_ennemi(self, joueur, ami, ennemi, cible=None):
                """
                :param joueur: Le numéro du robot à déplacer
                :param ami: Le numéro du robot ami
                :param enemi: Le numéro du robot ennemi
                :param cible: La cible du robot à déplacer
                :return: Rien, cette fonction modifie l'état des robots
                """
                assert(isinstance(joueur, int))
                assert(isinstance(ami, int))
                assert(isinstance(ennemi, int))
                assert(isinstance(cible, (Position, Player, Ball)))
                position1 = self.team.players[ami].pose.position
                position2 = self.opponent_team.players[ennemi].pose.position

                x = (position1.x + position2.x)/2
                y = (position1.y + position2.y)/2
                position = Position(x,y)
                self.bouger(joueur, position, cible)


            def stop(self, joueur):
                """
                :param joueur: Le numéro du robot à stopper
                :return: Rien, cette fonction modifie l'état des robots
                """
                self.robot_states[joueur] = self._idle
                self.robot_events[joueur] = EVENT_SUCCEED

            def collision(self, pos):
                """
                Vérifie si positionné un robot à une position engendre une collision.
                :param pos: La position à vérifier
                :return: True si la position est en collision avec un objet sur le terrain
                """
                self.collider = Collision(self.team.players + self.opponent_team.players)
                return self.collider.collision(pos)

            def get_position(self, joueur, team=NOUS):
                """
                Retourne la position du robot identifié par joueur
                :param joueur: Le numéro du robot dont on veut récupérer la position
                :param team: (OPT) l'équipe défini par la constante NOUS ou EUX
                :return: La position du robot.
                """
                if team == NOUS:
                    return self.team.players[joueur].pose.position
                else:
                    return self.opponent_team.players[joueur].pose.position

            def get_orientation(self, joueur, team=NOUS):
                """
                Retourne l'orientation du robot identifié par joueur
                :param joueur: Le numéro du robot dont on veut récupérer l'orientation
                :param team: (OPT) l'équipe défini par la constante NOUS ou EUX
                :return: L'orientation (radian) du robot
                """
                if team == NOUS:
                    return self.team.players[joueur].pose.orientation
                else:
                    return self.opponent_team.players[joueur].pose.orientation

            def raycast(self, joueur, vec, team=NOUS):
                """
                Retourne une liste contenant les positions des collisions de tracer un rayon à partir de joueur dans
                la direction du vecteur.
                :param joueur: Le numéro du robot à partir duquel le rayon est tracé
                :param vec: Vecteur du rayon tracé.
                :param team: (OPT) l'équipe défini par la constante NOUS ou EUX
                :return: Une liste de posision des collisions détectés. Si vide -> il n'y a pas de collisions
                """
                ret = []
                if team == NOUS:
                    joueur = self.team.players[joueur]
                else:
                    joueur = self.opponent_team.players[joueur]

                joueur_pos = joueur.pose.position
                x = joueur_pos.x
                y = joueur_pos.y

                obj = self.team.players + self.opponent_team.players
                for o in obj:
                    pos = o.pose.position
                    xp = pos.x
                    yp = pos.y
                    x_min = xp - BOUNDING_BOX_DELTA
                    x_max = xp + BOUNDING_BOX_DELTA
                    y_min = yp - BOUNDING_BOX_DELTA
                    y_max = yp + BOUNDING_BOX_DELTA

                    if vec.x == 0 and vec.y == 0:
                        # vecteur nulle
                        continue
                    elif vec.x == 0:
                        # aucune variation en x
                        continue
                    elif vec.y == 0:
                        # aucune variation en y
                        continue
                    else:
                        kx = (xp - x)/vec.x
                        ky = (yp - y)/vec.y

                    print("Collision detecte!")

                    xn = x + kx*vec.x
                    yn = y + ky*vec.y

                    if xn > x_min and xn < x_max and yn > y_min and yn < y_max:
                        posn = Position(xn, yn)
                        theta = get_angle(joueur_pos, posn)
                        phi = m.pi/2 - theta
                        xc = xp + BOUNDING_BOX_DELTA*m.cos(phi)
                        yc = yp + BOUNDING_BOX_DELTA*m.sin(phi)
                        coll = Position(xp, yp)
                        ret.append(coll)
                return ret


    return DefiStrategy


def start_game(main_loop):

    framework = Framework()
    framework.start_game(getStrategy(main_loop), async = True)
    return framework


class Defi(object):

    def __init__(self):
        self.etat = self.initialiser
        self.timeout = time.time() + 9999999999

    def prochain_etat(self, prochain_etat, timeout=999999, timeout_fcn=None):
        if timeout_fcn:
            self._timeout_fcn = timeout_fcn
        else:
            self._timeout_fcn = prochain_etat

        self._prochain_etat = prochain_etat
        self.timeout = time.time() + timeout
        self.etat = self._attendre

    def _attendre(self, coach, terrain, etats, equipe_bleu, equipe_jaune):
        if not any(event == EVENT_WIP for event in coach.robot_events) :
            self.etat = self._prochain_etat
        elif time.time() > self.timeout:
            self.etat = self._timeout_fcn

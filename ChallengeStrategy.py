from RULEngine.Strategy.Strategy import Strategy
from RULEngine.Command import Command
from RULEngine.Util.Pose import Pose
from RULEngine.Util.Position import Position
from RULEngine.Util.geometry import intercept, get_distance, get_angle
from RULEngine.Util.area import *
import sys, time, math

__author__ = 'jbecirovski'

class ChallengeStrategy(Strategy):
    def __init__(self, field, referee, team, opponent_team, is_team_yellow=False):
        Strategy.__init__(self, field, referee, team, opponent_team)

        self.team.is_team_yellow = is_team_yellow
        self.init_pst = None
        self.target = [None for _ in range(6)]
        self.state = [None for _ in range(6)]
        self.lastKick = time.time()
        self.beginTime = time.time()
        self.on_start = self.halt

    def set_mode(self, value):
        self.beginTime = time.time()
        self.init_pst = None
        self.target = [None for _ in range(6)]
        self.state = [None for _ in range(6)]
        self.on_start = getattr(self, value, self.halt)


    def halt(self):
        pass

    ''' STRATEGY - PATHFINDER (MOVE) '''
    def move_circle(self):
        if self.init_pst is None:
            self.init_pst = [self.team.players[i].pose.position for i in range(6)]
            self.state = [None for _ in range(6)]
            self.target = [None for _ in range(6)]
            #print('INIT: {}\nSTATE: {}\nTARGET: {}'.format(self.init_pst, self.state, self.target))
        else:
            for i in range(6):
                if self.state[i] is None:
                    self.state[i] = [self.move_left, self.move_right, self.move_top, self.move_bottom][i % 4]
                    self.target[i] = self.init_pst[i]
                    #print('Robot: {} | State: {} | Pst: {} | Target: {}'.format(i, self.state[i], self.init_pst[i], self.target[i]))
                else:
                    self.state[i](i)
                    self._send_command(Command.MoveTo(self.team.players[i], self.team, self.target[i]))

    def move_left(self, i):
        if get_distance(self.team.players[i].pose.position, self.target[i]) < 250:
            self.target[i] = self.init_pst[i] + Position(500, 0)
            self.state[i] = self.move_top

    def move_top(self, i):
        if get_distance(self.team.players[i].pose.position, self.target[i]) < 250:
            self.target[i] = self.init_pst[i] + Position(500, 0)
            self.state[i] = self.move_right

    def move_right(self, i):
        if get_distance(self.team.players[i].pose.position, self.target[i]) < 250:
            self.target[i] = self.init_pst[i] + Position(0, -500)
            self.state[i] = self.move_bottom

    def move_bottom(self, i):
        if get_distance(self.team.players[i].pose.position, self.target[i]) < 250:
            self.target[i] = self.init_pst[i] + Position(-500, 0)
            self.state[i] = self.move_left
    ''' END STRATEGY - PATHFINDER (MOVE) '''

    def center(self):
        self._send_command(Command.MoveTo(self.team.players[0], self.team, Position(0,0)))

    ''' STRATEGY - ATTACK '''
    def attackStrategy(self):
        bot0_pst = self.team.players[0].pose.position
        bot1_pst = self.team.players[1].pose.position
        if self.field.ball.position.x < -1500:
            self.attackState()
        else:
           self.standState()

    def standState(self):
        self._send_command(Command.MoveTo(self.team.players[1], self.team, Position(-2000, -2500)))

        next_pst = self.comeBehind(self.team.players[0].pose.position, self.field.ball.position, Position(-2000, 2500))
        agl = get_angle(self.team.players[0].pose.position, self.field.ball.position)
        self._send_command(Command.MoveToAndRotate(self.team.players[0], self.team, Pose(next_pst, agl)))


    def attackState(self):
        bot0_pst = self.team.players[0].pose.position
        bot1_pst = self.team.players[1].pose.position
        ball_pst = self.field.ball.position

        player = self.opponent_team.players[2]
        balle = self.field.ball.position
        couvrir = Position(-4500, 0)
        threshold = 500

        position = intercept(player, balle, couvrir, threshold)
        self._send_command(Command.MoveTo(self.team.players[2], self.team, position))

        if ball_pst.y > 0:
            self.forwarder(0)
            self.assistant(1)
        else:
            self.forwarder(1)
            self.assistant(0)

    def forwarder(self, i):
        bot_pst = self.team.players[i].pose.position
        bot_dir = self.team.players[i].pose.orientation
        ball_pst = self.field.ball.position

        goal_pst = self.opponent_team.players[0].pose.position
        agl = get_angle(bot_pst, ball_pst)
        dst = get_distance(bot_pst, ball_pst)


        enemy_dst_top = get_distance(goal_pst, Position(-4500, 800))
        enemy_dst_bot = get_distance(goal_pst, Position(-4500, -800))
        if time.time() > self.beginTime + 8:
            self.kickBallAction(i)
        elif enemy_dst_bot > enemy_dst_top:
            self.kickBallAction(i) if i else self.passBallAction(i)
        else:
            self.passBallAction(i) if i else self.kickBallAction(i)

    def assistant(self, i):
        self.receptBallAction(i)

    def fetchAction(self, i):
        agl = get_angle(self.team.players[i].pose.position, self.field.ball.position)
        self._send_command(Command.MoveToAndRotate(self.team.players[i], self.team, Pose(self.field.ball.position, agl)))

    def kickAction(self, i, force=5):
        agl = get_angle(self.team.players[i].pose.position, self.field.ball.position)
        if time.time() - (self.lastKick + 0.25) > 0 and -0.09 < agl - self.team.players[i].pose.orientation < 0.09:
            self.lastKick = time.time()
            self._send_command(Command.Kick(self.team.players[i], self.team, force if force <= 8 else 8))

    def kickBallAction(self, i):
        bot_pst = self.team.players[i].pose.position
        tar_pst = self.field.ball.position
        goal_pst = Position(-4500, -150) if i else Position(-4500, 150)
        next_pst = self.comeBehind(bot_pst, tar_pst, goal_pst)
        agl = get_angle(bot_pst, goal_pst)
        agl2 = get_angle(bot_pst, tar_pst)
        if get_distance(tar_pst, bot_pst) < 130 and -0.045 < agl - agl2 < 0.045 and tar_pst.x < -1000:
            self.kickAction(i, force=8)
        else:
            self._send_command(Command.MoveToAndRotate(self.team.players[i], self.team, Pose(next_pst, agl)))

    def passBallAction(self, i):
        bot_pst = self.team.players[i].pose.position
        tar_pst = self.field.ball.position
        goal_pst = self.team.players[not i].pose.position + Position(-50, 0)
        next_pst = self.comeBehind(bot_pst, tar_pst, goal_pst)
        agl = get_angle(bot_pst, goal_pst)
        agl2 = get_angle(bot_pst, tar_pst)
        if get_distance(tar_pst, bot_pst) < 130 and -0.045 < agl - agl2 < 0.045:
            kick_f = get_distance(goal_pst, bot_pst) // 500
            self.kickAction(i, force=kick_f)
        else:
            self._send_command(Command.MoveToAndRotate(self.team.players[i], self.team, Pose(next_pst, agl)))

    @staticmethod
    def comeBehind(bot, tar, obj):
        result_pst = Position()
        aglTar2Obj = get_angle(tar, obj)
        aglBot2Tar = get_angle(tar, bot)
        diffAglBot2Obj = aglBot2Tar - aglTar2Obj

        if get_distance(bot, tar) > 130:
            if 0 <= diffAglBot2Obj < 1.57:
                result_pst = stayOutsideCircle(tar, obj, get_distance(obj, tar) + 500)
                result_pst.x = result_pst.x + 500 * math.cos(aglTar2Obj + 1.57)
                result_pst.y = result_pst.y + 500 * math.sin(aglTar2Obj + 1.57)

            elif -1.57 <= diffAglBot2Obj < 0:
                result_pst = stayOutsideCircle(tar, obj, get_distance(obj, tar) + 500)
                result_pst.x = result_pst.x + 500 * math.cos(aglTar2Obj - 1.57)
                result_pst.y = result_pst.y + 500 * math.sin(aglTar2Obj - 1.57)

            elif 1.57 <= diffAglBot2Obj < 2.9:
                result_pst = stayOutsideCircle(tar, obj, get_distance(obj, tar) + 500)

            elif -2.9 <= diffAglBot2Obj < -1.57:
                result_pst = stayOutsideCircle(tar, obj, get_distance(obj, tar) + 500)

            else:
                result_pst = stayOutsideCircle(tar, obj, get_distance(tar, obj) + 90)

        else:
            result_pst = stayOutsideCircle(tar, obj, get_distance(tar, obj))

        return result_pst

    def receptBallAction(self, i):
        bot_pst = self.team.players[i].pose.position
        ball_pst = self.field.ball.position
        agl1 = get_angle(bot_pst, ball_pst)
        agl2 = get_angle(bot_pst, Position(-4500, 0))
        agl = agl2 - agl1
        agl = agl1 + agl * 0.3

        if i:
            next_pst = stayInsideSquare(ball_pst, -1500, -1501, -4500, 4500)
        else:
            next_pst = stayInsideSquare(ball_pst, 1501, 1500, -4500, 4500)
        self._send_command(Command.MoveToAndRotate(self.team.players[i], self.team, Pose(next_pst, agl)))

    ''' END STRATEGY - ATTACK '''

    def goaler(self):
        player = self.team.players[0]
        balle = self.field.ball.position
        couvrir = Position(4500, 0)
        threshold = 500

        position = intercept(player, balle, couvrir, threshold)
        self._send_command(Command.MoveTo(self.team.players[0], self.team, position))

    def on_halt(self):
        pass

    def on_stop(self):
        pass

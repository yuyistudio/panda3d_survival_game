# encoding: utf8

__author__ = 'Leon'


from util import lerp_util, log
from panda3d.core import Vec3
from variable.global_vars import G
import math


class CameraManager(object):
    def __init__(self):
        #self.cam_pos_lerper = lerp_util.LerpVec3(4.3210)
        self.cam_height_lerper = lerp_util.FloatLerp(30, 15, 2000 if G.debug else 40, 6.666)
        self.cam_angle_lerper = lerp_util.FloatLerp(0, -100000, 100000,6.6666)
        self.xy_ratio = 1.4

        G.accept('wheel_up', self._wheel_event, [-1])
        G.accept('wheel_down', self._wheel_event, [1])
        G.accept('q', self._change_angle, [-1])
        G.accept('e', self._change_angle, [1])

        self._angle_gap = 90
        self._angle_index = 0
        self._change_angle(1)

        self._pos_offset = Vec3()
        self._center_pos = Vec3()

    def _change_angle(self, delta):
        self._angle_index += delta
        self.cam_angle_lerper.set_target(self._angle_gap * self._angle_index)

    def _wheel_event(self, value):
        self.cam_height_lerper.change_target(value * 5)

    def look_at(self, pos):
        self._center_pos = pos

    def on_update(self, dt):
        angle = self.cam_angle_lerper.lerp(dt)
        height = self.cam_height_lerper.lerp(dt)

        radius = height * self.xy_ratio
        x = radius * math.sin(math.radians(angle))
        y = radius * math.cos(math.radians(angle))
        z = height
        self._pos_offset = Vec3(x, y, z)

        G.cam.set_pos(self._center_pos + self._pos_offset)
        G.cam.look_at(self._center_pos)

    def get_direction(self, dx, dy):
        angle = self.cam_angle_lerper.get_target()
        rad = math.radians(angle)
        cosine = math.cos(rad)
        sine = math.sin(rad)
        # 二维顺时针旋转矩阵展开
        dx, dy = cosine * dx + sine * dy, - sine * dx + cosine * dy
        return - dx, - dy

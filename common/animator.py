# encoding: utf8
import sys
sys.path.insert(0, 'd:\\Leon\\gamedev\\pandas3d\\learn')
from direct.actor import Actor
from panda3d.core import *
from variable.global_vars import G


class Animator(object):
    _NO_MORE_EVENT = -1

    def __init__(self, config, event_handler):
        """
        :param config:
        :param event_handler: object with function AnimName_EventName() to handle events.
        :return:
        """
        self._config = config
        self._handler = event_handler

        self._current_event_idx = 0
        self._last_frame = -1
        self._last_anim = None

        self._events = {}
        anim_mapping = {}
        filepath = config['filepath']
        anim_file_pattern = filepath.replace('.egg', '-%s.egg')
        for anim_name, anim_config in config.get('animations').iteritems():
            anim_mapping[anim_name] = anim_file_pattern % anim_name

            event_config = anim_config.get('events')
            if event_config:
                anim_events = []
                for event_name, event_frame in event_config:
                    assert event_frame >= 0
                    anim_events.append((event_name, event_frame))
                anim_events.sort(key=lambda event: event[1])
                self._events[anim_name] = anim_events

        self._actor_np = Actor.Actor(filepath, anim_mapping)
        for tex in self._actor_np.find_all_textures():
            tex.set_magfilter(Texture.FT_nearest)
            tex.set_minfilter(Texture.FT_linear)
        for anim_name, anim_config in config.get('animations').iteritems():
            self._actor_np.setPlayRate(anim_config.get('rate', 1.), anim_name)

        self.play(config.get('default', 'idle'), once=False)

    def get_actor_np(self):
        return self._actor_np

    def _emit_event(self, anim_name, event_name):
        try:
            fn = getattr(self._handler, '%s_%s' % (anim_name, event_name))
            if fn:
                fn()
        except:
            pass

    def _trigger_events(self, anim_name, current_frame):
        if not self._events:
            return

        anim_events = self._events.get(anim_name)
        if not anim_events:
            return

        if current_frame < self._last_frame:
            self._last_frame = current_frame
            # 触发还未来的及触发的事件，比如最后一帧的事件
            while self._current_event_idx < len(anim_events):
                self._emit_event(anim_name, anim_events[self._current_event_idx][0])
                self._current_event_idx += 1
            # 重头开始触发事件
            self._current_event_idx = 0
        else:
            self._last_frame = current_frame
            if self._current_event_idx == Animator._NO_MORE_EVENT:
                self._last_frame = current_frame
                return

        while True:
            event = anim_events[self._current_event_idx]
            if current_frame >= event[1]:
                self._emit_event(anim_name, event[0])
                self._current_event_idx += 1
                if self._current_event_idx >= len(anim_events):
                    # 事件都触发完了，等待下次动画loop时重置事件
                    self._current_event_idx = Animator._NO_MORE_EVENT
                    break
            else:
                break

    def on_update(self):
        current_anim = self._actor_np.getCurrentAnim()
        if not current_anim:
            self._trigger_events(self._last_anim, -1)
            self.play('idle', once=False)
            return

        self._trigger_events(current_anim, self._actor_np.getCurrentFrame())
        self._last_anim = current_anim

    def play(self, anim_name, once):
        current_anim = self._actor_np.getCurrentAnim()
        if anim_name == current_anim:
            return

        self._actor_np.stop(current_anim)
        self._current_event_idx = 0  # reset events

        if once:
            self._actor_np.play(anim_name)
        else:
            self._actor_np.loop(anim_name)



class Handler(object):
    def walk_done(self):
        print 'walk done'

    def walk_start(self):
        print 'walk start'

    def pickup_pickup(self):
        import random
        print 'picked something:', random.random()

    def pickup_done(self):
        print 'pick done'


def test():
    config = {
        'filepath': "../assets/blender/test/hero.egg",
        'animations': {
            "walk": {
                "events":[['start', 0], ['middle', 40]],
                "rate": 3,
            },
            "pickup": {
                "events": [['pickup', 10], ['done', 20]],
                "rate": 3,
            },
            "idle": {
                'rate': 3.1,
            }
        },
        'default': 'idle',
    }

    ac = Animator(config, Handler())
    ac.get_actor_np().reparent_to(G.render)
    ac.play('idle', False)
    def up(task):
        ac.on_update()
        return task.cont
    def pickup():
        ac.play('pickup', True, 3)
    G.accept('space', pickup)
    G.taskMgr.add(up, 'xx')
    G.cam.set_pos(Vec3(10, 10, 3))
    G.cam.look_at(ac._actor_np)
    G.run()

if __name__ == '__main__':
    test()

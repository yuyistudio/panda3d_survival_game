#encoding: utf8

from panda3d.core import *
from variable.global_vars import G
import config

TOOL_ANIM_NAME = "tool"
TOOL_SUBPART = "tool_subpart"

class HitRecorder(object):
    def __init__(self):
        self.ready = False
        self.hit_names = set()

    def already_hit(self, name):
        if not self.ready:
            return True
        l1 = len(self.hit_names)
        self.hit_names.add(name)
        return len(self.hit_names) == l1

    def reset(self):
        self.ready = True
        self.hit_names.clear()

class ToolInfo(object):
    def __init__(self, tool_np, ghost_np):
        self.tool_np = tool_np
        self.ghost_np = ghost_np

class HeroTool(object):
    def __init__(self, hero):
        self.hero = hero
        G.accept("mouse1", self.useTool)
        G.accept("c", lambda: self.changeTool("sword"))
        G.accept("v", lambda: self.changeTool("axe"))


        self.tool_weight = 0
        self.target_tool_weight = 0
        self.tool_weight_lerp = 10

        self.hit_recorder = HitRecorder()

        self.name2tool = {}
        self.tool_names = 'sword axe'.split()
        for tool_name in self.tool_names:
            tool_np = G.loader.loadModel("assets/blender/%s" % tool_name)
            ghost_np = G.physics_world.addBoxTrigger(tool_np, config.BIT_MASK_TOOL)
            self.name2tool[tool_name] = ToolInfo(tool_np, ghost_np)
            G.physics_world.world.removeGhost(ghost_np.node())
        self.current_tool_name = "axe"
        self.changeTool("axe")

    def changeTool(self, tool_name):
        current_tool = self.getCurrentTool()
        G.physics_world.world.removeGhost(current_tool.ghost_np.node())
        current_tool.tool_np.detachNode()
        tool = self.name2tool.get(tool_name)
        assert(tool)
        G.physics_world.world.attachGhost(tool.ghost_np.node())
        weapon_slot = self.hero.anim_np.exposeJoint(None, "modelRoot", "weapon.r")
        tool.tool_np.reparentTo(weapon_slot)
        self.current_tool_name = tool_name

    def useTool(self):
        self.hit_recorder.reset()
        if self.target_tool_weight > 0.1:
            return
        self.hero._animator.play(TOOL_ANIM_NAME, once=True)
        self.target_tool_weight = 10

    def getCurrentTool(self):
        current_tool = self.name2tool.get(self.current_tool_name)
        return current_tool

    def _checkHit(self):
        if self.target_tool_weight < 1:
            return
        ghost = self.getCurrentTool().ghost_np.node()  # get_trigger_np().get_ghost_node()
        for node in ghost.getOverlappingNodes():
            physical_np = node.getPythonTag("instance")
            if not physical_np:
                continue
            name = physical_np.getName()
            if self.hit_recorder.already_hit(name):  # tool aren't being used OR has been used already
                return
            node.setLinearVelocity((physical_np.getPos() - self.hero.physics_np.getPos()).normalized() * 5)
            print 'hit:', name

    def on_update(self, dt):
        self._checkHit()


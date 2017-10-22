# encoding: utf8

__author__ = 'Leon'

from variable.global_vars import G
from operation import operation
from hero import create
from chunk import chunk_manager, test_map_generator
from craft_system import craft_manager
from objects import ground, lights, box
from panda3d.core import Vec3
import json


class GameManager(object):
    def __init__(self):
        self.hero = create.Hero()
        self.operation = operation.Operation(self.hero)
        self.craft_mgr = craft_manager.CraftManager()
        self.craft_mgr.register_recipes(json.loads(open('assets/json/recipes.json').read()))
        self.chunk_mgr = chunk_manager.ChunkManager(chunk_title_count=16, chunk_tile_size=2)
        self.chunk_mgr.set_generator(G.config_mgr.get_map_config('perlin')())
        self.chunk_mgr.set_tile_texture(G.config_mgr.get_tile_config('default'))
        self.chunk_mgr.set_spawner(G.spawner)

        self.current_slot = '1'
        self.current_scene = 'main_land'
        self.slot = G.storage_mgr.get_or_create_slot_entry(self.current_slot)
        self.slot.load()
        G.storage_mgr.save_slots_entry()
        self.scene = self.slot.get_or_create_scene_entry(self.current_scene)
        self.slot.save()
        self.chunk_mgr.set_storage_mgr(self.scene)

        self._ground = ground.create()  # TODO remove it
        self._lights = lights.create()  # TODO remove it

    def save_scene(self):
        self.slot.save()
        self.scene.save()

    def on_update(self, dt):
        self.hero.onUpdate(dt)
        pos = self.hero.getNP().getPos()
        self.chunk_mgr.on_update(pos.getX(), pos.getY(), dt)






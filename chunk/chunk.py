#encoding: utf8


import math
import logging
from panda3d.core import Vec3
from variable.global_vars import G
import sys
import config as gconf
from util import log
import random


class Tile(object):
    def __init__(self, r, c):
        self.objects = []
        self.r, self.c = r, c

    def destroy(self):
        for obj in self.objects:
            obj.destroy(True)


class Chunk(object):
    """
    1. 管理一堆Tiles和objects的个体；
    2. 管理这些Tiles和objects生成的geom和collider，并进行合并优化；
    """
    def __init__(self, mgr, base_x, base_y, tile_count, tile_size):
        self._mgr, self._bx, self._by, self._tc, self._ts = \
            mgr, base_x, base_y, tile_count, tile_size

        self._key = '%d_%d' % (base_x, base_y)
        r, c = self.xy2rc(base_x, base_y)
        self._tiles = []
        for i in range(tile_count):
            for j in range(tile_count):
                self._tiles.append(Tile(r + i, c + j))
        self._frozen_objects = []

        self._update_iterator = self._iterate_objects()
        self._iterator_dt = 0
        self._enabled = True
        self._ground_geom = None
        self._ground_data = None
        self._block_body = None  # 地图上不可到达区域的collider对应的body

        self._static_models = []
        self._root_np = None
        self._is_doing_flatten = False

        self._ground_items = []

    def add_ground_item(self, ground_item):
        self._ground_items.append(ground_item)

    def set_ground_geom(self, geom, data, block_body):
        self._ground_geom = geom
        self._ground_data = data
        self._block_body = block_body
        if block_body:
            G.physics_world.add_body(block_body)

    def get_ground_data(self):
        return self._ground_data

    def get_objects(self):
        objects = []
        for tile in self._tiles:
            objects.extend(tile.objects)
        return objects

    def get_objects_at_pos(self, x, y):
        r, c = self.xy2rc(x, y)
        tile = self.get_tile_at(r, c)
        if tile:
            result = [obj for obj in tile.objects if not obj.is_destroyed()]
            return result
        return []

    def get_tile_at(self, r, c):
        tile = self._tiles[r * self._tc + c]
        assert tile, 'rc (%s,%s) not in chunk range' % (r, c)
        return tile

    def add_object_to(self, obj, r, c):
        tile = self._tiles[r * self._tc + c]
        assert tile, 'rc (%s,%s) not in chunk range' % (r, c)
        self._on_new_object_added(tile, obj)

    def add_object(self, obj):
        pos = obj.get_pos()
        r, c = self.xy2rc(pos.getX(), pos.getY())
        assert self.rc_in_chunk(r, c), '%s , %s , %s,%s' % ((r, c), pos, self._bx, self._by)
        tile = self._tiles[r * self._tc + c]
        self._on_new_object_added(tile, obj)

    def _on_new_object_added(self, tile, new_obj):
        tile.objects.append(new_obj)
        self._static_models.extend(new_obj.get_static_models())

    def remove_entity(self, entity, is_static=True):
        """
        可以是静态或者动态的object
        :param entity:
        :return:
        """
        if is_static:
            # 移除entit引用
            pos = entity.get_pos()
            r, c = self.xy2rc(pos.getX(), pos.getY())
            assert self.rc_in_chunk(r, c), '%s , %s , %s,%s' % ((r, c), pos, self._bx, self._by)
            tile = self._tiles[r * self._tc + c]
            try:
                tile.objects.remove(entity)
            except Exception, e:
                log.debug("AAA %s %s %s", e, entity.get_pos(), r, c)
            # 重新获取静态模型
            for model in entity.get_static_models():
                self._static_models.remove(model)
        else:
            # 移除entit引用
            self._frozen_objects.remove(entity)

    def is_geom_flattened(self):
        return self._root_np

    def get_flatten_fn(self):
        if self._is_doing_flatten:
            """只flatten一次"""
            return None
        self._is_doing_flatten = True
        return self.__do_flatten_async

    def __do_flatten_async(self):
        if self._root_np:
            self._root_np.remove_node()
        self._root_np = G.render.attach_new_node('root_%s' % self._key)
        if self._static_models:
            for model in self._static_models:
                model.reparent_to(self._root_np)
            G.loader.asyncFlattenStrong(self._root_np, True)
        self._is_doing_flatten = False

    def xy2rc(self, x, y):
        """
        :param x: 世界坐标x
        :param y:
        :return: Chunk内坐标r/c
        """
        x -= self._bx
        y -= self._by
        return int(math.floor(y / self._ts)), int(math.floor(x / self._ts))

    def rc2xy(self, r, c):
        """
        :param r: Chunk内坐标r/c
        :param c:
        :return: 世界坐标x/y
        """
        return self._bx + c * self._ts, self._by + r * self._ts

    def rc_in_chunk(self, r, c):
        """
        :param r: Chunk内坐标r/c
        :param c:
        :return:
        """
        return 0 <= r < self._tc and 0 <= c < self._tc

    def xy_in_chunk(self, x, y):
        """
        :param x: Chunk内坐标x/y
        :param y:
        :return:
        """
        r, c = self.xy2rc(x, y)
        return 0 <= r < self._tc and 0 <= c < self._tc

    def on_load(self, spawner, data):
        self._ground_data = data['ground']
        for obj_data in data['objects']:
            obj = spawner.spawn_from_storage(obj_data)
            assert obj, 'invalid storage data: %s' % obj_data
            self.add_object(obj)

    def on_save(self):
        objects_data = []
        for tile in self._tiles:
            for obj in tile.objects:
                objects_data.append(obj.on_save())
        for obj in self._frozen_objects:
            objects_data.append(obj.on_save())
        return {
            'objects': objects_data,
            'ground' : self._ground_data,
        }

    def destroy(self):
        if self._ground_geom:
            self._ground_geom.remove_node()
        if self._root_np:
            self._root_np.remove_node()
        for tile in self._tiles:
            tile.destroy()
        self._tiles = None
        for obj in self._frozen_objects:
            obj.destroy(False)
        for item in self._ground_items:
            if not item.is_destroyed():
                item.destroy()
        self._frozen_objects = None

    def _iterate_objects(self):
        while True:
            # 每一帧更新一个Tile
            for tile in self._tiles:
                obj = None
                remained_objects = []
                for obj in tile.objects:
                    entity = obj
                    if entity.is_destroyed():
                        continue
                    entity.on_update(self._iterator_dt)
                    pos = entity.get_pos()
                    if self.xy_in_chunk(pos.getX(), pos.getY()):
                        remained_objects.append(obj)
                    else:
                        self._frozen_objects.append(obj)
                tile.objects = remained_objects
                del obj  # 每一帧中都确保没有对entity的多余引用
                yield

            # 更新所有的frozen_objects
            remained_objects = []
            frozen_obj = None
            for frozen_obj in self._frozen_objects:
                if frozen_obj.is_destroyed():
                    continue
                if not self._mgr.transfer_frozen_object(self, frozen_obj):
                    remained_objects.append(frozen_obj)
            self._frozen_objects = remained_objects
            del frozen_obj  # 每一帧中都确保没有对entity的多余引用
            yield

    def on_update(self, dt):
        if not self._enabled:
            return
        self._iterator_dt = dt
        self._update_iterator.next()

        # 更新所有的ground items
        remained_items = []
        for item in self._ground_items:
            if item.is_destroyed():
                continue
            item.on_update(dt)
            remained_items.append(item)
        self._ground_items = remained_items

    def set_enabled(self, enabled):
        assert self._root_np
        assert self._enabled != enabled
        self._enabled = enabled
        if enabled:
            if self._block_body:
                G.physics_world.add_body(self._block_body)
            if self._ground_geom:
                self._ground_geom.show()
            import time
            time.sleep(0.001)
            if self._root_np:
                self._root_np.show()
        else:
            if self._block_body:
                G.physics_world.remove_body(self._block_body)
            if self._ground_geom:
                self._ground_geom.hide()
            if self._root_np:
                self._root_np.hide()
        for obj in self._iter_all_objects():
            obj.set_enabled(enabled)

    def set_enabled_with_yield(self, enabled):
        self._enabled = enabled

        if enabled:
            if self._ground_geom:
                self._ground_geom.show()
            if self._root_np:
                self._root_np.show()
        else:
            if self._ground_geom:
                self._ground_geom.hide()
            if self._root_np:
                self._root_np.hide()
        yield
        for obj in self._iter_all_objects():
            obj.set_enabled(enabled)
            yield

    def _iter_all_objects(self):
        """
        遍历该chunk内的所有object。包括frozen_objects。
        :return:
        """
        for tile in self._tiles:
            for obj in tile.objects:
                yield obj
        for obj in self._frozen_objects:
            yield obj

    def maybe_messy_clear_objects(self):
        """
        删除该Chunk内的所有object.
        Warning：仅仅删除引用。
        :return:
        """
        for obj in self._frozen_objects:
            # 为什么是3：1、局部变量obj；2、self._frozen_objects；3、getrefcount(obj)的参数；
            assert sys.getrefcount(obj) == 3
        del self._frozen_objects[:]
        for tile in self._tiles:
            if tile.objects:
                assert sys.getrefcount(tile.objects[0]) == 2, \
                    'unexpected ref count: %d, obj: %s' % (sys.getrefcount(tile.objects[0]), tile.objects[0])
                del tile.objects[:]


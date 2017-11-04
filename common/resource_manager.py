# encoding: utf8


"""
管理texture static_model
"""

from variable.global_vars import G
from util import storage
from panda3d.core import Texture
import os


class ResourceManager(object):
    def __init__(self):
        self._models = {}
        self._textures = {}
        self._scenes = storage.load_json_file('assets/json/scenes.json')
        self._item_config = storage.load_json_file('assets/json/items.json')
        self._object_config = storage.load_json_file('assets/json/objects.json')
        assert self._scenes and self._item_config and self._object_config, (not self._scenes, not self._item_config, not self._object_config)

        # 载入item textures
        self._item_textures = {}

        for folder, filename in storage.iter_files('assets/images/items'):
            full_path = os.path.join(folder, filename)
            full_path = full_path.replace('\\', '/')
            used_texture = G.loader.loadTexture(full_path)
            used_texture.set_magfilter(Texture.FT_nearest)
            self._item_textures[full_path] = used_texture

    def get_static_model(self, filepath):
        model = self._models.get(filepath)
        if not model:
            model = G.loader.loadModel(filepath)
        return model

    def get_texture(self, filepath):
        texture = self._textures.get(filepath)
        if not texture:
            texture = G.loader.loadTexture(filepath)
            self._textures[filepath] = texture
        return texture

    def get_scene_config(self, scene_name):
        return self._scenes.get(scene_name)

    def get_object_config(self):
        return self._object_config

    def get_item_config(self):
        return self._item_config

    def get_item_config_by_name(self, item_name):
        return self._item_config.get(item_name)

    def get_item_texture(self, image_path):
        return self._item_textures.get(image_path)

    def get_item_texture_by_name(self, item_name):
        config = self.get_item_config_by_name(item_name)
        return self.get_item_texture(config['texture'])

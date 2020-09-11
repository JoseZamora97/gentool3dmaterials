from typing import List


class Environment:
    def __init__(self, dimension: int = 0):
        self.dimension = dimension


class Material:
    class Kind:
        STATIC_TEXTURE_AND_PARAMS = "static_static"
        STATIC_TEXTURE_DYNAMIC_PARAMS = "static_dynamic"
        DYNAMIC_TEXTURE_AND_PARAMS = "dynamic_dynamic"

    class Texture:
        RANDOM = "random"
        GOLD = "gold"
        MARBLE = "marble"
        CRYSTAL = "crystal"
        WOOD = "wood"

    def __init__(self,
                 kind: str = "",
                 texture: str = "",
                 metallic: float = .0,
                 specular: float = .0,
                 roughness: float = .0
                 ):
        self.kind = kind
        self.metallic = metallic
        self.specular = specular
        self.roughness = roughness
        self.texture = texture

    def static_texture_and_params(self,
                                  texture: str = "",
                                  metallic: float = .0,
                                  specular: float = .0,
                                  roughness: float = .0):
        self.kind = Material.Kind.STATIC_TEXTURE_AND_PARAMS

        self.texture = texture
        self.metallic = metallic
        self.specular = specular
        self.roughness = roughness

        return self

    def static_texture_dynamic_params(self, texture):
        self.kind = Material.Kind.STATIC_TEXTURE_DYNAMIC_PARAMS
        self.texture = texture

        return self

    def dynamic_texture_and_params(self):
        self.kind = Material.Kind.DYNAMIC_TEXTURE_AND_PARAMS
        self.texture = Material.Texture.RANDOM

        return self


class Object:
    def __init__(self,
                 name: str,
                 path: str,
                 material: Material,
                 normalize: bool = True):
        self.name = name
        self.path = path
        self.normalize = normalize
        self.material = material


class Light:
    class Kind:
        STATIC_LIGHT = "static"  # no se mueve, tiene un color fijo
        DYNAMIC_LIGHT = "dynamic"  # se mueve, tiene un color fijo
        RAINBOW_STATIC_LIGHT = "rainbow_static_light"  # no se mueve, cambia de color
        RAINBOW_DYNAMIC_LIGHT = "rainbow_dynamic_light"  # se mueve, cambia de color

    def __init__(self,
                 kind: str = "",
                 color: list = None,
                 location: list = None,
                 max_range: int = 0,
                 max_energy: int = 10
                 ):
        self.kind = kind
        self.color = color
        self.location = location
        self.max_range = max_range
        self.max_energy = max_energy

    def dynamic_light(self, color: list, max_range: int):
        assert len(color) == 3, "color must have lenght of 3"
        assert 0.0 <= color[0] <= 1.0, "r-channel must be between 0 and 1"
        assert 0.0 <= color[1] <= 1.0, "g-channel must be between 0 and 1"
        assert 0.0 <= color[2] <= 1.0, "b-channel must be between 0 and 1"

        self.color = color
        self.kind = self.Kind.DYNAMIC_LIGHT
        self.max_range = max_range
        return self

    def static_light(self, color: list, location: list):
        assert len(color) == 3, "color must have lenght of 3"
        assert 0.0 <= color[0] <= 1.0, "r-channel must be between 0 and 1"
        assert 0.0 <= color[1] <= 1.0, "g-channel must be between 0 and 1"
        assert 0.0 <= color[2] <= 1.0, "b-channel must be between 0 and 1"
        assert len(location) == 3, "location must have lenght of 3"

        self.color = color
        self.location = location
        self.kind = self.Kind.DYNAMIC_LIGHT
        return self

    def rainbow_static_light(self, location: list, max_energy: int):
        assert len(location) == 3, "location must have lenght of 3"

        self.kind = self.Kind.RAINBOW_STATIC_LIGHT
        self.location = location
        self.max_energy = max_energy
        return self

    def rainbow_dynamic_light(self, max_range: float, max_energy: int):
        self.kind = self.Kind.RAINBOW_DYNAMIC_LIGHT
        self.max_range = max_range
        self.max_energy = max_energy

        return self


class Viewpoint:
    class Kind:
        STATIC_CAMERA = "static_camera"
        DYNAMIC_CAMERA = "dynamic_camera"
        OBJECT_PATH = "object_path"

    def __init__(self, kind: str = "",
                 location: list = None,
                 amount: int = 0,
                 size: int = 0,
                 horizontal_divisions: int = 0,
                 vertical_divisions: int = 0,
                 max_range: int = 0
                 ):
        self.max_range = max_range
        self.location = location
        self.kind = kind
        self.amount = amount
        self.size = size
        self.vertical_divisions = vertical_divisions
        self.horizontal_divisions = horizontal_divisions

    def static_camera_viewpoint(self,
                                location: List,
                                amount: int):
        self.kind = self.Kind.STATIC_CAMERA
        self.location = location
        self.amount = amount

        return self

    def dynamic_camera_viewpoint(self, amount: int, max_range: int):
        self.kind = self.Kind.DYNAMIC_CAMERA
        self.amount = amount
        self.max_range = max_range

        return self

    def espheric_path_viewpoint(self,
                                size: int,
                                horizontal_divisions: int,
                                vertical_divisions: int):
        self.kind = self.Kind.OBJECT_PATH
        self.size = size
        self.horizontal_divisions = horizontal_divisions
        self.vertical_divisions = vertical_divisions

        return self


class Render:
    class Style:
        NORMAL = "normal"
        SILHOUETTE = "silhouette"
        TEXTURE_SEGMENTATION = "texture-segmentation"
        RAY_TRACED = "ray-traced"
        RASTERED = "rastered"

    def __init__(self, resolution_x: int, resolution_y: int, output_dir_path: str, styles: List[str]):
        self.resolution_x = resolution_x
        self.resolution_y = resolution_y
        self.output_dir_path = output_dir_path
        self.styles = styles

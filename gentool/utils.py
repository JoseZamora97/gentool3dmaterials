import os
import random
from typing import List
from mathutils import Matrix

import bmesh
import bpy

from .basics import Material, Object, Light, Viewpoint, Environment, Render
from .translator import DataGenFunctsInterface


class UtilsName:
    """
    Class for store names.
    """
    prefix = '3dGenTool'
    scene_name = f'{prefix}-Scene'
    viewpoints_name = f'{prefix}-Viewpoints'
    empty_name = f'{prefix}-Empty'
    camera_name = f'{prefix}-Camera'
    model_name = f'{prefix}-Model'
    light_name = f'{prefix}-Light'


class EnvironmentCreator:
    @staticmethod
    def create_environment(dimension: int):
        """
        Create a "scene" this means creates a cube which will contains the object
        that will be rendered.
        @param: dimension : Cube edge size.

        :return: a reference to the environment
        """
        mesh = bpy.data.meshes.new(UtilsName.scene_name)
        sc_object = bpy.data.objects.new(UtilsName.scene_name, mesh)

        # Hide this object on rendering process
        sc_object.hide_render = True
        # Viewport previsualization is 'WIRE'
        sc_object.display_type = 'WIRE'

        # Set a transparent material for viewport
        # rendering visualisation
        MaterialHandler.set_transparent(sc_object)

        view_layer = bpy.context.view_layer
        view_layer.active_layer_collection.collection.objects.link(sc_object)

        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=dimension)
        bm.to_mesh(mesh)
        bm.free()

        return sc_object  # reference to the scene created.


class ViewpointsCreator:
    @staticmethod
    def create_viewpoints(u_segments: int = 32, v_segments: int = 16, diameter: int = 1):
        """
        Create the mesh UV_sphere from params. These mesh vertexes will
        be used for set the camera and iterate over, for render from
        multiples places.
        @param: u_segments : horizontal segments shown.
        @param: v_segments : vertical segments shown.
        @param: diameter : sphere diameter.
        """
        mesh = bpy.data.meshes.new(UtilsName.viewpoints_name)
        vp_object = bpy.data.objects.new(UtilsName.viewpoints_name, mesh)

        # Hide this object on rendering process
        vp_object.hide_render = True
        # Viewport previsualization is 'WIRE'
        vp_object.display_type = 'WIRE'
        # Set a transparent material for viewport
        # rendering visualisation
        MaterialHandler.set_transparent(vp_object)

        view_layer = bpy.context.view_layer
        view_layer.active_layer_collection.collection.objects.link(vp_object)

        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=u_segments, v_segments=v_segments, diameter=diameter)
        bm.to_mesh(mesh)
        bm.free()

        return vp_object  # reference to the empty object created.

    @staticmethod
    def create_camera(location: tuple = (0, 0, 0)):
        """
        Create a camera at location.
        @param location donde estara posicionada
        """
        cam_data = bpy.data.cameras.new(name=UtilsName.camera_name)
        cam_object = bpy.data.objects.new(UtilsName.camera_name, object_data=cam_data)
        cam_object.location = location
        view_layer = bpy.context.view_layer
        view_layer.active_layer_collection.collection.objects.link(cam_object)

        bpy.data.scenes['Scene'].camera = cam_object  # camara por defecto de la escena llamada Scene

        return cam_object  # reference to the camera created.

    @staticmethod
    def create_empty(size):
        """
        Create an empty object. Usually used for being tracked by
        the camera instead of an usual object, this is helpful for
        apply rotations to the camera without rotate the principal
        object.
        @param: size : size of empty object.
        """
        empty_object = bpy.data.objects.new(UtilsName.empty_name, None)
        empty_object.empty_display_size = size
        empty_object.empty_display_type = 'PLAIN_AXES'
        view_layer = bpy.context.view_layer
        view_layer.active_layer_collection.collection.objects.link(empty_object)

        return empty_object  # reference to the empty object created.

    @staticmethod
    def camera_track_object(camera, targetobj):
        """
        Set a constraint to the camera to track a target object.
        Both camera and target are blender objects.
        @param: camera : camera
        @param: targetobj : object to get tracked by the camera
        """
        camerac = camera.constraints.new(type='TRACK_TO')
        camerac.target = targetobj
        camerac.track_axis = 'TRACK_NEGATIVE_Z'
        camerac.up_axis = 'UP_Y'

        return camerac  # reference to the camera constraints created.


class LightCreator:
    @staticmethod
    def create_light(kind: str, color: tuple, location: tuple, energy: int) -> object:
        """
        Create a blender light source in the scene.
        @param: kind: 'POINT' or 'SUN'.
        @param: color: light color.
        @param: location: light location.
        @param: range_position: max & min range to generate randoms locations.
        """
        
        light_data = bpy.data.lights.new(name=UtilsName.light_name, type=kind)
        light_object = bpy.data.objects.new(name=UtilsName.light_name, object_data=light_data)
        
        light_object.location = location
        light_data.color = color
        light_data.energy = 1000

        view_layer = bpy.context.view_layer
        view_layer.active_layer_collection.collection.objects.link(light_object)

        return light_object  # reference to the light created.


def compute_translation(vmin, vmax, respect_to=0.0):
    c = (vmin + vmax) / 2
    d = respect_to - c
    return round(d, 2)


def get_min_max(o, respect_to: tuple = (0, 0, 0)):
    maxx = minx = miny = maxy = maxz = minz = 0
    for v in o.data.vertices:
        maxx = max(v.co.x, maxx)
        minx = min(v.co.x, minx)
        maxy = max(v.co.y, maxy)
        miny = min(v.co.y, miny)
        maxz = max(v.co.z, maxz)
        minz = min(v.co.z, minz)
    
    # Saber el mayor.
    x = compute_translation(minx, maxx, respect_to=respect_to[0])
    y = compute_translation(miny, maxy, respect_to=respect_to[1])
    z = compute_translation(minz, maxz, respect_to=respect_to[2])

    return x, y, z


class ObjectNormalizer:
    @staticmethod
    def scale_object(obj, max_dimension: float):
        scale_factor = max_dimension / max(obj.dimensions)
        obj.scale = (scale_factor, scale_factor, scale_factor)

    @staticmethod
    def translate_object(obj, to: tuple = (.0,.0,.0), tolerance=1): 
        coords = coords_prev = None
        counter = 0
        
        while coords != to and counter < tolerance:
            coords = get_min_max(obj, respect_to=to)
            
            if (coords == coords_prev):
                counter += 1
                continue
            
            coords_prev = coords
            bpy.ops.transform.transform(mode='TRANSLATION', value=(*coords, 0.0))
            obj.data.transform(obj.matrix_world)
            obj.matrix_world = Matrix()

class ObjectIO:
    extensions_allowed = {'.obj': bpy.ops.import_scene.obj}

    @staticmethod
    def load(path: str, scene_dimension: int, normalize: bool) -> tuple:
        """
        Load a file or directory from path and scale to fit the scene or
        downscale the model depending of params.
        @param: path : folder path.
        """
        assert os.path.exists(path), "Not such file or directory!"
        _, extension = os.path.splitext(path)
        assert extension in ObjectIO.extensions_allowed, f"No extension allowed. Only {ObjectIO.extensions_allowed} are " \
                                                       f"supported for now. "
        
        ObjectIO.extensions_allowed.get(extension)(filepath=path, use_smooth_groups=True)
        obj = bpy.context.selected_objects[0]
        obj.name = f"{UtilsName.model_name}-{os.path.basename(path)}"
        obj.data.transform(obj.matrix_world)
        obj.matrix_world = Matrix()

        if normalize:  # Apply model fitting
            ObjectNormalizer.scale_object(obj, scene_dimension)
            ObjectNormalizer.translate_object(obj, to=(0, 0, 0))

        return obj

    @staticmethod
    def export(path: str):
        bpy.ops.object.select_all(action='DESELECT')
        for ob in bpy.data.objects:
            if UtilsName.model_name in ob.name:
                ob.select_set(True)

        bpy.ops.export_scene.obj(filepath=path, use_materials=False)

class Cleaner:
    @staticmethod
    def clear_scene():
        objs = bpy.data.objects
        for obj in objs:
            print(f"Deleted object: type={obj.type}, name={obj.name}")
            objs.remove(obj, do_unlink=True)

class RenderHandler:
    IMG_FORMAT = 'PNG'
    ENGINE_CYCLES = 'CYCLES'
    ENGINE_EEVEE = 'BLENDER_EEVEE'

    @staticmethod
    def set_render_output_resolution(res_x: int, res_y: int, res_percentage: int = 100) -> None:
        """
        Set render output resolution
        @param: res_x : width resolution.
        @param: res_y : height resolution.
        @param: res_percentage : percentage resolution.
        """
        scene = bpy.context.scene
        scene.render.resolution_x = res_x
        scene.render.resolution_y = res_y
        scene.render.resolution_percentage = res_percentage

    @staticmethod
    def set_cycles(transparent: bool, samples: int):
        """
        Set cycles paramethers.
        @param transparent background transparency ?
        @param samples the amount of samples at rendering
        """
        scene = bpy.context.scene
        scene.render.engine = RenderHandler.ENGINE_CYCLES
        # The samples to preview are 10
        scene.cycles.preview_samples = 10
        # Samples for rendering
        scene.cycles.samples = samples
        scene.render.film_transparent = transparent  # background -> transparent
        bpy.context.scene.render.image_settings.file_format = RenderHandler.IMG_FORMAT
        bpy.context.scene.cycles.device = 'GPU'

    @staticmethod
    def render(path: str, engine: str, samples: int):
        bpy.context.scene.render.filepath = path
        if engine == RenderHandler.ENGINE_CYCLES:
            RenderHandler.set_cycles(transparent=True, samples=samples)
        else:
            bpy.context.scene.render.engine = RenderHandler.ENGINE_EEVEE
        bpy.ops.render.render(use_viewport=True, write_still=True)


class LightEffect:
    """
    This class creates a global illumination
    and change rendering parameters to preview the 3D model
    """

    @staticmethod
    def global_illumination():
        """
        This function creates a global lighting "world" and assigns it as the main one,
        among its capabilities adds an hdri image as global illumination.
        Configures "cycles" as the main engine,10 samples and transparent background
        If the world and the configuration exists, it does not recreate it
        """
        pass
        scene = bpy.context.scene
        if scene.world.name != "gentool3dmultiview":
            # path a ti hdri
            path_hdri = "//assets/HDRIsunBeach.exr"
            new_world = bpy.data.worlds.new("gentool3dmultiview")
            new_world.use_nodes = True
            scene.world = new_world
            shader_node_tex_environment = scene.world.node_tree.nodes.new("ShaderNodeTexEnvironment")
            shader_node_tex_environment.image = bpy.data.images.load(path_hdri)
            node_tree = scene.world.node_tree
            node_tree.links.new(
                shader_node_tex_environment.outputs['Color'], node_tree.nodes['Background'].inputs['Color']
            )
            scene.world.node_tree.nodes["Background"].inputs[1].default_value = 2

    @staticmethod
    def create_shadeless_world(name="MundoTransparente", color=(0, 0, 0, 1)):
        """
        This function creates a global lighting "world" and assigns it as the main one,
        among its capabilities adds an hdri image as global illumination.
        Configures "cycles" as the main engine,10 samples and transparent background
        If the world and the configuration exists, it does not recreate it
        @param color: background color
        @param name: world name
        """
        scene = bpy.context.scene
        if scene.world.name != name:
            new_world = bpy.data.worlds.new(name)
            new_world.use_nodes = True
            scene.world = new_world
            node_tree = scene.world.node_tree
            node_tree.nodes["Background"].inputs[0].default_value = color  # background color


class MaterialHandler:
    """
    This class handles the materials.
    """
    TRASNPARENT = "transparent"

    SHADE = 'shadeless'
    SILHOUETTE = 'silhouette'

    MATERIALS = {
        SILHOUETTE: "silueta",
        Material.Texture.MARBLE: "marmol",
        Material.Texture.CRYSTAL: "vidrio",
        Material.Texture.WOOD: "madera",
        Material.Texture.GOLD: "oro",
        f"{Material.Texture.MARBLE}_{SHADE}": "marmolSinSombras",
        f"{Material.Texture.CRYSTAL}_{SHADE}": "vidrioSinSombras",
        f"{Material.Texture.WOOD}_{SHADE}": "maderaSinSombras",
        f"{Material.Texture.GOLD}_{SHADE}": "oroSinSombras"
    }

    COLORS_SHADELESS = {
        SILHOUETTE: (0, 0, 0, 1),
        f"{Material.Texture.MARBLE}_{SHADE}": (0.262, 0.262, 0.262, 1),
        f"{Material.Texture.CRYSTAL}_{SHADE}": (0.262, 0.014, 0.064, 1),
        f"{Material.Texture.WOOD}_{SHADE}": (0.262, 0.112, 0.08, 1),
        f"{Material.Texture.GOLD}_{SHADE}": (0.8, 0.44, 0.02, 1)
    }
    
    TEXTURES = {
        Material.Texture.MARBLE: "marmol",
        Material.Texture.CRYSTAL: "vidrio",
        Material.Texture.WOOD: "madera",
        Material.Texture.GOLD: "oro",
    }

    @staticmethod
    def change_shadeless_material_color(model, color: tuple = (0, 0, 0, 0)):
        model.active_material.node_tree.nodes["Emission"].inputs[0].default_value = color

    @staticmethod
    def set_transparent(model):
        """
        Set a model a transparent material for hiding it at render time
        @param model the model
        """
        mat = bpy.data.materials.get(MaterialHandler.TRASNPARENT)
        if mat is None:
            mat = bpy.data.materials.new(MaterialHandler.TRASNPARENT)
            mat.use_nodes = True
            node_tree = mat.node_tree
            nodes = node_tree.nodes
            bsdf = nodes.get("Principled BSDF")
            bsdf.inputs[18].default_value = 0  # alpha valor 0

        if model.data.materials:  # add if slots availables
            model.data.materials[0] = mat  # assign to 1st material slot
        else:  # no slots
            model.data.materials.append(mat)  # agrega el material

    @staticmethod
    def load_material(material_name: str, path="//assets/materiales.blend"):  # carga el material de oro
        """
        Loads a ".blend" file with contains the materials.
        @param material_name material name to import
        @param path materials location file
        """
        with bpy.data.libraries.load(path) as (_, data_to):
            data_to.materials = [material_name]
            return data_to.materials  # this could be empty

    @staticmethod
    def _create_material(material_name, model, apply_light):  # metodo privado por convención
        """
        This function create and apply a material, avoiding replications.
        @param material_name Nombre de material
        @param model 3D object to apply the material
        @param apply_light function for light aplications.
        """
        materials = bpy.data.materials
        for i in materials:
            if i.name == material_name:
                model.active_material = i
                apply_light()
                return

        materials = MaterialHandler.load_material(material_name=material_name)

        for i in materials:
            model.active_material = i

        apply_light()


    @staticmethod
    def apply_material_to(model, material: str, apply_light: callable):
        assert material in MaterialHandler.MATERIALS, "MaterialHandler not allowed!"
        MaterialHandler._create_material(
            material_name=MaterialHandler.MATERIALS.get(material), 
            model=model, 
            apply_light=apply_light
        )

    @staticmethod
    def modify_material_properties(model, metalic, specular, roughness):
        """
        Accens to the "Principled bsdf" of the model an change his params.
        """
        model.active_material.node_tree.nodes["Principled BSDF"].inputs[4].default_value = metalic
        model.active_material.node_tree.nodes["Principled BSDF"].inputs[5].default_value = specular
        model.active_material.node_tree.nodes["Principled BSDF"].inputs[7].default_value = roughness

    @staticmethod
    def clear_material(model):
        LightEffect.global_illumination()
        # Create a transparent world
        model.data.materials.clear()


def create_random_3_tuple(min_value, max_value):
    return (
        random.uniform(min_value, max_value),
        random.uniform(min_value, max_value),
        random.uniform(min_value, max_value)
    )

class DataGenApplyFuncts(DataGenFunctsInterface):

    def set_render_resolution(self, r: Render):
        RenderHandler.set_render_output_resolution(
            res_x=r.resolution_x,
            res_y=r.resolution_y,
            res_percentage=100
        )

    def render(self, path: str, render_style: str, texture: str, object_loaded):
        
        if render_style == Render.Style.NORMAL:
            MaterialHandler.clear_material(object_loaded)
            RenderHandler.render(
                path=os.path.join(path, f"{Render.Style.NORMAL}.{RenderHandler.IMG_FORMAT}"),
                engine=RenderHandler.ENGINE_EEVEE,
                samples=100
            )

        elif render_style == Render.Style.SILHOUETTE:
            MaterialHandler.apply_material_to(
                model=object_loaded,
                material=MaterialHandler.SILHOUETTE,
                apply_light=LightEffect.create_shadeless_world
            )
            MaterialHandler.change_shadeless_material_color(
                object_loaded,
                color=MaterialHandler.COLORS_SHADELESS.get(MaterialHandler.SILHOUETTE)
            )
            RenderHandler.render(
                os.path.join(path, f"{Render.Style.SILHOUETTE}.{RenderHandler.IMG_FORMAT}"),
                engine=RenderHandler.ENGINE_EEVEE,
                samples=100
            )

        elif render_style == Render.Style.TEXTURE_SEGMENTATION:
            MaterialHandler.apply_material_to(
                model=object_loaded,
                material=f"{texture}_{MaterialHandler.SHADE}",
                apply_light=LightEffect.create_shadeless_world
            )
            MaterialHandler.change_shadeless_material_color(
                object_loaded,
                color=MaterialHandler.COLORS_SHADELESS.get(f"{texture}_{MaterialHandler.SHADE}")
            )
            RenderHandler.render(
                os.path.join(path, f"{Render.Style.TEXTURE_SEGMENTATION}.{RenderHandler.IMG_FORMAT}"),
                engine=RenderHandler.ENGINE_EEVEE,
                samples=100
            )

        elif render_style == Render.Style.RAY_TRACED:
            MaterialHandler.apply_material_to(
                model=object_loaded,
                material=texture,
                apply_light=LightEffect.global_illumination
            )
            # MaterialHandler.modify_material_properties(
            #     model=object_loaded,
            #     metalic=o.material.metallic,
            #     specular=o.material.specular,
            #     roughness=o.material.roughness
            # )
            RenderHandler.render(
                os.path.join(path, f"{Render.Style.RAY_TRACED}.{RenderHandler.IMG_FORMAT}"),
                engine=RenderHandler.ENGINE_CYCLES,
                samples=128
            ) 

        elif render_style == Render.Style.RASTERED:
            MaterialHandler.apply_material_to(
                model=object_loaded,
                material=texture,
                apply_light=LightEffect.global_illumination
            )
            RenderHandler.render(
                os.path.join(path, f"{Render.Style.RASTERED}.{RenderHandler.IMG_FORMAT}"),
                engine=RenderHandler.ENGINE_EEVEE,
                samples=100
            )

        else:
            pass

        MaterialHandler.clear_material(object_loaded)


    def define_texture(self, o: Object):
        if o.material.texture == Material.Texture.RANDOM:
            return random.sample(MaterialHandler.TEXTURES.keys(), 1)[0]
        return o.material.texture

    def create_environment(self, e: Environment):
        env = EnvironmentCreator.create_environment(
            e.dimension
        )
        return env

    def create_viewpoints(self, vs: List[Viewpoint], preview: bool):
        viewpoints_created = list()

        for v in vs:
            if v.kind == Viewpoint.Kind.STATIC_CAMERA:
                location = tuple(v.location)  # create an inmutable object.
                viewpoints_created.append([location] * v.amount)  # repeate it for memory saving

            elif v.kind == Viewpoint.Kind.DYNAMIC_CAMERA:
                viewpoints_created.append([  # append randoms 3-tuples.
                    create_random_3_tuple(0 - v.max_range, v.max_range) for _ in range(v.amount)
                ])

            elif v.kind == Viewpoint.Kind.OBJECT_PATH:
                # Create the blender UV_sphere.
                viewpoint_object = ViewpointsCreator.create_viewpoints(
                    u_segments=v.horizontal_divisions,
                    v_segments=v.vertical_divisions,
                    diameter=v.size
                )
                # Get vertices as locations.
                viewpoints_created.append(
                    [(vert.co.x, vert.co.y, vert.co.z) for vert in viewpoint_object.data.vertices]
                )
                # Remove it for memory saving
                bpy.data.objects.remove(viewpoint_object, do_unlink=True)
            else:
                continue

        return viewpoints_created if not preview else [[viewpoints_created[0][0], ], ]

    def create_light(self, li: Light):
        if li.kind == Light.Kind.STATIC_LIGHT:
            return LightCreator.create_light(kind='POINT', color=tuple(li.color),
                location=tuple(li.location), energy=li.max_energy)

        if li.kind == Light.Kind.DYNAMIC_LIGHT:
            return LightCreator.create_light(kind='POINT', color=tuple(li.color),
                                        location=create_random_3_tuple(0 - li.max_range, li.max_range),
                                        energy=random.uniform(0, li.max_energy))

        if li.kind == Light.Kind.RAINBOW_STATIC_LIGHT:
            return LightCreator.create_light(kind='POINT', color=create_random_3_tuple(0, 1),
                                        location=create_random_3_tuple(0 - li.max_range, li.max_range),
                                        energy=li.max_energy)

        if li.kind == Light.Kind.RAINBOW_DYNAMIC_LIGHT:
            return LightCreator.create_light(kind='POINT', color=create_random_3_tuple(0, 1),
                                        location=create_random_3_tuple(0 - li.max_range, li.max_range),
                                        energy=random.uniform(0, li.max_energy))
    
    def get_light_params(self, light):
        return [*light.location.xyz, light.data.energy]

    def load_object(self, o: Object, size_env: int):
        obj = ObjectIO.load(
            o.path, scene_dimension=size_env, normalize=o.normalize
        )
        return obj

    def create_camera(self):
        camera = ViewpointsCreator.create_camera()
        empty = ViewpointsCreator.create_empty(size=2)
        ViewpointsCreator.camera_track_object(camera=camera, targetobj=empty)

        return camera

    def move_camara_to(self, camera, coords):
        camera.location.xyz = coords

    def clear_lights(self):
        for li in bpy.data.objects:
            if li.type == 'LIGHT':
                bpy.data.objects.remove(li, do_unlink=True)
              
    def export_normalized_object(self, path):
        ObjectIO.export(path=path)

    def clear_objects(self):
        Cleaner.clear_scene()

class Message:
    @staticmethod
    def show(title="", message="", icon='INFO'):
        """
        Show a message box
        muestra un mensaje dentro de una caja en blender3D. Tiene 3 parametros
        @params: title : the message title
        @params: message : the message.
        @params: icon : the icon of the message.
        """

        def draw(self, _):
            self.layout.label(text=message)
            print(icon, title, message)

        bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

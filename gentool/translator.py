import json
import os
import webbrowser
import csv

from threading import Thread
from typing import Dict, List

from .basics import Environment, Object, Light, Viewpoint, Render, Material


def process(o: Object) -> Dict:
    o.material = o.material.__dict__
    return o.__dict__


def reconstruct(o: Dict) -> Object:
    mat = Material(**(o.get('material')))
    o.update({'material': mat})
    return Object(**o)


class Config:
    def __init__(self,
                 environment: Environment,
                 render: Render,
                 objects: List[Object],
                 lights: List[Light],
                 viewpoints: List[Viewpoint]):
        assert environment is not None, "environment cant be None!"
        assert render is not None, "render cant be None!"
        assert objects != [], "objects is empty!"
        assert lights != [], "lights is empty!"
        assert viewpoints != [], "viewpoints is empty!"
        assert render.output_dir_path != "", "Output directory path not specified!"

        self.environment = environment
        self.objects = objects
        self.lights = lights
        self.viewpoints = viewpoints
        self.render = render


class ConfigIO:
    @staticmethod
    def json_dumps(instance: Config, path: str):
        config = {
            "environment": instance.environment.__dict__,
            "objects": [process(obj) for obj in instance.objects],
            "lights": [light.__dict__ for light in instance.lights],
            "viewpoints": [viewpoint.__dict__ for viewpoint in instance.viewpoints],
            "render": instance.render.__dict__
        }

        if path is not None:
            with open(path, "w") as fw:
                fw.write(json.dumps(config, indent=4, sort_keys=True))

        print(config)

    @staticmethod
    def json_loads(path: str):
        with open(path, "r") as fr:
            config = json.load(fr)

        config = {
            "environment": Environment(**config.get("environment")),
            "objects": [reconstruct(o) for o in config.get("objects")],
            "lights": [Light(**li) for li in config.get("lights")],
            "viewpoints": [Viewpoint(**v) for v in config.get("viewpoints")],
            "render": Render(**config.get("render"))
        }

        return Config(**config)


class DataGenFunctsInterface:

    def create_environment(self, e: Environment):
        """
        Creates an evironment for object normalicing
        :param e: the Environment
        :return:
        """
        pass

    def create_viewpoints(self, vs: List[Viewpoint], preview: bool):
        """
        Create the viewpoints of the camera
        :param vs: a list of Viewpoints objects.
        :param preview: if true, returns only 1 coord.
        :return:
        """
        pass

    def create_light(self, li: Light):
        """
        Create a light based on params of light
        :param li: Light
        :return: None
        """
        pass

    def load_object(self, o: Object, size_env: int):
        """
        Load an object into scene
        :param o: the object
        :param size_env: the size of the scene
        :return: reference to the object.
        """
        pass

    def create_camera(self):
        """
        This method creates a camera
        :return: reference to the camera.
        """
        pass

    def move_camara_to(self, camera, coords):
        """
        This move a camara to an specified coordinations
        :param camera: the camera
        :param coords: coordinates.
        :return:
        """
        pass

    def render(self, path: str, render_style: str, texture: str, object_loaded):
        """
        This method renders the image based on input render style.
        This should be one of RenderManager.Kind variables.
        :param path: to save the render
        :param render_style: Style to apply.
        :param object_loaded: Object to apply the style.
        :param texture: object texture
        :return: None
        """
        pass

    def clear_lights(self):
        """
        This method should remove all lights.
        """
        pass
    
    def load_material(self, object_loaded, material: Material):
        """
        This method loads all the materials.
        :param object_loaded: Object to apply the material.
        :param material: Material to apply.
        """
        pass

    def set_render_resolution(self, r: Render):
        """
        This method allows to change the render resolution.
        :param r: Render config params.
        """
        pass

    def define_texture(self, o: Object):
        """
        This method returns a texture to show in the object.
        :param o: Object config params
        """
        pass
    
    def get_light_params(self, light: Light):
        """
        Returns light location and color
        :param light: Light config params
        """
        pass
    
    def export_normalized_object(self, path):
        """
        Save the object normalized.
        :param path: output params.
        """
        pass
    
    def clear_objects(self):
        """
        Clear the scene objects.
        """
        pass

class DatasetsGenerator(Thread):
    def __init__(self, config: Config, functs: DataGenFunctsInterface, preview: bool):
        super(DatasetsGenerator, self).__init__()

        self.config = config
        self.functs = functs
        self.preview = preview

    def run(self):
        
        # self.functs.create_environment(self.config.environment)

        for obj in self.config.objects:
            
            camera = self.functs.create_camera()
            viewpoints = self.functs.create_viewpoints(self.config.viewpoints, self.preview)
            
            # Load the object and store the reference.
            object_loaded = self.functs.load_object(obj, size_env=self.config.environment.dimension)
            object_loaded.select_set(True)

            obj_path = os.path.join(self.config.render.output_dir_path, obj.name)
            
            # Create an object folder
            os.makedirs(obj_path)
           
            # Export normalized object
            if obj.normalize:
                self.functs.export_normalized_object(path=os.path.join(obj_path, f"{obj.name}_normalized.obj"))
            
            # Create the headers for saving lights in csv. 
            lights_list = [
                (f"light_{i}-x", f"light_{i}-y", f"light_{i}-z", f"light_{i}_e")
                for i, _ in enumerate(self.config.lights)
            ]
            lights_list = [item for sublist in lights_list for item in sublist]
            
            # Create the csv headers.
            data_csv_list = [
                ['index', 'view-x', 'view-y', 'view-z', 'texture'],
            ]
            
            index = 0
            
            # Iterate over viewpoint
            for viewpoint in viewpoints:
                
                # Iterate over each viewpoint coordinate tuple (x, y, z)
                for coords in viewpoint:
                    
                    data_csv_list_item = [index, *coords]
                    
                    # Move the camera to the coordinates
                    self.functs.move_camara_to(camera, coords)
                    
                    # Create the lights
                    for light in self.config.lights:
                        li = self.functs.create_light(light)
                        # data_csv_list_item += self.functs.get_light_params(li)
                    
                    # Create the folder for saving the model renders.
                    path_render_index = os.path.join(obj_path, f"{index}")
                    os.makedirs(path_render_index)
                    
                    # Set the render configurations to render the diferent styles.
                    self.functs.set_render_resolution(self.config.render)
                    
                    texture = self.functs.define_texture(obj)
                    data_csv_list_item += [texture]
                    
                    for render_style in self.config.render.styles:
                        self.functs.render(
                            path=path_render_index,
                            render_style=render_style,
                            texture=texture,
                            object_loaded=object_loaded
                        )

                    # Clear the lights
                    self.functs.clear_lights()
                    # Append the new row for csv saving.
                    data_csv_list.append(data_csv_list_item)
                    index += 1

                # Todo: make UI progress bar.
            csv_path = os.path.join(obj_path, f"{obj.name}.csv")
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(data_csv_list)
            
            self.functs.clear_objects()

        # Open output folder to see the results.
        webbrowser.open('file:///' + os.path.abspath(self.config.render.output_dir_path))

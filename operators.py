from bpy.types import Operator

from .gentool.basics import Environment, Object, Material, Viewpoint, Render, Light
from .gentool.translator import ConfigIO, DatasetsGenerator, Config
from .gentool.utils import (Cleaner, DataGenApplyFuncts, Message)


class OperatorsEnd:
    FINISHED = "FINISHED"
    RUNNING_MODAL = "RUNNING_MODAL"
    CANCELLED = "CANCELLED"
    PASS_THROUGH = "PASS_THROUGH"
    INTERFACE = "INTERFACE"


def create_config_from_gui(properties):
    e = Environment(dimension=properties.scene_dimension)
    m = Material(
        kind=properties.material_kind,
        texture=properties.choice_material
        # metallic=properties.metallic,
        # specular=properties.specular,
        # roughness=properties.roughness
    )
    o = Object(
        name='sample',
        path=properties.input_model,
        material=m,
        normalize=properties.normalize
    )
    v = Viewpoint(
        kind=properties.camera_kind,
        location=properties.camera_location,
        amount=properties.amount_shoots,
        size=properties.camera_size,
        horizontal_divisions=properties.camera_h_segments,
        vertical_divisions=properties.camera_v_segments,
        max_range=properties.camera_range_location
    )

    i = Light(
        # kind=properties.light_kind,
        # color=properties.light_color,
        # location=properties.light_location,
        # max_range=properties.light_range_location,
        # max_energy=properties.max_energy
    )

    styles = []
    if properties.style_normal:
        styles.append(Render.Style.NORMAL)
    if properties.style_silhouette:
        styles.append(Render.Style.SILHOUETTE)
    if properties.style_silhouette_colored:
        styles.append(Render.Style.TEXTURE_SEGMENTATION)
    if properties.style_ray_traced:
        styles.append(Render.Style.RAY_TRACED)
    if properties.style_rastered:
        styles.append(Render.Style.RASTERED)

    r = Render(
        resolution_x=properties.render_resolution_x,
        resolution_y=properties.render_resolution_y,
        output_dir_path=properties.render_output_folder_path,
        styles=styles
    )

    return Config(environment=e, render=r, objects=[o], lights=[i], viewpoints=[v])


def generate_renders(config: Config, preview: bool):
    dataset_generator = DatasetsGenerator(
        config=config,
        functs=DataGenApplyFuncts(),
        preview=preview
    )

    dataset_generator.setName('Dataset-Generator')
    dataset_generator.run()


class OP_OT_GenerateScene(Operator):
    """
    This class shows to the user the created objects where all generation
    will proceed.
    """
    bl_label = "Render a Sample"
    bl_idname = "object.generate_scene"

    def execute(self, context):
        try:
            config = create_config_from_gui(context.scene.tool)
            generate_renders(config, preview=True)
            Message.show(
                title="Information",
                message="Rendering the preview",
                icon='INFO'
            )
        except Exception as e:
            Cleaner.clear_scene()
            Message.show(
                title="Operation Canceled",
                message=str(e),
                icon='ERROR'
            )

            return {OperatorsEnd.CANCELLED}
        return {OperatorsEnd.FINISHED}


class OP_OT_ClearScene(Operator):
    """
    Clear the scene.
    """
    bl_label = "Clear Scene"
    bl_idname = "object.clear_scene"

    def execute(self, _):
        Cleaner.clear_scene()
        return {OperatorsEnd.FINISHED}


class OP_OT_GenerateDataset(Operator):
    bl_label = "Generate"
    bl_idname = "object.generate_dataset"
    bl_options = {'REGISTER'}

    def execute(self, context):
        tool = context.scene.tool
        input_path = tool.input_presets_file

        config = ConfigIO.json_loads(input_path) if tool.choice_render == 'FILE' \
            else create_config_from_gui(tool)
        generate_renders(config, preview=False)

        return {OperatorsEnd.FINISHED}

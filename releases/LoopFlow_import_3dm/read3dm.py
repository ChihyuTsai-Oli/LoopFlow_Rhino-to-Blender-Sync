# [read3dm.py full source]

import os.path
import bpy
import sys
import os
from pathlib import Path
from typing import Any, Dict, Set

def modules_path():
    addon_dir = os.path.dirname(os.path.realpath(__file__))
    if addon_dir not in sys.path:
        sys.path.insert(1, addon_dir)
    return addon_dir

modules_path()

import rhino3dm as r3d
from . import converters

def create_or_get_top_layer(context, filepath):
    top_collection_name = Path(filepath).stem
    if top_collection_name in context.blend_data.collections:
        toplayer = context.blend_data.collections[top_collection_name]
        def delete_collection_hierarchy(col):
            for child in col.children: delete_collection_hierarchy(child)
            for obj in col.objects:
                data = obj.data
                bpy.data.objects.remove(obj, do_unlink=True)
                if data and data.users == 0:
                    if isinstance(data, bpy.types.Mesh): bpy.data.meshes.remove(data)
                    elif isinstance(data, bpy.types.Curve): bpy.data.curves.remove(data)
            if col.name != top_collection_name: bpy.data.collections.remove(col)
        delete_collection_hierarchy(toplayer)
    else:
        toplayer = context.blend_data.collections.new(name=top_collection_name)
    return toplayer

def read_3dm(context : bpy.types.Context, options : Dict[str, Any]) -> Set[str]:
    converters.initialize(context)
    filepath : str = options.get("filepath", "")
    try:
        model = r3d.File3dm.Read(filepath)
    except:
        return {'CANCELLED'}

    options["rh_model"] = model
    toplayer = create_or_get_top_layer(context, filepath)
    converters.utils.reset_all_dict(context)
    
    scale = r3d.UnitSystem.UnitScale(model.Settings.ModelUnitSystem, r3d.UnitSystem.Meters) / context.scene.unit_settings.scale_length
    layerids, materials = {}, {}

    # User's original option (determines whether to overwrite node trees)
    update_mats_flag = options.get("update_materials", False)

    # 1. Run material sync (material.py is written to skip node overwriting when flag=False and nodes already exist)
    converters.handle_materials(context, model, materials, update_mats_flag)
    converters.handle_layers(context, model, toplayer, layerids, materials, update_mats_flag, True)

    # 2. Force-enable material linking
    # Ensures newly imported geometry is correctly linked to the preserved, edited material even when [X] is used
    link_options = options.copy()
    link_options["update_materials"] = True 

    for ob in model.Objects:
        og = ob.Geometry
        attr = ob.Attributes
        rhinolayer = model.Layers.FindIndex(attr.LayerIndex)
        
        object_name = attr.Name if attr.Name else f"{str(og.ObjectType).split('.')[1]} {str(attr.Id)}"
        
        # Get material name
        mat_index = attr.MaterialIndex
        if attr.MaterialSource == r3d.ObjectMaterialSource.MaterialFromLayer:
            mat_index = rhinolayer.RenderMaterialIndex
        
        rhino_material = model.Materials.FindIndex(mat_index)
        if rhino_material:
            matname = rhino_material.Name
        else:
            matname = converters.material.DEFAULT_RHINO_MATERIAL

        view_color = rhinolayer.Color if attr.ColorSource == r3d.ObjectColorSource.ColorFromLayer else attr.ObjectColor
        
        # Look up the material in the mapping table (may be a renamed/preserved existing material)
        blmat = materials.get(matname, materials[converters.material.DEFAULT_RHINO_MATERIAL])
        
        layer = layerids[str(rhinolayer.Id)][1]
        
        # Convert geometry and pass in the forced-link flag
        converters.convert_object(context, ob, object_name, layer, blmat, view_color, scale, link_options)

    if toplayer.name not in context.scene.collection.children:
        context.scene.collection.children.link(toplayer)

    with context.temp_override(selected_editable_objects=toplayer.all_objects):
        bpy.ops.object.shade_smooth()

    converters.cleanup()
    return {'FINISHED'}
# [read3dm.py 完整程式碼]

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

    # 使用者原本的選項 (決定是否覆蓋節點)
    update_mats_flag = options.get("update_materials", False)

    # 1. 執行材質同步 (material.py 已經改寫為：若 flag 為 False 且已有節點，則跳過內容覆蓋)
    converters.handle_materials(context, model, materials, update_mats_flag)
    converters.handle_layers(context, model, toplayer, layerids, materials, update_mats_flag, True)

    # 2. 強制開啟「材質連結」開關
    # 這是為了確保即便按下 [X]，新匯入的幾何體也會正確地「連上」那顆保留了編輯內容的材質球
    link_options = options.copy()
    link_options["update_materials"] = True 

    for ob in model.Objects:
        og = ob.Geometry
        attr = ob.Attributes
        rhinolayer = model.Layers.FindIndex(attr.LayerIndex)
        
        object_name = attr.Name if attr.Name else f"{str(og.ObjectType).split('.')[1]} {str(attr.Id)}"
        
        # 取得材質名稱
        mat_index = attr.MaterialIndex
        if attr.MaterialSource == r3d.ObjectMaterialSource.MaterialFromLayer:
            mat_index = rhinolayer.RenderMaterialIndex
        
        rhino_material = model.Materials.FindIndex(mat_index)
        if rhino_material:
            matname = rhino_material.Name
        else:
            matname = converters.material.DEFAULT_RHINO_MATERIAL

        view_color = rhinolayer.Color if attr.ColorSource == r3d.ObjectColorSource.ColorFromLayer else attr.ObjectColor
        
        # 從對照表中抓取材質 (可能是已更名、已保留編輯的舊材質)
        blmat = materials.get(matname, materials[converters.material.DEFAULT_RHINO_MATERIAL])
        
        layer = layerids[str(rhinolayer.Id)][1]
        
        # 執行幾何體轉換，並帶入強制連結開關
        converters.convert_object(context, ob, object_name, layer, blmat, view_color, scale, link_options)

    if toplayer.name not in context.scene.collection.children:
        context.scene.collection.children.link(toplayer)

    with context.temp_override(selected_editable_objects=toplayer.all_objects):
        bpy.ops.object.shade_smooth()

    converters.cleanup()
    return {'FINISHED'}
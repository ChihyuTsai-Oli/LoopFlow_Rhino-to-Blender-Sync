# [material.py 完整程式碼]

import binascii
import struct
import bpy
import rhino3dm as r3d
from bpy_extras.node_shader_utils import ShaderWrapper, PrincipledBSDFWrapper
from . import utils
from . import rdk_manager
from pathlib import Path, PureWindowsPath, PurePosixPath
import base64
import tempfile
import uuid
from typing import Any, Tuple

DEFAULT_RHINO_MATERIAL = "Rhino Default Material"
DEFAULT_TEXT_MATERIAL = "Rhino Default Text"
DEFAULT_RHINO_MATERIAL_ID = uuid.UUID("00000000-ABCD-EF01-2345-000000000000")
DEFAULT_RHINO_TEXT_MATERIAL_ID = uuid.UUID("00000000-ABCD-EF01-6789-000000000000")

_white = (0.8, 0.8, 0.8, 1.0) # 修正為灰白色

def tobytes(d):
    t = type(d)
    if t is bool: return struct.pack("?", d)
    if t is float: return struct.pack("f", d)
    if t is tuple and len(d) == 4: return struct.pack("IIII", *d)
    return b''

def srgb_eotf(srgb_color):
    def cc(v): return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return tuple(cc(x) for x in srgb_color)

def get_color_field(rm, field_name):
    colstr = rm.GetParameter(field_name)
    if not colstr: return _white
    return srgb_eotf(tuple(float(f) for f in colstr.split(",")))

def get_float_field(rm, field_name):
    fl = rm.GetParameter(field_name)
    return float(fl) if fl else 0.0

def material_name(m): return m.Name if m and m.Name else DEFAULT_RHINO_MATERIAL
def rendermaterial_name(m): return m.Name if m and m.Name else DEFAULT_RHINO_MATERIAL

# --- 材質轉換處理器 (全部導向 Principled BSDF) ---

def paint_material(rm, bm):
    p = PrincipledBSDFWrapper(bm, is_readonly=False)
    p.base_color = get_color_field(rm, "color")[0:3]
    p.roughness = 1.0 - get_float_field(rm, "reflectivity")

def plaster_material(rm, bm):
    p = PrincipledBSDFWrapper(bm, is_readonly=False)
    p.base_color = get_color_field(rm, "color")[0:3]
    p.roughness = 1.0

def default_material(bm):
    p = PrincipledBSDFWrapper(bm, is_readonly=False)
    p.base_color = (0.8, 0.8, 0.8)
    p.roughness = 1.0

def default_text_material(bm):
    p = PrincipledBSDFWrapper(bm, is_readonly=False)
    p.base_color = (0.05, 0.05, 0.05)
    p.roughness = 1.0

def metal_material(rm, bm):
    p = PrincipledBSDFWrapper(bm, is_readonly=False)
    p.base_color = get_color_field(rm, "color")[0:3]
    p.metallic = 1.0
    p.roughness = get_float_field(rm, "polish-amount")

def glass_material(rm, bm):
    p = PrincipledBSDFWrapper(bm, is_readonly=False)
    p.base_color = get_color_field(rm, "color")[0:3]
    p.transmission = 1.0
    p.ior = get_float_field(rm, "ior")

def pbr_material(rm, bm):
    p = PrincipledBSDFWrapper(bm, is_readonly=False)
    p.base_color = get_color_field(rm, "pbr-base-color")[0:3]
    p.metallic = get_float_field(rm, "pbr-metallic")
    p.roughness = get_float_field(rm, "pbr-roughness")
    p.transmission = 1.0 - get_float_field(rm, "pbr-opacity")
    p.ior = get_float_field(rm, "pbr-opacity-ior")

material_handlers = {
    'rdk-paint-material': paint_material, 'rdk-plaster-material': plaster_material,
    'rdk-metal-material': metal_material, 'rdk-glass-material': glass_material,
    '5a8d7b9b-cdc9-49de-8c16-2ef64fb097ab': pbr_material,
}

def harvest_from_rendercontent(model, mat, bm):
    bm.use_nodes = True
    handler = material_handlers.get(mat.TypeName, plaster_material)
    handler(mat, bm)

def handle_embedded_files(model): pass

def handle_materials(context, model : r3d.File3dm, materials, update):
    """智慧材質同步邏輯"""
    handle_embedded_files(model)

    # 處理預設材質
    for d_name, d_id, d_handler in [(DEFAULT_RHINO_MATERIAL, DEFAULT_RHINO_MATERIAL_ID, default_material), (DEFAULT_TEXT_MATERIAL, DEFAULT_RHINO_TEXT_MATERIAL_ID, default_text_material)]:
        if d_name not in materials:
            tags = utils.create_tag_dict(d_id, d_name)
            blmat = utils.get_or_create_iddata(context.blend_data.materials, tags, None)
            # 若為全新材質 (無節點)，則執行初始設定
            if not blmat.use_nodes:
                d_handler(blmat)
            materials[d_name] = blmat

    # 處理 Rhino 模型材質
    for mat in model.Materials:
        if not mat.PhysicallyBased: mat.ToPhysicallyBased()
        m = model.RenderContent.FindId(mat.RenderMaterialInstanceId)
        if not m: continue
        
        matname = rendermaterial_name(m)
        
        # 1. 透過 GUID 在 Blender 資料庫尋找對象 (會自動處理更名)
        tags = utils.create_tag_dict(m.Id, m.Name)
        blmat = utils.get_or_create_iddata(context.blend_data.materials, tags, None)
        
        # 2. 智慧判定：是否執行 Harvest (覆蓋節點)
        # 條件：(按下 [O] 按鈕) 或 (這是一顆完全沒有節點的全新材質)
        if update or not blmat.use_nodes:
            harvest_from_rendercontent(model, m, blmat)
            
        materials[matname] = blmat
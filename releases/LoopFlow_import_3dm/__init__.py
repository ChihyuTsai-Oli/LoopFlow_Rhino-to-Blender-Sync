# -*- coding: utf-8 -*-
"""
====================================
Import Rhinoceros 3D (R2B Pro)
====================================
Version            : v5.0
Date               : 2026-04-27
Author             : Cursor + Claude Sonnet 4.6
Environment        : Blender 5.1.0 / Python 3.13
Location           : 3D Viewport sidebar (N-Panel > LoopFlow 3dm > Rhino Live Link)

[System Overview]
This addon is the Blender-side receiver for the "Rhino into Blender" workflow.
It breaks the barrier between the two applications by providing seamless geometry
updates, dual-JSON performance sync, fully automated light assembly, and BIM
auto-material assignment.

[Core Features & Operations]

1. Seamless Geometry Update (Model Sync & State Memory)
   - Supports first-time import and subsequent updates. On update it deduplicates
     automatically and perfectly preserves any manually configured "exclude, hide,
     render-off" states and Bounds display mode set inside Blender.
   - Usage: on the Rhino side run LiveLink_R2B_Models.py (choose a layer to produce R2B.3dm);
     on the Blender side click [Import Models] or [Update Models].

2. Dual-JSON Engine: Camera & Light Sync
   - Camera: background timer polls R2B_Camera_Sync.json every CAMERA_POLL_INTERVAL seconds;
     extremely lightweight, keeps 60 FPS unaffected.
   - Lights: manual update, reads R2B_Light_Sync.json.
   - Precise alignment & orphan cleanup: forces displaced fixtures back to their correct
     positions. Built-in "life-link" engine — when a Rhino point is deleted, Blender
     cleanly removes the corresponding object, eliminating StructRNA ghost errors.
   - Usage:
     - Create COL_FIXTURES (for fixture models) and COL_LIGHTING (for lights), and set up templates.
     - Set the [Sync Folder] in the panel to the directory containing the JSON files.
     - Camera: click [Start Camera Sync] to activate background sync.
     - Lights: after exporting points from Rhino, click [Sync Rhino Lights] for a one-click update.

3. Auto Basic Material Assigner
   - General and specialised binding: strips prefixes and intelligently assigns materials
     scene-wide; forces all objects (including empty material slots) inside LAYER_SUFFIX_LT
     nested layers to bind the designated emissive material.
   - Stamp & prototype mechanism: built-in prototype lookup. If a model update generates
     an unstamped .001 duplicate, the script automatically re-routes it back to the
     manually adjusted stamped prototype, eliminating material proliferation and overwriting.
   - Usage:
     - Place objects in the `Materials` collection and assign prototype materials
       (e.g. DW_Glass, D_Frame; LAYER_SUFFIX_LT mapped to MAT_PRESET_LT_K).
     - Click [Assign Basic Mat.] to instantly replace all matching materials scene-wide.

[Notes]
- The sync directory is auto-populated by RHINO_OT_ResetPath using the DataPath from R2B_Path.txt.
- Light sync relies on the template object names inside COL_FIXTURES and COL_LIGHTING.
- Camera sync runs as a background Timer; stop it with [Stop Camera Sync] before closing the addon or Blender.

"""

bl_info = {
    "name": "Import Rhinoceros 3D (R2B Pro)",
    "author": "Nathan 'jesterKing' Letwory, Joel Putnam, Tom Svilans, Lukas Fertig, Bernd Moeller, Workflow Partner",
    "version": (0, 0, 50),
    "blender": (5, 1, 0),
    "location": "N-Panel > LoopFlow 3dm",
    "description": "R2B Dual-JSON performance build (V50 centralised constants + LoopFlow 3dm Panel)",
    "category": "Import-Export",
}

import bpy
import os
import re
import json
import mathutils
from .read3dm import read_3dm
from bpy_extras.io_utils import ImportHelper

# -------------------------------------------------------------------
# Module-level constants (centralised for easy tuning)
# -------------------------------------------------------------------

# Sync file names
CAMERA_SYNC_FILE   = "R2B_Camera_Sync.json"
LIGHT_SYNC_FILE    = "R2B_Light_Sync.json"

# Collection names
COL_FIXTURES       = "Lighting Fixtures"
COL_LIGHTING       = "Lighting"
COL_LIGHT_POINTS   = "R2B Lighting Points"
COL_MATERIALS      = "Materials"       # Prototype library Collection for Assign Basic Mat. (currently disabled)

# Material constants
MAT_PRESET_LT_K    = "Preset_Lighting_K"
LAYER_SUFFIX_LT    = "5_LT"
MAT_AUTO_5LT       = "Auto_5LT_Light"

# Technical parameters
CAMERA_POLL_INTERVAL = 0.03     # Camera poll interval (seconds)
DEFAULT_LENS         = 50.0     # Default focal length (mm)
EMPTY_DISPLAY_SIZE   = 0.3      # Display size for light-point Empties

# -------------------------------------------------------------------
# 1. Core helper functions
# -------------------------------------------------------------------
def merge_duplicate_materials():
    count = 0
    for mat in bpy.data.materials:
        match = re.match(r"(.*)\.\d{3}$", mat.name)
        if match:
            base_name = match.group(1)
            base_mat = bpy.data.materials.get(base_name)
            if base_mat and base_mat != mat:
                mat.user_remap(base_mat)
                bpy.data.materials.remove(mat)
                count += 1
    return count

def get_template_objects(type_name):
    templates = []
    clean_type = type_name.strip()
    for col_name in [COL_FIXTURES, COL_LIGHTING]:
        col = bpy.data.collections.get(col_name)
        if col:
            for obj in col.objects:
                base_name = re.sub(r'\.\d{3}$', '', obj.name).strip()
                if base_name == clean_type:
                    templates.append(obj)
                    break
    return templates

def get_all_objects_in_collection(collection):
    objs = set(collection.objects)
    for child in collection.children:
        objs.update(get_all_objects_in_collection(child))
    return objs

# -------------------------------------------------------------------
# 2. Viewport sync engine (camera only - ultra-lightweight)
# -------------------------------------------------------------------
def update_viewport_from_json():
    wm = bpy.context.window_manager
    scene = bpy.context.scene
    if wm.get("livelink_viewport_active", 0) == 0:
        return None

    json_dir = bpy.path.abspath(scene.rhino_json_dir)
    json_path = os.path.join(json_dir, CAMERA_SYNC_FILE)

    scale_factor = scene.rhino_cam_scale
    lens_mult = scene.rhino_cam_lens_mult

    if not os.path.exists(json_path):
        return CAMERA_POLL_INTERVAL

    try:
        current_mtime = os.path.getmtime(json_path)
        last_mtime = wm.get("livelink_last_mtime", 0.0)

        if current_mtime == last_mtime:
            return CAMERA_POLL_INTERVAL
        wm["livelink_last_mtime"] = current_mtime

        with open(json_path, 'r') as f:
            data = json.load(f)

        raw_x = data["location"]["x"] * scale_factor
        raw_y = data["location"]["y"] * scale_factor
        raw_z = data["location"]["z"] * scale_factor
        loc = mathutils.Vector((raw_x, raw_y, raw_z))

        dir_vec = mathutils.Vector((data["direction"]["x"], data["direction"]["y"], data["direction"]["z"])).normalized()
        up_vec  = mathutils.Vector((data["up"]["x"], data["up"]["y"], data["up"]["z"])).normalized()

        base_lens = data.get("lens", DEFAULT_LENS)
        final_lens = base_lens * lens_mult

        z_axis = -dir_vec
        x_axis = up_vec.cross(z_axis).normalized()
        y_axis = z_axis.cross(x_axis).normalized()

        mat = mathutils.Matrix((x_axis, y_axis, z_axis)).transposed()
        rot_quat = mat.to_quaternion()

        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                rv3d = space.region_3d
                if rv3d.view_perspective != 'PERSP':
                    rv3d.view_perspective = 'PERSP'
                space.lens = final_lens
                rv3d.view_rotation = rot_quat
                rv3d.view_location = loc + dir_vec * rv3d.view_distance
                area.tag_redraw()

    except Exception:
        pass

    return CAMERA_POLL_INTERVAL

# -------------------------------------------------------------------
# 3. Light sync engine (triggered by manual button)
# -------------------------------------------------------------------
class RHINO_OT_SyncLights(bpy.types.Operator):
    bl_idname = "import_3dm.sync_lights"
    bl_label = "Sync Rhino Lights"
    bl_description = "Read R2B_Light_Sync.json and manually align/generate fixtures and clean up orphans"

    def execute(self, context):
        scene = context.scene
        json_dir = bpy.path.abspath(scene.rhino_json_dir)
        json_path = os.path.join(json_dir, LIGHT_SYNC_FILE)
        scale_factor = scene.rhino_cam_scale

        if not os.path.exists(json_path):
            self.report({'WARNING'}, f"File not found: {json_path}! Please verify the directory.")
            return {'CANCELLED'}

        try:
            with open(json_path, 'r') as f:
                data = json.load(f)

            if "points" not in data:
                self.report({'INFO'}, "No light point data found in JSON.")
                return {'FINISHED'}

            light_col = bpy.data.collections.get(COL_LIGHT_POINTS)
            if not light_col:
                light_col = bpy.data.collections.new(COL_LIGHT_POINTS)
                bpy.context.scene.collection.children.link(light_col)

            active_guids = set()

            for pt_data in data["points"]:
                guid = pt_data["guid"]
                active_guids.add(guid)
                pt_type = pt_data["type"]
                pt_loc = mathutils.Vector((
                    pt_data["loc"][0] * scale_factor,
                    pt_data["loc"][1] * scale_factor,
                    pt_data["loc"][2] * scale_factor
                ))

                target_empty = None
                for obj in light_col.objects:
                    try:
                        if obj.get("rhino_guid") == guid:
                            target_empty = obj
                            break
                    except ReferenceError:
                        pass

                if target_empty:
                    target_empty.location = pt_loc
                else:
                    new_empty = bpy.data.objects.new(f"RH_{pt_type}_{guid[:5]}", None)
                    new_empty.empty_display_type = 'PLAIN_AXES'
                    new_empty.empty_display_size = EMPTY_DISPLAY_SIZE
                    new_empty["rhino_guid"] = guid
                    new_empty["rhino_type"] = pt_type
                    light_col.objects.link(new_empty)
                    new_empty.location = pt_loc
                    target_empty = new_empty

                    for potential_child in bpy.data.objects:
                        try:
                            if potential_child.get("recovered_rhino_guid") == guid:
                                world_mat = potential_child.matrix_world.copy()
                                potential_child.parent = target_empty
                                potential_child.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                                parent_future_world = mathutils.Matrix.Translation(pt_loc)
                                potential_child.matrix_local = parent_future_world.inverted() @ world_mat
                                del potential_child["recovered_rhino_guid"]
                        except ReferenceError:
                            pass

                templates = get_template_objects(pt_type)
                processed_insts = []

                for template in templates:
                    safe_name = re.sub(r'\.\d{3}$', '', template.name)
                    prefix = f"INST_{safe_name}_{guid[:5]}"

                    existing_inst = None
                    for c in target_empty.children:
                        try:
                            if c.name.startswith(prefix) and c not in processed_insts:
                                existing_inst = c
                                break
                        except ReferenceError:
                            pass

                    if existing_inst:
                        existing_inst.location = template.location
                        existing_inst.rotation_euler = template.rotation_euler
                        existing_inst.scale = template.scale
                        processed_insts.append(existing_inst)
                    else:
                        new_inst = template.copy()
                        if template.data:
                            new_inst.data = template.data
                        new_inst.name = prefix
                        light_col.objects.link(new_inst)

                        new_inst.parent = target_empty
                        new_inst.matrix_parent_inverse = mathutils.Matrix.Identity(4)
                        new_inst.location = template.location
                        new_inst.rotation_euler = template.rotation_euler
                        new_inst.scale = template.scale
                        processed_insts.append(new_inst)

                for c in list(target_empty.children):
                    try:
                        if c.name.startswith("INST_") and c not in processed_insts:
                            bpy.data.objects.remove(c, do_unlink=True)
                    except ReferenceError:
                        pass

            # [V49 fix] Cascade-delete orphaned empties when Rhino points are removed
            empties_to_remove = []
            for obj in light_col.objects:
                try:
                    if "rhino_guid" in obj and obj["rhino_guid"] not in active_guids:
                        empties_to_remove.append(obj)
                except ReferenceError:
                    pass

            for empty in empties_to_remove:
                try:
                    removed_guid = empty["rhino_guid"]
                    for child in list(empty.children):
                        try:
                            if child.name.startswith("INST_"):
                                bpy.data.objects.remove(child, do_unlink=True)
                            else:
                                child["recovered_rhino_guid"] = removed_guid
                                world_mat = child.matrix_world.copy()
                                child.parent = None
                                child.matrix_world = world_mat
                        except ReferenceError:
                            pass
                    bpy.data.objects.remove(empty, do_unlink=True)
                except ReferenceError:
                    pass

            self.report({'INFO'}, f"Light sync complete! Processed {len(data['points'])} point(s).")
        except Exception as e:
            self.report({'ERROR'}, f"Sync failed: {e}")

        return {'FINISHED'}

# -------------------------------------------------------------------
# 4. Additional operators
# -------------------------------------------------------------------

# ===========================================================================
# [DISABLED] RHINO_OT_AssignBasicMat — Assign Basic Mat. full-scene auto-assign
# Remove all leading '#' below to re-enable; also uncomment corresponding entries
# in the classes tuple and Panel draw method.
# ===========================================================================
# class RHINO_OT_AssignBasicMat(bpy.types.Operator):
#     bl_idname = "import_3dm.assign_basic_mat"
#     bl_label = "Assign Basic Mat."
#     bl_description = "Auto-scan the Materials library collection and replace scene materials by keyword"
#
#     def execute(self, context):
#         mat_col = bpy.data.collections.get(COL_MATERIALS)
#         if not mat_col:
#             self.report({'WARNING'}, "'Materials' Collection not found. Please create it and add source objects!")
#             return {'CANCELLED'}
#
#         assigned_phase1 = 0
#         assigned_phase2 = 0
#
#         # Phase 1: specialised rule LAYER_SUFFIX_LT (prototype-lookup safe version)
#         preset_k_mat = None
#         for obj in mat_col.objects:
#             if MAT_PRESET_LT_K in obj.name and obj.material_slots and obj.material_slots[0].material:
#                 preset_k_mat = obj.material_slots[0].material
#                 break
#             for slot in obj.material_slots:
#                 if slot.material and MAT_PRESET_LT_K in slot.material.name:
#                     preset_k_mat = slot.material
#                     break
#             if preset_k_mat:
#                 break
#
#         if not preset_k_mat:
#             self.report({'WARNING'}, f"No material containing '{MAT_PRESET_LT_K}' found in {COL_MATERIALS}. Skipping {LAYER_SUFFIX_LT} binding!")
#         else:
#             target_objs = set()
#             for col in bpy.data.collections:
#                 col_base = col.name.split('.')[0].strip()
#                 if col_base.endswith(LAYER_SUFFIX_LT):
#                     target_objs.update(get_all_objects_in_collection(col))
#
#             shared_empty_mat = bpy.data.materials.get(MAT_AUTO_5LT)
#             if not shared_empty_mat or not shared_empty_mat.get("r2b_auto_assigned"):
#                 shared_empty_mat = preset_k_mat.copy()
#                 shared_empty_mat.name = MAT_AUTO_5LT
#                 shared_empty_mat["r2b_auto_assigned"] = True
#
#             for obj in target_objs:
#                 if obj.type in {'MESH', 'CURVE', 'SURFACE'}:
#                     if len(obj.material_slots) == 0:
#                         obj.data.materials.append(shared_empty_mat)
#                         assigned_phase1 += 1
#                     else:
#                         for slot in obj.material_slots:
#                             mat = slot.material
#                             if not mat:
#                                 slot.material = shared_empty_mat
#                                 assigned_phase1 += 1
#                             elif not mat.get("r2b_auto_assigned"):
#                                 base_name = mat.name.split('.')[0].strip()
#                                 existing_tagged = bpy.data.materials.get(base_name)
#
#                                 if existing_tagged and existing_tagged.get("r2b_auto_assigned") and existing_tagged != mat:
#                                     mat.user_remap(existing_tagged)
#                                     bpy.data.materials.remove(mat)
#                                     assigned_phase1 += 1
#                                 else:
#                                     new_mat = preset_k_mat.copy()
#                                     mat.user_remap(new_mat)
#                                     bpy.data.materials.remove(mat)
#                                     new_mat.name = base_name
#                                     new_mat["r2b_auto_assigned"] = True
#                                     assigned_phase1 += 1
#
#         # Phase 2: general rule (prototype-lookup safe version)
#         source_mats = {}
#         for obj in mat_col.objects:
#             for slot in obj.material_slots:
#                 if slot.material:
#                     mat = slot.material
#                     clean_name = mat.name.split('.')[0].strip()
#                     if MAT_PRESET_LT_K in clean_name:
#                         continue
#                     keyword = re.sub(r'^(DW_|D_|W_)', '', clean_name, flags=re.IGNORECASE).strip()
#                     if keyword:
#                         source_mats[keyword.lower()] = mat
#
#         if source_mats:
#             sorted_keywords = sorted(source_mats.keys(), key=len, reverse=True)
#             for mat in list(bpy.data.materials):
#                 if mat.get("r2b_auto_assigned"):
#                     continue
#
#                 mat_name_lower = mat.name.lower()
#                 best_keyword = None
#
#                 for kw in sorted_keywords:
#                     if kw in mat_name_lower:
#                         if mat != source_mats[kw]:
#                             best_keyword = kw
#                             break
#
#                 if best_keyword:
#                     base_name = mat.name.split('.')[0].strip()
#                     existing_tagged = bpy.data.materials.get(base_name)
#
#                     if existing_tagged and existing_tagged.get("r2b_auto_assigned") and existing_tagged != mat:
#                         mat.user_remap(existing_tagged)
#                         bpy.data.materials.remove(mat)
#                         assigned_phase2 += 1
#                     else:
#                         source_mat = source_mats[best_keyword]
#                         new_mat = source_mat.copy()
#                         mat.user_remap(new_mat)
#                         bpy.data.materials.remove(mat)
#                         new_mat.name = base_name
#                         new_mat["r2b_auto_assigned"] = True
#                         assigned_phase2 += 1
#
#         self.report({'INFO'}, f"Done! {LAYER_SUFFIX_LT} forced {assigned_phase1} replacement(s); basic materials replaced {assigned_phase2}.")
#         return {'FINISHED'}
# ===========================================================================

class RHINO_OT_ResetProp(bpy.types.Operator):
    bl_idname = "import_3dm.reset_prop"
    bl_label = "Reset Property"
    bl_description = "Reset to default value"
    target: bpy.props.StringProperty()

    def execute(self, context):
        if self.target == "scale":
            context.scene.rhino_cam_scale = 0.01
            self.report({'INFO'}, "Scale Factor reset to default (0.01)")
        elif self.target == "lens":
            context.scene.rhino_cam_lens_mult = 1.80
            self.report({'INFO'}, "Lens Multiplier reset to default (1.80)")
        return {'FINISHED'}

class RHINO_OT_ToggleCamSync(bpy.types.Operator):
    bl_idname = "import_3dm.toggle_cam_sync"
    bl_label = "Toggle Camera Sync"
    bl_description = "Start or stop camera viewport sync with Rhino"

    def execute(self, context):
        wm = context.window_manager
        current_state = wm.get("livelink_viewport_active", 0)

        if current_state == 1:
            wm["livelink_viewport_active"] = 0
            self.report({'INFO'}, "Camera sync: stopped")
        else:
            wm["livelink_viewport_active"] = 1
            wm["livelink_last_mtime"] = 0.0
            bpy.app.timers.register(update_viewport_from_json)
            self.report({'INFO'}, "Camera sync: started")

        return {'FINISHED'}

class RHINO_OT_ShowHelp(bpy.types.Operator):
    bl_idname = "import_3dm.show_help"
    bl_label = "Rhino Live Link Quick Guide"
    bl_description = "Show the R2B workflow steps and notes"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="[Model Sync]", icon='MESH_DATA')
        box.label(text="1. Rhino: run LiveLink_R2B_Models.py (select a layer to produce R2B.3dm)")
        box.label(text="2. Blender: click 'Import Models' or 'Update Models'")
        layout.separator()
        box2 = layout.box()
        box2.label(text="[Auto Material & Lights]", icon='LIGHT')
        box2.label(text="1. Place prototype objects in Materials to use Assign Basic Mat")
        box2.label(text=f"2. Create {COL_FIXTURES} / {COL_LIGHTING} to link Rhino point positions")
        box2.label(text="3. Set Sync Folder (click Auto-Detect to fill automatically), then update lights and camera in one click")

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=450)

class RHINO_OT_ResetPath(bpy.types.Operator):
    bl_idname = "import_3dm.reset_path"
    bl_label = "Auto-Detect Paths"
    bl_description = "Auto-set the model path to //R2B.3dm and the JSON sync directory to DataPath from R2B_Path.txt"

    def execute(self, context):
        blend_path = bpy.data.filepath
        if not blend_path:
            self.report({'ERROR'}, "Please save the Blender file first to obtain its directory")
            return {'CANCELLED'}

        # Model path: R2B.3dm relative to the Blender file
        context.scene.rhino_update_path = "//R2B.3dm"

        # Sync Folder: points to DataPath from R2B_Path.txt (absolute AppData path)
        data_dir = os.path.join(
            os.getenv("APPDATA", ""),
            "McNeel", "Rhinoceros", "8.0", "scripts", "LoopFlow_R2B", "Data"
        )
        context.scene.rhino_json_dir = data_dir

        self.report({'INFO'}, "Paths auto-configured (Model: //R2B.3dm, JSON: {})".format(data_dir))
        return {'FINISHED'}

class RHINO_OT_QuickSync(bpy.types.Operator):
    bl_idname = "import_3dm.quick_sync"
    bl_label = "Rhino Quick Sync"

    @classmethod
    def description(cls, context, properties):
        if getattr(properties, 'update_mats', False):
            return "Import model and update materials (recommended for first import; overwrites unprotected materials)"
        return "Update geometry only, perfectly preserving materials and layer states already configured in Blender"

    update_mats: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        path = bpy.path.abspath(context.scene.rhino_update_path)
        if not os.path.exists(path):
            self.report({'ERROR'}, f"File not found: {path}")
            return {'CANCELLED'}

        col_states = {}

        def capture_col_states(lc):
            col_states[lc.collection.name] = {
                'exclude': lc.exclude,
                'hide_viewport_eye': lc.hide_viewport,
                'hide_viewport_screen': lc.collection.hide_viewport,
                'hide_render': lc.collection.hide_render
            }
            for child in lc.children:
                capture_col_states(child)

        capture_col_states(context.view_layer.layer_collection)

        obj_states = {}
        for obj in bpy.data.objects:
            obj_states[obj.name] = {
                'hide_get': obj.hide_get(),
                'hide_viewport': obj.hide_viewport,
                'hide_render': obj.hide_render,
                'display_type': obj.display_type,
                'display_bounds_type': obj.display_bounds_type
            }

        bpy.ops.import_3dm.some_data(
            filepath=path,
            import_curves=True,
            import_meshes=True,
            update_materials=self.update_mats
        )

        merged = merge_duplicate_materials()

        def restore_col_states(lc):
            if lc.collection.name in col_states:
                state = col_states[lc.collection.name]
                lc.exclude = state['exclude']
                lc.hide_viewport = state['hide_viewport_eye']
                lc.collection.hide_viewport = state['hide_viewport_screen']
                lc.collection.hide_render = state['hide_render']
            for child in lc.children:
                restore_col_states(child)

        restore_col_states(context.view_layer.layer_collection)

        for obj in bpy.data.objects:
            if obj.name in obj_states:
                state = obj_states[obj.name]
                obj.hide_set(state['hide_get'])
                obj.hide_viewport = state['hide_viewport']
                obj.hide_render = state['hide_render']
                obj.display_type = state.get('display_type', 'TEXTURED')
                obj.display_bounds_type = state.get('display_bounds_type', 'BOX')

        if merged > 0:
            self.report({'INFO'}, f"Model updated (states preserved, merged {merged} material(s))")
        else:
            self.report({'INFO'}, "Model updated (states preserved)")

        return {'FINISHED'}

# -------------------------------------------------------------------
# 5. Panel and import operator
# -------------------------------------------------------------------
class Import3dm(bpy.types.Operator, ImportHelper):
    bl_idname = "import_3dm.some_data"
    bl_label = "Import Rhinoceros 3D"
    filename_ext = ".3dm"
    filter_glob: bpy.props.StringProperty(default="*.3dm", options={'HIDDEN'})
    import_curves: bpy.props.BoolProperty(name="Curves", default=True)
    import_meshes: bpy.props.BoolProperty(name="Meshes", default=True)
    update_materials: bpy.props.BoolProperty(name="Update Materials", default=False)

    def execute(self, context):
        options = self.as_keywords(ignore=("filter_glob",))
        return read_3dm(context, options)

class RHINO_PT_QuickUpdate(bpy.types.Panel):
    bl_label = "Rhino Live Link"
    bl_idname = "RHINO_PT_QuickUpdate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LoopFlow 3dm'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        wm = context.window_manager

        layout.label(text="Model Sync", icon='MESH_DATA')
        box_model = layout.box()

        col = box_model.column()
        col.scale_y = 1.2
        col.operator("import_3dm.quick_sync", text="Import Models", icon='IMPORT').update_mats = True

        col_upd = box_model.column()
        col_upd.scale_y = 1.3
        col_upd.operator("import_3dm.quick_sync", text="Update Models", icon='FILE_REFRESH').update_mats = False

        row_model_path = box_model.row(align=True)
        row_model_path.prop(scene, "rhino_update_path", text="")
        row_model_path.operator("import_3dm.reset_path", text="", icon='VIEWZOOM')

        layout.separator()

        layout.label(text="Camera & Light Sync", icon='OUTLINER_OB_CAMERA')
        box_cam = layout.box()

        is_active = wm.get("livelink_viewport_active", 0) == 1

        row_cam = box_cam.row()
        row_cam.scale_y = 1.3
        if is_active:
            row_cam.operator("import_3dm.toggle_cam_sync", text="Stop Camera Sync", icon='PAUSE')
        else:
            row_cam.operator("import_3dm.toggle_cam_sync", text="Start Camera Sync", icon='PLAY')

        row_scale = box_cam.row(align=True)
        row_scale.prop(scene, "rhino_cam_scale", text="Scale")
        row_scale.operator("import_3dm.reset_prop", text="", icon='FILE_REFRESH').target = "scale"

        row_lens = box_cam.row(align=True)
        row_lens.prop(scene, "rhino_cam_lens_mult", text="Lens")
        row_lens.operator("import_3dm.reset_prop", text="", icon='FILE_REFRESH').target = "lens"

        box_cam.separator()

        row_light = box_cam.row()
        row_light.scale_y = 1.3
        row_light.operator("import_3dm.sync_lights", text="Sync Rhino Lights", icon='LIGHT')

        box_cam.prop(scene, "rhino_json_dir", text="Sync Folder")

        layout.separator()

        # layout.operator("import_3dm.assign_basic_mat", text="Assign Basic Mat.", icon='MATERIAL')  # [DISABLED]
        layout.operator("import_3dm.show_help", text="Help & Guide", icon='HELP')

# -------------------------------------------------------------------
# 6. Registration
# -------------------------------------------------------------------
classes = (
    Import3dm,
    RHINO_OT_SyncLights,
    # RHINO_OT_AssignBasicMat,  # [DISABLED]
    RHINO_OT_ResetProp,
    RHINO_OT_ResetPath,
    RHINO_OT_QuickSync,
    RHINO_OT_ToggleCamSync,
    RHINO_OT_ShowHelp,
    RHINO_PT_QuickUpdate
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.rhino_update_path = bpy.props.StringProperty(
        name="Path", default="//R2B.3dm", subtype='FILE_PATH'
    )
    bpy.types.Scene.rhino_json_dir = bpy.props.StringProperty(
        name="Sync Folder", default="//", subtype='DIR_PATH'
    )
    bpy.types.Scene.rhino_cam_scale = bpy.props.FloatProperty(
        name="Scale Factor", description="Unit conversion ratio (0.01 for centimetres)", default=0.01, min=0.0001, max=100.0
    )
    bpy.types.Scene.rhino_cam_lens_mult = bpy.props.FloatProperty(
        name="Lens Multiplier", description="Increase this value if the view appears too wide", default=1.80, min=0.1, max=5.0
    )

def unregister():
    if bpy.context.window_manager.get("livelink_viewport_active", 0) == 1:
        bpy.context.window_manager["livelink_viewport_active"] = 0

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.rhino_update_path
    del bpy.types.Scene.rhino_json_dir
    del bpy.types.Scene.rhino_cam_scale
    del bpy.types.Scene.rhino_cam_lens_mult

if __name__ == "__main__":
    register()

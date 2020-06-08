# <pep8-80 compliant>

'''
This program is free software; you can redistribute it and
or modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see http://www.gnu.org/licenses
'''

# Inspired from an idea by Daniel Bystedt

import fileinput
import os
from math import pi
from platform import system

import blf
import bpy
import rna_keymap_ui
from bpy.props import (BoolProperty, EnumProperty, FloatProperty, IntProperty,
                       PointerProperty, StringProperty)
from bpy.types import (AddonPreferences, Menu, Operator, Panel,
                       PreferencesFilePaths, PropertyGroup)

bl_info = {
    "name": "RADarr",
    "description": "Radial Array made super easy",
    "author": "Arindam Mondal",
    "version": (283, 0, 1),
    "blender": (2, 83, 0),
    "location": "3D Viewport > Object Mode",
    "category": "Object"
}


last_transf_increment = 0.00
op_call_flag = False
first_run = True
ori_rot_val = 0.00
init_count = 0
event_trig = True
dont_update_temp = True
dont_update = True

main_ob_rot_X, main_ob_rot_Y, main_ob_rot_Z = 0.0, 0.0, 0.0
mt_offset_rot_nor = 0.0

ci, co = True, False
operator_doff = True

user_dir = os.path.expanduser("~")
# home_dir = os.environ.get('HOME')
common_subdir = "2.83/scripts/addons/RADarr"

if system() == 'Linux':
    addon_path = "/.config/blender/" + common_subdir
elif system() == 'Windows':
    addon_path = (
        "\\AppData\\Roaming\\Blender Foundation\\Blender\\"
        + common_subdir.replace("/", "\\")
    )
    # os.path.join()
elif system() == 'Darwin':
    addon_path = "/Library/Application Support/Blender/" + common_subdir

addon_dir = user_dir + addon_path

custom_script_dir = bpy.context.preferences.filepaths.script_directory

if os.path.isdir(addon_dir) == False:
    if system() == 'Windows':
        addon_dir = custom_script_dir + "\\addons\\RADarr"
    else:
        addon_dir = custom_script_dir + "/addons/RADarr"

modal_file_path = addon_dir + "/modal/bool_state.txt"

font_info = {
    "font_id": 0,
    "handler": None,
}

addon_keymaps = []
kc = bpy.context.window_manager.keyconfigs.addon


def get_orients():
    view_orientations = []

    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            reg_3d = area.spaces.active.region_3d
            view_matrix = reg_3d.view_matrix
            view_rot = view_matrix.to_euler()

            def r(x): return round(x, 2)

            orientation_dict = {
                (0.0, 0.0, 0.0): 'TOP',
                (r(pi), 0.0, 0.0): 'BOTTOM',
                (r(-pi/2), 0.0, 0.0): 'FRONT',
                (r(pi/2), 0.0, r(-pi)): 'BACK',
                (r(-pi/2), r(pi/2), 0.0): 'LEFT',
                (r(-pi/2), r(-pi/2), 0.0): 'RIGHT'
            }

            view_orientation = orientation_dict.get(
                tuple(map(r, view_rot)),
                'ANOMALY'
            )

            view_orientations.append(view_orientation)

    return view_orientations


def set_orients():

    csr = bpy.context.scene.rad_array

    if csr.orient_modes == 'AUTO':
        consider_view = get_orients()[0]
    else:
        consider_view = csr.orient_axes

    if consider_view == 'TOP':
        return 2, 1, 0, 1
    elif consider_view == 'BOTTOM':
        return 2, -1, 0, 1
    elif consider_view == 'FRONT':
        return 1, -1, 0, 1
    elif consider_view == 'BACK':
        return 1, 1, 0, -1
    elif consider_view == 'LEFT':
        return 0, -1, 1, -1
    elif consider_view == 'RIGHT':
        return 0, 1, 1, 1
    elif consider_view == 'ANOMALY':
        return 2, 1, 0, 1


def rad_arr(self, context):

    global main_ob_rot_X, main_ob_rot_Y, main_ob_rot_Z
    global mt_offset_rot_nor
    global last_transf_increment, op_call_flag
    global first_run, ori_rot_val

    if op_call_flag:
        csr = context.scene.rad_array
    else:
        csr = self

    main_ob = bpy.context.active_object
    main_ob_name = main_ob.name

    main_ob_rot_X = main_ob.rotation_euler[0]
    main_ob_rot_Y = main_ob.rotation_euler[1]
    main_ob_rot_Z = main_ob.rotation_euler[2]

    bcs = bpy.context.scene
    cursorLoc_X = bcs.cursor.location[0]
    cursorLoc_Y = bcs.cursor.location[1]
    cursorLoc_Z = bcs.cursor.location[2]
    bpy.ops.view3d.snap_cursor_to_selected()

    if main_ob.modifiers.get("RADarr!"):
        for modifier in main_ob.modifiers:
            if modifier.name == "RADarr!":

                csr.circum_coverage = 1.00
                first_run = True
                ori_rot_val = 0.00

                mt_offset = bpy.data.objects[main_ob_name + "_Offseter"]

                bpy.ops.object.select_all(action='DESELECT')
                mt_offset.select_set(True)
                bpy.ops.object.rotation_clear()

                n = set_orients()[0]

                mt_offset.rotation_euler[n] = (2 * pi) / csr.dyn_count
                modifier.count = csr.dyn_count

                mt_offset_rot_nor = mt_offset.rotation_euler[n]

                if n == 0:
                    mt_offset.rotation_euler[0] = (
                        mt_offset_rot_nor + main_ob_rot_X
                    )
                    mt_offset.rotation_euler[1] = main_ob_rot_Y
                    mt_offset.rotation_euler[2] = main_ob_rot_Z

                elif n == 1:
                    mt_offset.rotation_euler[0] = main_ob_rot_X
                    mt_offset.rotation_euler[1] = (
                        mt_offset_rot_nor + main_ob_rot_Y
                    )
                    mt_offset.rotation_euler[2] = main_ob_rot_Z

                elif n == 2:
                    mt_offset.rotation_euler[0] = main_ob_rot_X
                    mt_offset.rotation_euler[1] = main_ob_rot_Y
                    mt_offset.rotation_euler[2] = (
                        mt_offset_rot_nor + main_ob_rot_Z
                    )

                prntr = bpy.data.objects[main_ob_name + "_Parenter"]

                if csr.space_types:
                    bpy.ops.object.select_all(action='DESELECT')
                    prntr.select_set(True)
                    bpy.ops.object.rotation_clear()
                else:
                    prntr.rotation_euler[0] = main_ob_rot_X
                    prntr.rotation_euler[1] = main_ob_rot_Y
                    prntr.rotation_euler[2] = main_ob_rot_Z

                bpy.ops.object.select_all(action='DESELECT')
                main_ob.select_set(True)
                bpy.context.view_layer.objects.active = main_ob

                l = set_orients()[2]
                p = set_orients()[3]

                main_ob.location[l] -= (last_transf_increment * p)
                main_ob.location[l] += (csr.ofst_radius * p)
                last_transf_increment = csr.ofst_radius

    else:

        mod_id = main_ob.modifiers.new(
            type="ARRAY",
            name="RADarr!"
        )

        bpy.ops.object.transform_apply(scale=True)

        bpy.ops.object.empty_add(type='SPHERE', radius=0)
        mt_offset = bpy.context.active_object
        mt_offset.name = main_ob_name + "_Offseter"

        n = set_orients()[0]

        mt_offset.rotation_euler[n] = (2 * pi) / csr.dyn_count

        mt_offset_rot_nor = mt_offset.rotation_euler[n]

        if n == 0:
            mt_offset.rotation_euler[0] = (
                mt_offset_rot_nor + main_ob_rot_X
            )
            mt_offset.rotation_euler[1] = main_ob_rot_Y
            mt_offset.rotation_euler[2] = main_ob_rot_Z

        elif n == 1:
            mt_offset.rotation_euler[0] = main_ob_rot_X
            mt_offset.rotation_euler[1] = (
                mt_offset_rot_nor + main_ob_rot_Y
            )
            mt_offset.rotation_euler[2] = main_ob_rot_Z

        elif n == 2:
            mt_offset.rotation_euler[0] = main_ob_rot_X
            mt_offset.rotation_euler[1] = main_ob_rot_Y
            mt_offset.rotation_euler[2] = (
                mt_offset_rot_nor + main_ob_rot_Z
            )

        if csr.radius_range == "MM":
            disp_size = 0.01
        elif csr.radius_range == "CM":
            disp_size = 0.10
        elif csr.radius_range == "METER":
            disp_size = 1.00

        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=disp_size)
        parenter = bpy.context.active_object
        parenter.name = main_ob_name + "_Parenter"

        bpy.ops.object.select_all(action='DESELECT')
        main_ob.select_set(True)
        mt_offset.select_set(True)
        parenter.select_set(True)
        bpy.context.view_layer.objects.active = parenter
        bpy.ops.object.parent_set()
        mt_offset.hide_viewport = True

        prntr = bpy.data.objects[main_ob_name + "_Parenter"]

        if csr.space_types:
            bpy.ops.object.select_all(action='DESELECT')
            prntr.select_set(True)
            bpy.ops.object.rotation_clear()
        else:
            prntr.rotation_euler[0] = main_ob_rot_X
            prntr.rotation_euler[1] = main_ob_rot_Y
            prntr.rotation_euler[2] = main_ob_rot_Z

        bpy.ops.object.select_all(action='DESELECT')
        main_ob.select_set(True)
        bpy.context.view_layer.objects.active = main_ob

        mod_id.count = csr.dyn_count
        mod_id.use_relative_offset = False
        mod_id.use_object_offset = True
        mod_id.offset_object = mt_offset

        l = set_orients()[2]
        p = set_orients()[3]

        main_ob.location[l] += (csr.ofst_radius * p)
        last_transf_increment = (csr.ofst_radius * p)

    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    bcs.cursor.location[0] = cursorLoc_X
    bcs.cursor.location[1] = cursorLoc_Y
    bcs.cursor.location[2] = cursorLoc_Z

    csr.circum_coverage = 1.00
    first_run = True
    ori_rot_val = 0.00


def temp_update(context):

    global dont_update_temp

    csr = context.scene.rad_array
    print(dont_update_temp)
    dont_update_temp = csr.update_switch
    print(dont_update_temp)


def modal_switch(self, context):

    global dont_update_temp

    # try:
    #     del(bpy.types.Scene.rad_array)
    #     bpy.utils.unregister_class(GLOBAL_PG_radr_props_settings)
    # except:
    #     pass

    user_pref = bpy.context.preferences.addons[__name__]
    if user_pref.preferences.interactive_switch:
        dont_update_temp = False
    else:
        dont_update_temp = True

    # bpy.utils.register_class(GLOBAL_PG_radr_props_settings)
    # bpy.types.Scene.rad_array = PointerProperty(
    #     type = GLOBAL_PG_radr_props_settings
    # )


def do_nothing(self, context):
    pass


def rad_arr_f5(context):

    global last_transf_increment

    csr = context.scene.rad_array

    main_ob = bpy.context.active_object
    main_ob_name = main_ob.name

    bcs = bpy.context.scene
    cursorLoc_X = bcs.cursor.location[0]
    cursorLoc_Y = bcs.cursor.location[1]
    cursorLoc_Z = bcs.cursor.location[2]
    bpy.ops.view3d.snap_cursor_to_selected()

    if main_ob.modifiers.get("RADarr!"):
        for modifier in main_ob.modifiers:
            if modifier.name == "RADarr!":

                mt_offset = bpy.data.objects[main_ob_name + "_Offseter"]

                n = set_orients()[0]

                mt_offset.rotation_euler[n] = (2 * pi) / csr.dyn_count

                modifier.count = csr.dyn_count

                l = set_orients()[2]
                p = set_orients()[3]

                main_ob.location[l] -= (last_transf_increment * p)
                main_ob.location[l] += (csr.ofst_radius * p)
                last_transf_increment = csr.ofst_radius

    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    bcs.cursor.location[0] = cursorLoc_X
    bcs.cursor.location[1] = cursorLoc_Y
    bcs.cursor.location[2] = cursorLoc_Z


def rad_arr_modal(self, context):

    global main_ob_rot_X, main_ob_rot_Y, main_ob_rot_Z
    global mt_offset_rot_nor
    global last_transf_increment
    global first_run, ori_rot_val

    csr = context.scene.rad_array

    main_ob = bpy.context.active_object
    main_ob_name = main_ob.name

    if self.modal_op_count == 0:

        if main_ob.modifiers.get("RADarr!"):

            csr.dyn_count = 1
            csr.ofst_radius = 0.00
            rad_arr_f5(context)

            bpy.ops.object.modifier_remove(modifier="RADarr!")
            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            bpy.ops.object.select_all(action='DESELECT')

            offset_empty_name = main_ob_name + "_Offseter"
            offset_empty = bpy.data.objects[offset_empty_name]
            offset_empty.hide_viewport = False
            offset_empty.select_set(True)
            bpy.ops.object.delete()

            parent_empty_name = main_ob_name + "_Parenter"
            parent_empty = bpy.data.objects[parent_empty_name]
            parent_empty.select_set(True)
            bpy.ops.object.delete()

            main_ob.select_set(True)
            bpy.context.view_layer.objects.active = main_ob

        mod_id = main_ob.modifiers.new(
            type="ARRAY",
            name="RADarr!"
        )

        bpy.ops.object.transform_apply(scale=True)

        bpy.ops.object.empty_add(type='SPHERE', radius=0)
        mt_offset = bpy.context.active_object
        mt_offset.name = main_ob_name + "_Offseter"

        if csr.radius_range == "MM":
            disp_size = 0.01
        elif csr.radius_range == "CM":
            disp_size = 0.10
        elif csr.radius_range == "METER":
            disp_size = 1.00

        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=disp_size)
        parenter = bpy.context.active_object
        parenter.name = main_ob_name + "_Parenter"

        bpy.ops.object.select_all(action='DESELECT')
        main_ob.select_set(True)
        mt_offset.select_set(True)
        parenter.select_set(True)
        bpy.context.view_layer.objects.active = parenter
        bpy.ops.object.parent_set()

        bpy.ops.object.select_all(action='DESELECT')
        main_ob.select_set(True)
        bpy.context.view_layer.objects.active = main_ob

        mod_id.use_relative_offset = False
        mod_id.use_object_offset = True
        mod_id.offset_object = mt_offset

    l = set_orients()[2]
    p = set_orients()[3]

    main_ob.location[l] -= (self.last_pos * p)
    main_ob.location[l] += (self.modal_radius * p)
    self.last_pos = self.modal_radius

    csr.ofst_radius = self.modal_radius
    last_transf_increment = csr.ofst_radius

    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    offset_empty_name = main_ob_name + "_Offseter"
    offset_empty = bpy.data.objects[offset_empty_name]

    n = set_orients()[0]

    offset_empty.rotation_euler[n] = (2 * pi) / self.modal_count

    bpy.context.object.modifiers["RADarr!"].count = self.modal_count

    csr.dyn_count = self.modal_count
    csr.space_types = self.modal_space_types


def radr_modal_hud(self, context):

    font_path = addon_dir + "/font/WeblySleek.ttf"
    font_info["font_id"] = blf.load(font_path)
    font_id = font_info["font_id"]

    csr = context.scene.rad_array
    radius = csr.ofst_radius
    count = csr.dyn_count

    width = bpy.context.region.width
    height = bpy.context.region.height

    user_pref = bpy.context.preferences.addons[__name__]
    if user_pref.preferences.hud_position == 'ML':
        h_factor = 10
    if user_pref.preferences.hud_position == 'MU':
        h_factor = 1.15

    blf.size(font_id, 16, 75)

    blf.color(font_id, 1, 1, 1, 0.5)
    blf.position(font_id, (width / 2) - 125, height / h_factor, 0)
    blf.draw(font_id, f"{'Radius :'}")

    if 100.00 > radius >= 1.00:
        si_unit = "m"
    elif 1.00 > radius >= 0.10:
        radius *= 100
        si_unit = "cm"
    elif 0.10 > radius >= 0.01:
        radius *= 1000
        si_unit = "mm"
    elif 0.01 > radius >= 1e-5:
        si_unit = "μm"
    else:
        si_unit = " "

    blf.color(font_id, 1, 1, 1, 1)
    blf.position(font_id, (width / 2) - 60, height / h_factor, 0)
    blf.draw(font_id, f"{radius:.2f} {si_unit}")

    blf.color(font_id, 1, 1, 1, 0.5)
    blf.position(font_id, (width / 2) + 30, height / h_factor, 0)
    blf.draw(font_id, f"{'Count :'}")

    blf.color(font_id, 1, 1, 1, 1)
    blf.position(font_id, (width / 2) + 90, height / h_factor, 0)
    blf.draw(font_id, f"{count}")


def partial_fill(self, context):

    global first_run, ori_rot_val
    global main_ob_rot_Z, mt_offset_rot_nor

    n = set_orients()[0]

    main_ob = bpy.context.active_object
    main_ob_name = main_ob.name

    offset_empty_name = main_ob_name + "_Offseter"
    offset_empty = bpy.data.objects[offset_empty_name]

    # if main_ob_rot_Z == 0.00:
    #     if first_run:
    #         ori_rot_val = offset_empty.rotation_euler[n]

    #     factor = self.circum_coverage
    #     rot_val = ori_rot_val * factor
    #     offset_empty.rotation_euler[n] = rot_val

    # else:
    #     if first_run:
    #         ori_rot_val = mt_offset_rot_nor

    #     factor = self.circum_coverage
    #     rot_val = ori_rot_val * factor
    #     offset_empty.rotation_euler[n] = rot_val - mt_offset_rot_nor

    if first_run:
        ori_rot_val = offset_empty.rotation_euler[n]

    factor = self.circum_coverage
    rot_val = ori_rot_val * factor
    offset_empty.rotation_euler[n] = rot_val

    first_run = False


def fibonacci(self, context):

    global init_count

    main_ob = bpy.context.active_object
    main_ob_name = main_ob.name

    offset_empty_name = main_ob_name + "_Offseter"
    offset_empty = bpy.data.objects[offset_empty_name]

    bpy.ops.object.select_all(action='DESELECT')
    offset_empty.hide_viewport = False
    offset_empty.select_set(True)

    init_count = self.dyn_count

    if self.fibo_switch:

        v = 0.948
        bpy.ops.transform.resize(value=(v, v, v))
        main_ob.modifiers["RADarr!"].count = 100

    else:

        main_ob.modifiers["RADarr!"].count = init_count
        bpy.ops.object.scale_clear()

    bpy.ops.object.select_all(action='DESELECT')
    offset_empty.hide_viewport = True
    main_ob.select_set(True)
    bpy.context.view_layer.objects.active = main_ob


def fuse_vert(self, context):

    main_ob = bpy.context.active_object
    subsurf_flag = False

    obj_mod = main_ob.modifiers

    if obj_mod.get("RADarr!"):
        for mod in obj_mod:

            if mod.type == 'SUBSURF':
                subsurf_flag = True
                subsurf_name = mod.name

            if mod.name == "RADarr!":

                if subsurf_flag:
                    subsurf_index = obj_mod.find(subsurf_name)
                    radarr_index = obj_mod.find("RADarr!")

                    if subsurf_index < radarr_index:
                        while obj_mod.find("RADarr!") != subsurf_index:
                            boo = bpy.ops.object
                            boo.modifier_move_up(modifier="RADarr!")

                mod.use_merge_vertices = self.vertex_fusion
                mod.use_merge_vertices_cap = self.vertex_fusion
                mod.merge_threshold = self.merge_proximity


def doff_execute(self, context):

    global ci, co

    main_ob = bpy.context.active_object

    count = context.scene.rad_array.dyn_count

    nor_coords = [
        1.00000000, 0.86602500, 1.00000000,
        0.36327125, 0.57735000, 0.24078700,
        0.41421400, 0.18198500, 0.32492000,
        0.14681300, 0.26795000, 0.12323850,
        0.22824300, 0.10627800, 0.19891300,
        0.09346600, 0.17632800, 0.08343530,
        0.15838430, 0.07536280, 0.14377800,
        0.06872350, 0.13165200,
    ]

    if (count % 2) == 0:
        a = 5.00862 * (0.572758 ** count)
        b = 0.000683887 * (count ** 2)
        c = 0.0354693 * count
        d = 0.591497
    else:
        a = 6.26065 * (0.451568 ** count)
        b = 0.000547214 * (count ** 2)
        c = 0.0251026 * count
        d = 0.359715

    if count < 25:
        x1 = nor_coords[count - 2]
    else:
        x1 = a + b - c + d

    if count < 3:
        y1 = 0
    elif (count % 2) != 0:
        y1 = 0.5
    else:
        y1 = 1

    x2 = x1
    y2 = y1 * -1

    def doff_ops(u, v):

        csr = bpy.context.scene.rad_array

        x = main_ob.location[0]
        y = main_ob.location[1]
        z = main_ob.location[2]

        if csr.orient_modes == 'AUTO':
            consider_view = get_orients()[0]
        else:
            consider_view = csr.orient_axes

        def nor_tuple():

            if (
                consider_view == 'TOP'
                or
                consider_view == 'BOTTOM'
                or
                consider_view == 'ANOMALY'
            ):
                return u, v, 0

            elif (
                consider_view == 'FRONT'
                or
                consider_view == 'BACK'
            ):
                return u, 0, v

            elif (
                consider_view == 'RIGHT'
                or
                consider_view == 'LEFT'
            ):
                return 0, u, v

        if (
            consider_view == 'TOP'
            or
            consider_view == 'BOTTOM'
            or
            consider_view == 'FRONT'
            or
            consider_view == 'RIGHT'
            or
            consider_view == 'ANOMALY'
        ):
            ci = True
            co = False

        elif (
            consider_view == 'BACK'
            or
            consider_view == 'LEFT'
        ):
            ci = False
            co = True

        bpy.ops.mesh.bisect(
            plane_co=(x, y, z),
            plane_no=nor_tuple(),
            clear_inner=ci,
            clear_outer=co
        )

    if operator_doff:
        csr = context.scene.rad_array
    else:
        csr = self

    if (
        csr.vertex_fusion
        and
        csr.remove_excess
    ):

        current_mode = main_ob.mode

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        doff_ops(x1, y1)

        bpy.ops.mesh.select_all(action='SELECT')
        doff_ops(x2, y2)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode=current_mode)


def rad_arr_apply(context):

    main_ob = bpy.context.active_object
    main_ob_name = main_ob.name

    bpy.ops.object.modifier_apply(modifier="RADarr!")
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.select_all(action='DESELECT')

    offset_empty_name = main_ob_name + "_Offseter"
    offset_empty = bpy.data.objects[offset_empty_name]
    offset_empty.hide_viewport = False
    offset_empty.select_set(True)
    bpy.ops.object.delete()

    parent_empty_name = main_ob_name + "_Parenter"
    parent_empty = bpy.data.objects[parent_empty_name]
    parent_empty.select_set(True)
    bpy.ops.object.delete()

    main_ob.select_set(True)
    bpy.context.view_layer.objects.active = main_ob


def get_keymap(km, kmi):

    for i, km_item in enumerate(km.keymap_items):
        if km.keymap_items.keys()[i] == kmi:
            return km_item
    return None


def add_keymap():

    km = kc.keymaps.new(name="Object Mode")
    kmi = km.keymap_items.new(
        "object.modal_rad",
        'R',
        'PRESS',
        shift=True
    )

    user_pref = bpy.context.preferences.addons[__name__]
    if user_pref.preferences.interactive_switch:
        kmi.active = True
    else:
        kmi.active = False

    addon_keymaps.append((km, kmi))

    km = kc.keymaps.new(
        name='3D View',
        space_type='VIEW_3D',
        # modal = False,
    )
    kmi = km.keymap_items.new(
        'view3d.radr_float_ui',
        'E',
        'PRESS',
        # ctrl = True,
        # shift = True
    )

    kmi.active = True

    addon_keymaps.append((km, kmi))


def remove_keymap():

    km = kc.keymaps['Object Mode']

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
        kc.keymaps.remove(km)
    addon_keymaps.clear()


def modal_state_fn():

    with open(modal_file_path, 'r') as f:
        if f.read() == "ON\n":
            modal_state = True
            return True
        else:
            modal_state = False
            return False


def dont_update_fn(self, context):

    if (modal_state_fn() == True):
        pass
    elif (modal_state_fn() == False):
        rad_arr(self, context)


def modal_file_wc(self, context):

    # print(__file__)
    # print(os.path.basename(__file__))

    user_pref = bpy.context.preferences.addons[__name__]
    if user_pref.preferences.interactive_switch:
        with open(modal_file_path, 'w') as f:
            f.write("ON")

        for line in fileinput.input(__file__, inplace=1):
            if fileinput.filelineno() <= 65:
                line = line.replace(
                    'dont_update = False',
                    'dont_update = True'
                )
            print(line.rstrip('\n'))

        # with fileinput.FileInput(__file__, inplace = True) as s_file:
        #     for line in s_file:
        #         print(
        #             line.replace(
        #                 "dont_update = False",
        #                 "dont_update = True"
        #             ),
        #              end = ''
        #         )

    else:
        with open(modal_file_path, 'w') as f:
            f.write("OFF")

        for line in fileinput.input(__file__, inplace=1):
            if fileinput.filelineno() <= 65:
                line = line.replace(
                    'dont_update = True',
                    'dont_update = False'
                )
            print(line.rstrip('\n'))

        # with fileinput.FileInput(__file__, inplace = True) as s_file:
        #     for line in s_file:
        #         print(
        #             line.replace(
        #                 "dont_update = True",
        #                 "dont_update = False"
        #             ),
        #              end = ''
        #         )


class GLOBAL_PG_radr_props_settings(PropertyGroup):

    orient_modes: EnumProperty(
        name="- Oriental Modes -",
        description="Orientation Mode",
        items=[(
            'AUTO',
            "Auto",
            "Orientation is set automatically."
        ),
            (
            'MANUAL',
            "Manual",
            "Orientation is to be set manually."
        )],
        default='MANUAL',
        options={'HIDDEN'}
    )

    orient_axes: EnumProperty(
        name="- Oriental Views -",
        description="Oriented from",
        items=[('TOP', "Top", ""),
               ('FRONT', "Front", ""),
               ('RIGHT', "Right", ""),
               ('LEFT', "Left", ""),
               ('BACK', "Back", ""),
               ('BOTTOM', "Bottom", "")],
        default='TOP',
        options={'HIDDEN'}
    )

    folded_01: BoolProperty(
        default=True
    )

    folded_02: BoolProperty(
        default=True
    )

    update_switch: BoolProperty(
        name="Suspend Update:",
        description=(
            "Temporarily disable add-on UI property update callback"
        ),
        default=True,
        options={'HIDDEN'},
        # update = temp_update
    )

    dyn_count: IntProperty(
        name="Count :",
        description="Number of geo-instances",
        default=1,
        min=1,
        max=36,
        options={'HIDDEN'},
        update=(do_nothing if dont_update else rad_arr)
        # update = dont_update_fn
    )

    ofst_radius: FloatProperty(
        name="Radius :",
        description="Distance from the mt_offset",
        default=0.00,
        min=0.00,
        max=100.00,
        options={'HIDDEN'},
        update=(do_nothing if dont_update else rad_arr)
    )

    space_types: BoolProperty(
        name="Space Type:",
        description=(
            "Switch between World Space and Local Space"
        ),
        default=True,
        options={'HIDDEN'},
        update=rad_arr
    )

    circum_coverage: FloatProperty(
        name="",
        description="Circum-Percentage to be filled",
        default=1.00,
        min=0.00,
        max=1.00,
        options={'HIDDEN'},
        update=partial_fill
    )

    fibo_switch: BoolProperty(
        name="Fibonacci:",
        description=(
            "Toggle Fibonacci On/Off"
        ),
        default=False,
        options={'HIDDEN'},
        update=fibonacci
    )

    radius_range: EnumProperty(
        name="- Radius Range -",
        description="Effective radius in",
        items=[(
            "MM",
            "mm",
            "Interactive radius range in Milimeter unit."
        ),
            (
            "CM",
            "cm",
            "Interactive radius range in Centimeter unit."
        ),
            (
            "METER",
            "m",
            "Interactive radius range in Meter unit."
        )],
        default='METER',
        options={'HIDDEN'}
    )

    vertex_fusion: BoolProperty(
        name="Weld",
        description=(
            "Merge nearby vertices"
        ),
        default=False,
        options={'HIDDEN'},
        update=fuse_vert
    )

    remove_excess: BoolProperty(
        name="Scrap",
        description=(
            "Remove unwanted geometry"
        ),
        default=True,
        options={'HIDDEN'},
        # update = doff_execute
    )

    merge_proximity: FloatProperty(
        name="",
        description="Merge vertices w/i this limit",
        default=0.005,
        min=0.000,
        max=0.015,
        options={'HIDDEN'},
        update=fuse_vert
    )


class OBJECT_OT_modal_rad_arr(Operator):

    bl_idname = "object.modal_rad"
    bl_label = "RADarr (Interactive Mode)"

    modal_radius: FloatProperty(
        default=0.00,
        min=0.00,
        max=50.00
    )

    modal_count: IntProperty(
        default=1,
        min=1,
        max=16
    )

    # si_unit : StringProperty()

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and
            context.object.type == 'MESH'
        )

    def execute(self, context):

        rad_arr_modal(self, context)
        self.modal_op_count += 1

        return {'FINISHED'}

    def invoke(self, context, event):

        global first_run, ori_rot_val

        l = set_orients()[2]
        p = set_orients()[3]

        if context.object:

            self.init_loc_lateral = (context.object.location[l]) * p

            self.modal_op_count = 0
            self.last_pos = 0.00
            self.factor = 0.0000

            bcs = bpy.context.scene
            self.cursorLoc_X = bcs.cursor.location[0]
            self.cursorLoc_Y = bcs.cursor.location[1]
            self.cursorLoc_Z = bcs.cursor.location[2]
            bpy.ops.view3d.snap_cursor_to_selected()

            csr = context.scene.rad_array
            self.modal_space_types = csr.space_types

            self.execute(context)

            user_pref = bpy.context.preferences.addons[__name__]
            if user_pref.preferences.hud_switch:

                args = (self, context)

                btS = bpy.types.SpaceView3D
                self._handle = btS.draw_handler_add(
                    radr_modal_hud,
                    args,
                    'WINDOW',
                    'POST_PIXEL'
                )

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

        else:
            self.report({'WARNING'}, "No active object.")
            return {'CANCELLED'}

    def modal(self, context, event):

        global event_trig
        global first_run, ori_rot_val

        csr = context.scene.rad_array
        bcs = bpy.context.scene

        main_ob = bpy.context.active_object
        main_ob_name = main_ob.name

        context.area.tag_redraw()
        btS = bpy.types.SpaceView3D
        user_pref = bpy.context.preferences.addons[__name__]

        if csr.radius_range == "MM":
            self.factor = 0.0001
        elif csr.radius_range == "CM":
            self.factor = 0.0010
        elif csr.radius_range == "METER":
            self.factor = 0.0100

        if event.type == 'MOUSEMOVE':
            self.modal_radius = event.mouse_x * self.factor
            self.execute(context)

            # self.radius = csr.ofst_radius

            # if 100.00 > self.radius >= 1.00:
            #     self.si_unit = "m"
            # elif 1.00 > self.radius >= 0.10:
            #     self.si_unit = "cm"
            # elif 0.10 > self.radius >= 0.01:
            #     self.si_unit = "mm"
            # elif 0.01 > self.radius >= 1e-5:
            #     self.si_unit = "μm"
            # else:
            #     self.si_unit = " "

        elif event.type == 'WHEELUPMOUSE':
            self.modal_count += 1
            self.execute(context)

        elif (
            event.type == 'ONE' or
            event.type == 'W' or
            event.type == 'RIGHT_BRACKET' or
            event.type == 'UP_ARROW'
        ):
            if event_trig:
                self.modal_count += 1
                event_trig = False
                self.execute(context)
            else:
                event_trig = True

        elif event.type == 'WHEELDOWNMOUSE':
            self.modal_count -= 1
            self.execute(context)

        elif (
            event.type == 'ACCENT_GRAVE' or
            event.type == 'S' or
            event.type == 'LEFT_BRACKET' or
            event.type == 'DOWN_ARROW'
        ):
            if event_trig:
                self.modal_count -= 1
                event_trig = False
                self.execute(context)
            else:
                event_trig = True

        elif event.type == 'LEFTMOUSE':

            bcs.cursor.location[0] = self.cursorLoc_X
            bcs.cursor.location[1] = self.cursorLoc_Y
            bcs.cursor.location[2] = self.cursorLoc_Z

            offset_empty_name = main_ob_name + "_Offseter"
            offset_empty = bpy.data.objects[offset_empty_name]
            offset_empty.hide_viewport = True

            csr.circum_coverage = 1.00
            first_run = True
            ori_rot_val = 0.00

            if user_pref.preferences.hud_switch:
                btS.draw_handler_remove(self._handle, 'WINDOW')

            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:

            l = set_orients()[2]
            p = set_orients()[3]

            main_ob.location[l] = (self.init_loc_lateral - self.last_pos) * p
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

            bcs.cursor.location[0] = self.cursorLoc_X
            bcs.cursor.location[1] = self.cursorLoc_Y
            bcs.cursor.location[2] = self.cursorLoc_Z

            bpy.ops.object.modifier_remove(modifier="RADarr!")

            bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
            bpy.ops.object.select_all(action='DESELECT')

            offset_empty_name = main_ob_name + "_Offseter"
            offset_empty = bpy.data.objects[offset_empty_name]
            offset_empty.select_set(True)
            bpy.ops.object.delete()

            parent_empty_name = main_ob_name + "_Parenter"
            parent_empty = bpy.data.objects[parent_empty_name]
            parent_empty.select_set(True)
            bpy.ops.object.delete()

            main_ob.select_set(True)
            bpy.context.view_layer.objects.active = main_ob
            # bpy.ops.object.rotation_clear()

            csr.dyn_count = 1
            csr.ofst_radius = 0.00

            if user_pref.preferences.hud_switch:
                btS.draw_handler_remove(self._handle, 'WINDOW')

            return {'CANCELLED'}

        return {'RUNNING_MODAL'}


class OBJECT_OT_rad_arr(Operator):

    bl_idname = "object.radial_array"
    bl_label = "Update"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and
            context.object.type == 'MESH'
        )

    def execute(self, context):

        global op_call_flag

        op_call_flag = True
        rad_arr(self, context)
        op_call_flag = False

        return {'FINISHED'}


class PANEL_PT_rad_arr(Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Utilities"
    bl_label = "RADarr"

    def draw(self, context):
        layout = self.layout

        csr = context.scene.rad_array

        box_01 = layout.box()
        col = box_01.column(align=True)

        row = col.row(align=True)

        row.prop(
            csr,
            "folded_01",
            icon=(
                "DISCLOSURE_TRI_DOWN"
                if csr.folded_01
                else "DISCLOSURE_TRI_RIGHT"
            ),
            icon_only=True,
            emboss=False
        )

        row.label(text="Orientation Pref :")

        if csr.folded_01:
            row = col.row(align=True)
            row.prop(
                csr,
                "orient_modes",
                text=' ',
                expand=True
            )
            if csr.orient_modes == 'MANUAL':
                row.prop(
                    csr,
                    "orient_axes",
                    text=""
                )

        elements_01_enabled = False

        if (
            context.active_object is not None
            and
            context.object.type == 'MESH'
        ):
            elements_01_enabled = True

        col = layout.column()
        col.active = elements_01_enabled

        col.use_property_split = True
        # layout.prop(csr, "update_switch")
        col.prop(csr, "ofst_radius")
        col.prop(csr, "dyn_count")

        if dont_update:

            # box_02 = layout.box()
            # row = box_02.row()#align = True)
            # row.label(text = "")
            # sub = row.row()
            # sub.scale_x = 1.5
            # sub.operator("object.radial_array")
            # row.label(text = "")

            layout.separator(factor=0.05)
            # layout.column_flow()

            col = layout.row()

            split = col.split(factor=0.01)
            box_03 = split.column().box()
            row = box_03.row()

            split = col.split(factor=0.01)
            box = split.column().box()
            row = box_03.row()

            split = col.split()
            box_03 = split.column().box()
            row = box_03.row()
            row.operator("object.radial_array")

            split = col.split(factor=0.01)
            box_03 = split.column().box()
            row = box_03.row()

            split = col.split(factor=0.01)
            box_03 = split.column().box()
            row = box_03.row()


class PANEL_PT_rad_arr_sub_panel(Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Extras :"
    bl_parent_id = "PANEL_PT_rad_arr"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout


class PANEL_PT_rad_arr_st_sspanel(Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "-  Space Type"
    bl_parent_id = "PANEL_PT_rad_arr_sub_panel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        main_ob = bpy.context.active_object

        return (
            context.active_object is not None
            and
            main_ob.modifiers.get("RADarr!") is not None
        )

    def draw(self, context):
        layout = self.layout
        # layout.use_property_split = True

        csr = context.scene.rad_array

        if csr.space_types:
            label = 'World Space'
            icn = 'ORIENTATION_GLOBAL'
        else:
            label = 'Local Space'
            icn = 'ORIENTATION_LOCAL'

        layout.prop(
            csr,
            "space_types",
            text=label,
            icon=icn,
            toggle=True
        )


class PANEL_PT_rad_arr_cf_sspanel(Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "-  Partial Span"
    bl_parent_id = "PANEL_PT_rad_arr_sub_panel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        main_ob = bpy.context.active_object

        return (
            context.active_object is not None
            and
            main_ob.modifiers.get("RADarr!") is not None
        )

    def draw(self, context):
        layout = self.layout
        # layout.use_property_split = True

        csr = context.scene.rad_array

        layout.prop(
            csr,
            "circum_coverage",
            text='Circum Factor',
            slider=True
        )


class PANEL_PT_rad_arr_fibo_sspanel(Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "-  Fibonacci  [Beta]"
    bl_parent_id = "PANEL_PT_rad_arr_sub_panel"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        main_ob = bpy.context.active_object

        return (
            context.active_object is not None
            and
            main_ob.modifiers.get("RADarr!") is not None
        )

    def draw(self, context):
        layout = self.layout
        # layout.use_property_split = True

        csr = context.scene.rad_array

        if csr.fibo_switch:
            label = 'Activated'
        else:
            label = 'Deactivated'

        layout.prop(
            csr,
            "fibo_switch",
            text=label,
            toggle=True
        )


class PANEL_PT_rad_arr_rr_sspanel(Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "-  Radius Limits"
    bl_parent_id = "PANEL_PT_rad_arr_sub_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        # layout.use_property_split = True

        csr = context.scene.rad_array

        layout.prop(
            csr,
            "radius_range",
            text='Units :',
            expand=True
        )


class OBJECT_OT_rad_arr_scrap(Operator):

    bl_idname = "object.rad_scrap"
    bl_label = "Scrap"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        main_ob = bpy.context.active_object
        csr = context.scene.rad_array
        return (
            context.active_object is not None
            and
            main_ob.modifiers.get("RADarr!") is not None
            and
            csr.vertex_fusion
            and
            csr.dyn_count > 1
            # and
            # csr.dyn_count < 25
        )

    def execute(self, context):

        doff_execute(self, context)

        return {'FINISHED'}


class OBJECT_OT_rad_arr_apply(Operator):

    bl_idname = "object.rad_apply"
    bl_label = "Apply MOD"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        main_ob = bpy.context.active_object
        return (
            context.active_object is not None
            and
            main_ob.modifiers.get("RADarr!") is not None
        )

    def execute(self, context):

        rad_arr_apply(context)

        return {'FINISHED'}


class PANEL_PT_rad_apply_sub_panel(Panel):

    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Appertain :"
    bl_parent_id = "PANEL_PT_rad_arr"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        csr = context.scene.rad_array

        box_01 = layout.box()
        col = box_01.column(align=True)

        row = col.row(align=True)
        row.label(text="Mesh Level Ops -")
        col = box_01.column()

        main_ob = bpy.context.active_object
        elements_02_enabled = False

        if (
            context.active_object is not None
            and
            main_ob.modifiers.get("RADarr!") is not None
        ):

            elements_02_enabled = True

        row = col.row(align=True)
        row.enabled = elements_02_enabled
        row.prop(csr, "vertex_fusion")

        sub = row.row()
        sub.scale_x = 0.95
        # sub.prop(csr, "remove_excess")
        sub.operator("object.rad_scrap")

        sub = col.row()
        sub.active = csr.vertex_fusion
        sub.prop(
            csr,
            "merge_proximity",
            text='Fuse Contiguity ',
            slider=True
        )

        box_02 = layout.box()
        row = box_02.row()
        row.operator("object.rad_apply")


class VIEW3D_OT_radr_float_ui(Operator):
    bl_idname = "view3d.radr_float_ui"
    bl_label = "RADarr (Floating Panel)"

    def execute(self, context):
        return {'INTERFACE'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(
            self,
            width=200
        )

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="---------------------------------------------")

        row = col.row(align=True)
        row.label(text="-  Main Operator Panel  -")

        csr = context.scene.rad_array

        box_01 = layout.box()
        col = box_01.column(align=True)

        row = col.row(align=True)

        row.prop(
            csr,
            "folded_01",
            icon=(
                "DISCLOSURE_TRI_DOWN"
                if csr.folded_01
                else "DISCLOSURE_TRI_RIGHT"
            ),
            icon_only=True,
            emboss=False
        )

        row.label(text="Orientation Pref :")

        if csr.folded_01:
            row = col.row(align=True)
            row.prop(
                csr,
                "orient_modes",
                text=' ',
                expand=True
            )
            if csr.orient_modes == 'MANUAL':
                row.prop(
                    csr,
                    "orient_axes",
                    text=""
                )

        elements_01_enabled = False

        if (
            context.active_object is not None
            and
            context.object.type == 'MESH'
        ):
            elements_01_enabled = True

        col = layout.column()
        col.active = elements_01_enabled

        col.use_property_split = True
        # col.use_property_decorate = True
        # layout.prop(csr, "update_switch")
        col.prop(csr, "ofst_radius")
        col.prop(csr, "dyn_count")

        if dont_update:

            # box_02 = layout.box()
            # row = box_02.row()#align = True)
            # row.label(text = "")
            # sub = row.row()
            # sub.scale_x = 1.5
            # sub.operator("object.radial_array")
            # row.label(text = "")

            layout.separator(factor=0.05)
            # layout.column_flow()

            col = layout.row()

            split = col.split(factor=0.01)
            box_03 = split.column().box()
            row = box_03.row()

            split = col.split(factor=0.01)
            box = split.column().box()
            row = box_03.row()

            split = col.split()
            box_03 = split.column().box()
            row = box_03.row()
            row.operator("object.radial_array")

            split = col.split(factor=0.01)
            box_03 = split.column().box()
            row = box_03.row()

            split = col.split(factor=0.01)
            box_03 = split.column().box()
            row = box_03.row()

        col = layout.column(align=True)
        col.label(text="---------------------------------------------")

        row = col.row(align=True)
        row.label(text="-  Appertain  -")

        box_01 = layout.box()
        col = box_01.column(align=True)

        row = col.row(align=True)
        row.label(text="Mesh Level Ops -")
        col = box_01.column()

        main_ob = bpy.context.active_object
        elements_02_enabled = False

        if (
            context.active_object is not None
            and
            main_ob.modifiers.get("RADarr!") is not None
        ):

            elements_02_enabled = True

        row = col.row(align=True)
        row.enabled = elements_02_enabled
        row.prop(csr, "vertex_fusion")

        sub = row.row()
        sub.scale_x = 0.95
        # sub.prop(csr, "remove_excess")
        sub.operator("object.rad_scrap")

        sub = col.row()
        sub.active = csr.vertex_fusion
        sub.prop(
            csr,
            "merge_proximity",
            text='Fuse Contiguity ',
            slider=True
        )

        box_02 = layout.box()
        row = box_02.row()
        row.operator("object.rad_apply")


class RADARR_PF_save_quit(Operator):

    bl_idname = "pref.save_quit"
    bl_label = "Save Preferences & Quit"
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(cls, context):
    #     main_ob = bpy.context.active_object
    #     return (
    #         context.active_object is not None
    #         and
    #         main_ob.modifiers.get("RADarr!") is not None
    #     )

    def execute(self, context):
        bpy.ops.wm.save_userpref()
        bpy.ops.wm.quit_blender()
        return {'FINISHED'}


class INFO_OT_keymap_add(Operator):

    bl_idname = "info.keymap_add"
    bl_label = " "
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        add_keymap()

        self.report(
            {'INFO'},
            "Hotkey Added : "
            "Preferences > Keymap"
        )
        return {'FINISHED'}


class RADARR_PF_pref(AddonPreferences):

    bl_idname = __name__

    interactive_switch: BoolProperty(
        name="Interactive Mode : ON / OFF",
        description=(
            "This turns off the interactive behavior in the viewport"
        ),
        default=modal_state_fn(),
        update=modal_file_wc
    )

    hud_switch: BoolProperty(
        name="HUD Switch",
        description=(
            "Toggle on/off HUD when interactive mode is in action"
        ),
        default=True,
        # update =
    )

    hud_position: EnumProperty(
        name="HUD Locator ",
        description="HUD Positioned At",
        items=[
            ("ML", "Mid-Lower", ""),
            ("MU", "Mid-Upper", "")],
        default='ML',
    )

    radius_range_limit: EnumProperty(
        name="Radius Limit ",
        description="Modal effective range",
        items=[
            ("MM", "in Milimeters", ""),
            ("CM", "in Centimeters", ""),
            ("METER", "in Meters", "")],
        default='MM',
    )

    max_count_limit: IntProperty(
        name="Extended Count Limit ",
        description="Extending the max count limit",
        default=36,
        min=36,
        max=100,
        # update =
    )

    def draw(self, context):

        layout = self.layout

        wm = bpy.context.window_manager
        kc = wm.keyconfigs.user

        layout.separator()

        box_00 = layout.box()
        box_00.label(text="-  3D-Viewport Interactive Mode (IM) Settings  -")
        row = box_00.row()

        row.use_property_split = True

        if self.interactive_switch:
            modal_switch_txt = 'Interactive Mode Is Active !'
        else:
            modal_switch_txt = 'Interactive Mode Is OFF Now'

        row.prop(
            self, "interactive_switch",
            text=modal_switch_txt
        )

        if self.interactive_switch == dont_update:
            row.label(text="")

        if self.interactive_switch != dont_update:
            row.label(
                text="Needs A Restart To Work !",
                icon='INFO',
            )
            # row.label(icon = 'INFO')
            row = box_00.row()
            row.label(text="")
            row.operator("pref.save_quit")
            row.label(text="")

        km = kc.keymaps['Object Mode']
        kmi = get_keymap(
            km,
            "object.modal_rad"
        )

        if self.interactive_switch:

            box_01 = box_00.box()
            row = box_01.row()
            row.label(text="   IM Keybindings  :")
            row = box_01.row()

            if kmi:
                row = box_01.row()
                row.context_pointer_set("keymap", km)
                rna_keymap_ui.draw_kmi([], kc, km, kmi, row, 1)

            else:
                row = box_01.row()
                row.label(
                    icon='INFO',
                    text="Info: No Keymap Is Assigned"
                )
                row.operator(
                    INFO_OT_keymap_add.bl_idname,
                    icon='ADD',
                    text="Add A Default Keymap"
                )

            if self.hud_switch:
                hud_button_txt = "Status : ON"
            else:
                hud_button_txt = "Status : OFF"

            row = box_01.row()
            row = box_01.row()
            row.label(text="   IM Heads-Up Display  :")

            col = box_01.column(align=True)
            row = col.row(align=True)

            row.label(text="")
            row.prop(
                self, "hud_switch",
                text=hud_button_txt,
                toggle=True
            )
            # row.label(text = "HUD Position")
            row.active = self.hud_switch
            # row = row.row(align = True)
            row.label(text="")
            row.label(text="Dispalyed At :")
            row.prop(self, "hud_position", text="")
            row.label(text="")

        layout.separator()

        box_02 = layout.box()
        row = box_02.row()
        row.label(text="-  Floating Panel (FP) Settings  -")
        row = box_02.row()
        box_03 = box_02.box()
        row = box_03.row()
        row.label(text="   FP Keybindings  :")
        row = box_03.row()

        km = kc.keymaps['3D View']
        kmi = get_keymap(
            km,
            "view3d.radr_float_ui"
        )

        if kmi:
            row = box_03.row()
            row.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, row, 1)

        else:
            row = box_03.row()
            row.label(
                icon='INFO',
                text="Info: No Keymap Is Assigned"
            )
            row.operator(
                INFO_OT_keymap_add.bl_idname,
                icon='ADD',
                text="Add A Default Keymap"
            )


classes = (
    GLOBAL_PG_radr_props_settings,
    OBJECT_OT_modal_rad_arr,
    OBJECT_OT_rad_arr,
    PANEL_PT_rad_arr,
    PANEL_PT_rad_arr_sub_panel,
    PANEL_PT_rad_arr_st_sspanel,
    PANEL_PT_rad_arr_cf_sspanel,
    PANEL_PT_rad_arr_fibo_sspanel,
    PANEL_PT_rad_arr_rr_sspanel,
    OBJECT_OT_rad_arr_scrap,
    OBJECT_OT_rad_arr_apply,
    PANEL_PT_rad_apply_sub_panel,
    VIEW3D_OT_radr_float_ui,
    RADARR_PF_save_quit,
    INFO_OT_keymap_add,
    RADARR_PF_pref
)


def register():

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.rad_array = PointerProperty(
        type=GLOBAL_PG_radr_props_settings
    )

    add_keymap()


def unregister():

    remove_keymap()

    del(bpy.types.Scene.rad_array)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()

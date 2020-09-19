# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "BakeLab",
    "author" : "Shahzod Boyxonov (specoolar@gmail.com)",
    "description" : "Bake textures easily",
    "blender" : (2, 81, 0),
    "version" : (2, 0, 0),
    "location" : "View3D > Properties > BakeLab",
    "category" : "Baking"
}

if "bpy" in locals():
    import importlib
    importlib.reload(bakelab_bake)
    importlib.reload(bakelab_uv)
    importlib.reload(bakelab_baked_data)
    importlib.reload(bakelab_post)
    importlib.reload(bakelab_map)
    importlib.reload(bakelab_ui)
else:
    from . import bakelab_bake
    from . import bakelab_uv
    from . import bakelab_baked_data
    from . import bakelab_post
    from . import bakelab_map
    from . import bakelab_ui

import bpy

from bpy.types import (
            Operator, 
            PropertyGroup, 
            Panel
        )
from bpy.props import (
            IntProperty,
            EnumProperty,
            BoolProperty,
            FloatProperty,
            StringProperty,
            PointerProperty,
            CollectionProperty
        )
from os.path import expanduser

def updateAdaptiveImageMinSize(self, context):
    self.image_min_size = min(self.image_min_size, self.image_max_size)

def updateAdaptiveImageMaxSize(self, context):
    self.image_max_size = max(self.image_min_size, self.image_max_size)

def updateSavePath(self, context):
    if bpy.data.is_saved:
        self.save_path = bpy.path.abspath("//")

class BakeLabProperties(PropertyGroup):
    bake_state: EnumProperty(
            items = (
                ("NONE",   "None",   ""),
                ("BAKING", "Baking", ""),
                ("BAKED",  "Baked",  "")
            ),
            default = "NONE"
        )
    bake_mode: EnumProperty(
            name = "Mode",
            description = 'Baking mode',
            items = (
                ("INDIVIDUAL", "Individual Objects", "", "PIVOT_INDIVIDUAL", 1),
                ("ALL_TO_ONE", "All To One Image",   "", "PROP_ON", 2),
                ("TO_ACTIVE",  "Selected to active", "", "PIVOT_ACTIVE", 3)
            ),
            default = "INDIVIDUAL"
        )
    cage_extrusion : FloatProperty(
            name = 'Cage Extrusion', default = 0.05,
            min = 0, soft_max = 1
        )
    image_size : EnumProperty(
            name = 'Image Size',
            items = (
                ('FIXED',    'Fixed',    "Fixed image size"),
                ('ADAPTIVE', 'Adaptive', "Image size by object's surface area")
            ),
            default = 'FIXED'
        )
    adaptive_image_Settings : BoolProperty(
            name = '',
            default = True
        )
    texel_per_unit : FloatProperty(
            name = 'Texels Per Unit',
            default = 100,
            min = 0
        )
    image_min_size    : IntProperty(
            name = 'Min Size',
            default = 32,
            min = 1,
            update=updateAdaptiveImageMaxSize
        )
    image_max_size    : IntProperty(
            name = 'Max Size',
            default = 2048,
            min = 1,
            update=updateAdaptiveImageMinSize
        )
    round_adaptive_image : BoolProperty(
        name = 'Round to power of two', 
        default = True
    )
    anti_alias : IntProperty(
            name = 'Anti-aliasing', default = 1,
            description = 'Anti-aliasing (1 = No Anti-aliasing)',
            min = 1, soft_max = 8
        )
    bake_margin    : IntProperty(
            name = 'Bake Margin',
            description = 'Extends the baked result as a post process filter',
            default = 16,
            min = 0,
            soft_max = 64
        )
    global_image_name  : StringProperty(
            name = 'Image Name',
            description = 'Names of baked images',
            default = "Atlas",
        )
    compute_device : EnumProperty(
            name = 'Device',
            description = 'Compute Device',
            items =  (
                ('GPU','GPU Compute',''),
                ('CPU','CPU','')
            )
        )
    save_or_pack : EnumProperty(
                name  = 'Output',
                items =  (
                    ('PACK','Pack',''),
                    ('SAVE','Save','')
                ),
                default = 'PACK'
            )
    save_path : StringProperty(
                default=expanduser("~"),
                name="Folder",
                subtype="FILE_PATH",
                update=updateSavePath
            )
    show_bake_settings : BoolProperty(name = '', default = False)
    show_map_settings  : BoolProperty(name = '', default = False)
    show_file_settings : BoolProperty(name = '', default = False)
    
    apply_only_selected : BoolProperty(
        name = 'Apply only to Selected',
        description = 'Apply only to selected objects',
        default = True
    )
    make_single_user : BoolProperty(
        name = 'Make single user',
        description = 'Make data single user',
        default = True
    )
    # Display
    baking_obj_count : IntProperty(
            name = 'Baking object count',
            default = 0
        )
    baking_obj_index : IntProperty(
            name = 'Current baking object',
            default = 0
        )
    baking_obj_name : StringProperty(
            name = 'Current baking object',
            default = ""
        )
    baking_map_count : IntProperty(
            name = 'Baking map count',
            default = 0
        )
    baking_map_index : IntProperty(
            name = 'Current baking map',
            default = 0
        )
    baking_map_type : StringProperty(
            name = 'Current baking map type',
            default = ""
        )
    baking_map_name : StringProperty(
            name = 'Current baking image',
            default = ""
        )
    baking_map_size : StringProperty(
            name = 'Current baking size',
            default = ""
        )

classes = (
    BakeLabProperties,
    
    bakelab_bake.Baker,
    bakelab_uv.Unwrapper,
    bakelab_uv.ClearUV,
    bakelab_post.BakeLab_GenerateMaterials,
    bakelab_post.BakeLab_ApplyAO,
    bakelab_post.BakeLab_ApplyDisplace,
    bakelab_post.BakeLab_Finish,
    bakelab_map.BakeLabMap,
    bakelab_map.BakeLabAddMapItem,
    bakelab_map.BakeLabRemoveMapItem,
    bakelab_map.BakeLabMapListUI,
    bakelab_baked_data.BakeObjData,
    bakelab_baked_data.BakeMapData,
    bakelab_baked_data.BakeLab_BakedData,
    bakelab_map.BakeLabShowPassPresets,
    bakelab_ui.BakeLabUI
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.Scene.BakeLabProps = PointerProperty(type = BakeLabProperties)
    bpy.types.Scene.BakeLabMaps = CollectionProperty(type = bakelab_map.BakeLabMap)
    bpy.types.Scene.BakeLab_Data = CollectionProperty(type = bakelab_baked_data.BakeLab_BakedData)
    bpy.types.Scene.BakeLabMapIndex = IntProperty(name = 'BakeLab Map List Index')

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.BakeLabProps
    del bpy.types.Scene.BakeLabMaps
    del bpy.types.Scene.BakeLab_Data
    del bpy.types.Scene.BakeLabMapIndex

if __name__ == "__main__":
    register()

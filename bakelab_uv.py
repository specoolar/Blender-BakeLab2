import bpy
from bpy.types import (
            Operator
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
from .bakelab_tools import (
    SelectObject,
    SelectObjects,
    IsValidMesh
)

def SelectObject(obj):
    bpy.ops.object.select_all(action = 'DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
class Unwrapper(Operator):
    """Unwrap"""
    bl_idname = "bakelab.unwrap"
    bl_label = "Unwrap"
    bl_options = {'REGISTER','UNDO'}
          
    unwrap_method      : EnumProperty(
            name = 'Unwrap Method',
            items =  (
                ('smart_uv','Smart Project',''),
                ('lightmap_uv','LightMap Project','')
            ),
            default='smart_uv'
        )          
    unwrap_mode   : EnumProperty(
            name = 'Unwrap Mode',
            items =  (
                ('INDIVIDUAL',         'All Individual', ''),
                ('ALL_TO_ONE',    'All Into One', ''),
                ('ONLY_ACTIVE', 'Only Active',  '')
            )
        )
                    
    smart_uv_angle   : FloatProperty(
                name = 'Angle',
                description = 'Angle Limit',
                default = 66,
                min = 1,
                max = 89
            )
    smart_uv_margin  : FloatProperty(
                name = 'Margin',
                description = 'Island Margin',
                default = 0.03,
                min = 0,
                max = 1
            )
                    
    lightmap_quality : IntProperty(
                name = 'Quality',
                description = 'Pack Quality',
                default = 12,
                min = 1,
                max = 48
            )
    lightmap_margin  : FloatProperty(
                name = 'Margin',
                description = 'Margin',
                default = 0.3,
                min = 0,
                max = 1
            )

    uvmap_options : EnumProperty(
            name = 'UVMaps',
            items =  (
                ('CREATE_NEW', 'Create New',''),
                ('RE_UNWRAP',  'Unwrap active UV map','')
            ),
            default = 'CREATE_NEW'
        )
    uvmap_options_individual : EnumProperty(
            name = 'UVMaps',
            items =  (
                ('CREATE_NEW', 'Create New',           'Create and Unwrap new UV Map'),
                ('IF_MISSING', 'Unwrap if missing',    'Create and Unwrap only if object has no UV Maps'),
                ('RE_UNWRAP',  'Unwrap active UV map', 'Unwrap existing UV maps (Create if does not exist)')
            ),
            default = 'CREATE_NEW'
        )
    default_uv_name      : StringProperty(
            name = 'Default UV Name',
            description = 'New UV Layer name',
            default = 'BakeUVMap'
        )
    check_uv_name     : BoolProperty(
        name = 'Check UV name',
        description = "Don't create new if object has UV with same name",
        default = True
    )
    apply_modifiers  : BoolProperty(
        name = 'Apply Modifiers',
        default = True
    )
    make_single_user  : BoolProperty(
        name = 'Make data single user',
        default = True
    )
    make_single_user_view  : BoolProperty(
        name = 'Make data single user',
        default = True
    )
    
    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        layout.prop(self, "unwrap_mode")
        if self.unwrap_mode == 'INDIVIDUAL':
            layout.prop(self, "uvmap_options_individual")
            layout.prop(self, "default_uv_name")
            if self.uvmap_options_individual == 'CREATE_NEW':
                layout.prop(self, "check_uv_name")
        else:
            layout.prop(self, "uvmap_options")
            layout.prop(self, "default_uv_name")
            if self.uvmap_options == 'CREATE_NEW':
                layout.prop(self, "check_uv_name")
                
        layout.prop(self, "apply_modifiers")
        
        lock_make_single_user = False
        if self.apply_modifiers:
            lock_make_single_user = True
        if self.unwrap_mode == 'ALL_TO_ONE':
            lock_make_single_user = True
            
        if lock_make_single_user:
            col = layout.column()
            col.enabled = False
            col.prop(self, "make_single_user_view")
        else:
            layout.prop(self, "make_single_user")
        
        layout.separator()
            
        layout.prop(self, "unwrap_method")
        if self.unwrap_method == 'smart_uv':
            layout.prop(self, "smart_uv_angle")
            layout.prop(self, "smart_uv_margin")
        if self.unwrap_method == 'lightmap_uv':
            layout.prop(self, "lightmap_quality")
            layout.prop(self, "lightmap_margin")
            
    def Unwrap(self, context):
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action = 'SELECT')
        
        if self.unwrap_method == 'smart_uv':
            bpy.ops.uv.smart_project(
                angle_limit = self.smart_uv_angle,
                island_margin = self.smart_uv_margin
            )
        elif self.unwrap_method == 'lightmap_uv':
            bpy.ops.uv.lightmap_pack(
                PREF_BOX_DIV = self.lightmap_quality,
                PREF_MARGIN_DIV = self.lightmap_margin
            )
        bpy.ops.object.mode_set(mode = 'OBJECT')
        
    def modifier_apply(self, context, obj):
        active_object    = context.active_object
        selected_objects = context.selected_objects
        
        SelectObject(obj)
        if obj.data.users > 1:
            bpy.ops.object.make_single_user(object=True,obdata=True)
        
        for modifier in obj.modifiers:
            if modifier.show_render:
                if modifier.type == 'SUBSURF':
                    modifier.levels = modifier.render_levels
                bpy.ops.object.modifier_apply(modifier = modifier.name)
        
        SelectObjects(active_object, selected_objects)
    
    def execute(self,context):
        active_object    = context.active_object
        selected_objects = context.selected_objects
        mesh_objects = [obj for obj in selected_objects if IsValidMesh(self, obj)]
        if len(mesh_objects) == 0:
            self.report(type = {'ERROR'}, message = 'No mesh objects selected')
            return {'CANCELLED'}
        ############################################################################
        if self.unwrap_mode == 'INDIVIDUAL':
            SelectObjects(mesh_objects[0], mesh_objects)
            if self.make_single_user:
                bpy.ops.object.make_single_user(object=True, obdata=True)
                unwrap_objects = mesh_objects
            else:
                unwrap_objects = []
                unwrap_datas = []
                for obj in mesh_objects:
                    if obj.data in unwrap_datas:
                        continue
                    unwrap_objects.append(obj)
                    unwrap_datas.append(obj.data)
            
            for obj in unwrap_objects:
                SelectObject(obj)
                
                if self.apply_modifiers:
                    self.modifier_apply(context, obj)
                
                if self.uvmap_options_individual == 'CREATE_NEW':
                    if self.check_uv_name and self.default_uv_name in obj.data.uv_layers:
                        obj.data.uv_layers.active = obj.data.uv_layers[self.default_uv_name]
                    else:
                        obj.data.uv_layers.active = obj.data.uv_layers.new(name = self.default_uv_name)
                    self.Unwrap(context)
                elif self.uvmap_options_individual == 'IF_MISSING':
                    if len(obj.data.uv_layers) == 0:
                        obj.data.uv_layers.new(name = self.default_uv_name)
                        self.Unwrap(context)
                elif self.uvmap_options_individual == 'RE_UNWRAP':
                    self.Unwrap(context)
                        
                
        ############################################################################
        elif self.unwrap_mode == 'ONLY_ACTIVE':
            if active_object.type != 'MESH':
                self.report(type = {'ERROR'}, message = 'Active object is not mesh')
                SelectObjects(active_object, selected_objects)
                return {'CANCELLED'}
            
            SelectObject(active_object)
            
            if self.make_single_user:
                bpy.ops.object.make_single_user(object=True,obdata=True)
                
            if self.apply_modifiers:
                self.modifier_apply(context, active_object)
            
            if self.uvmap_options == 'CREATE_NEW':
                if self.check_uv_name  and  self.default_uv_name in active_object.data.uv_layers:
                    active_object.data.uv_layers.active = active_object.data.uv_layers[self.default_uv_name]
                else:
                    active_object.data.uv_layers.active = active_object.data.uv_layers.new(name = self.default_uv_name)
            
            self.Unwrap(context)
            
        ############################################################################
        elif self.unwrap_mode == 'ALL_TO_ONE':
            SelectObjects(mesh_objects[0], mesh_objects)
            bpy.ops.object.make_single_user(object=True, obdata=True)
            
            if self.uvmap_options == 'CREATE_NEW':
                for obj in mesh_objects:
                    if self.apply_modifiers:
                        self.modifier_apply(context, obj)
                    if self.check_uv_name  and  self.default_uv_name in obj.data.uv_layers:
                        obj.data.uv_layers.active = obj.data.uv_layers[self.default_uv_name]
                    else:
                        obj.data.uv_layers.active = obj.data.uv_layers.new(name = self.default_uv_name)
            
            self.Unwrap(context)
        ############################################################################
        SelectObjects(active_object, selected_objects)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        props = context.scene.BakeLabProps
        if props.bake_mode == 'INDIVIDUAL':
            self.unwrap_mode = 'INDIVIDUAL'
        if props.bake_mode == 'ALL_TO_ONE':
            self.unwrap_mode = 'ALL_TO_ONE'
        if props.bake_mode == 'TO_ACTIVE':
            self.unwrap_mode = 'ONLY_ACTIVE'
        self.make_single_user_view = True
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
        
class ClearUV(Operator):
    """Clear UVs"""
    bl_idname = "bakelab.clear_uv"
    bl_label = "Clear UV"
    bl_options = {'REGISTER','UNDO'}
    
    save_active  : BoolProperty(
        name = 'Save Active',
        default = True
    )
    save_active_render  : BoolProperty(
        name = 'Save Active Render',
        default = True
    )
    
    def execute(self,context):
        mesh_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        if len(mesh_objects) == 0:
            self.report(type = {'ERROR'}, message = 'No mesh objects selected')
            return {'CANCELLED'}

        for obj in mesh_objects:
            remove_uvs = []
            for uv in obj.data.uv_layers:
                if uv == obj.data.uv_layers.active and self.save_active:
                    continue
                if uv.active_render and self.save_active_render:
                    continue
                remove_uvs.append(uv)
            for uv in remove_uvs:
                obj.data.uv_layers.remove(uv)
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
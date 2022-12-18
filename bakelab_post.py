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
    SelectObjects
)

class BakeLab_GenerateMaterials(Operator):
    """Generate materials based on baked datas"""
    bl_idname = "bakelab.generate_mats"
    bl_label = "Generate Materials"
    bl_options = {'REGISTER','UNDO'}
            
    def generate_mat(self, bakeMapData, name):
        new_mat = bpy.data.materials.new(name+'_BAKED')
        new_mat.use_nodes = True
        if self.add_nodes(bakeMapData, new_mat):
            return new_mat
        else:
            bpy.data.materials.remove(new_mat)
            return None
        
    def add_nodes(self, bakeMapData, mat):
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        for node in nodes:
            nodes.remove(node)
        
        out = nodes.new(type = 'ShaderNodeOutputMaterial')
        out.location = 0, 0
        pbr = nodes.new(type = 'ShaderNodeBsdfPrincipled')
        pbr.location = -400, 0
        links.new(pbr.outputs[0],out.inputs[0])
        uvm = nodes.new(type = 'ShaderNodeTexCoord')
        uvm.location = -1800, 0
        
        pass_available = False
        node_y_shift = 0
        for data in bakeMapData:
            bake_map = data.bake_map
            bake_image = data.image
            
            if bake_map.type != 'CustomPass' and bake_map.type in self.baked_types:
                continue
            self.baked_types.append(bake_map.type)
            
            if bake_map.type == 'Albedo':
                imgNode = nodes.new(type = 'ShaderNodeTexImage')
                imgNode.hide = True
                imgNode.location = -1000,-100
                imgNode.image = bake_image
                links.new(imgNode.outputs[0], pbr.inputs[0])
                links.new(uvm.outputs[2], imgNode.inputs[0])
                pass_available = True
            if bake_map.type == 'Combined':
                imgNode = nodes.new(type = 'ShaderNodeTexImage')
                imgNode.hide = True
                imgNode.location = -1000, 300
                imgNode.image = bake_image
                EmitNode = nodes.new(type = 'ShaderNodeEmission')
                EmitNode.location = -400, 300
                EmitNode.width = pbr.width
                EmitNode.hide = True
                links.new(imgNode.outputs[0], EmitNode.inputs[0])
                links.new(EmitNode.outputs[0], out.inputs[0])
                links.new(uvm.outputs[2], imgNode.inputs[0])
                pass_available = True
            if bake_map.type == 'Normal':
                imgNode = nodes.new(type = 'ShaderNodeTexImage')
                imgNode.hide = True
                imgNode.location = -1000, -500
                imgNode.image = bake_image
                nmNode = nodes.new(type = 'ShaderNodeNormalMap')
                nmNode.hide = True
                nmNode.location = -700, -500
                nmNode.space = bake_map.normal_space
                links.new(imgNode.outputs[0], nmNode.inputs[1])
                links.new(nmNode.outputs[0], pbr.inputs[22])
                links.new(uvm.outputs[2], imgNode.inputs[0])
                pass_available = True
            if bake_map.type == 'AO':
                out.location[0] += 250
                imgNode = nodes.new(type = 'ShaderNodeTexImage')
                imgNode.hide = True
                imgNode.location = -1000, 150
                imgNode.image = bake_image
                reroute = nodes.new(type = 'NodeReroute')
                reroute.location = -150, 150
                ao_mix = nodes.new(type = 'ShaderNodeMixShader')
                ao_mix.location = 0, 0
                ao_dark = nodes.new(type = 'ShaderNodeEmission')
                ao_dark.label = 'Dark'
                ao_dark.location = -400, 100
                ao_dark.width = pbr.width
                ao_dark.hide = True
                ao_dark.inputs[0].default_value = 0,0,0,0
                ao_dark.inputs[1].default_value = 0
                
                links.new(uvm.outputs[2],imgNode.inputs[0])
                links.new(imgNode.outputs[0], reroute.inputs[0])
                links.new(reroute.outputs[0], ao_mix.inputs[0])
                links.new(ao_dark.outputs[0], ao_mix.inputs[1])
                links.new(pbr.outputs[0],     ao_mix.inputs[2])
                links.new(ao_mix.outputs[0],     out.inputs[0])
                pass_available = True
            if bake_map.type == 'Glossy':
                imgNode = nodes.new(type = 'ShaderNodeTexImage')
                imgNode.hide = True
                imgNode.location = -1000, -200
                imgNode.image = bake_image
                links.new(imgNode.outputs[0],pbr.inputs[7])
                links.new(uvm.outputs[2],imgNode.inputs[0])
                pass_available = True
            if bake_map.type == 'Roughness':
                imgNode = nodes.new(type = 'ShaderNodeTexImage')
                imgNode.hide = True
                imgNode.location = -1000, -250
                imgNode.image = bake_image
                links.new(imgNode.outputs[0],pbr.inputs[9])
                links.new(uvm.outputs[2],imgNode.inputs[0])
                pass_available = True
            if bake_map.type == 'Transmission':
                imgNode = nodes.new(type = 'ShaderNodeTexImage')
                imgNode.hide = True
                imgNode.location = -1000, -900
                imgNode.image = bake_image
                links.new(imgNode.outputs[0],pbr.inputs[15])
                links.new(uvm.outputs[2],imgNode.inputs[0])
                pass_available = True
                
            ###### Custom Passes{
            if bake_map.type == 'CustomPass':
                ####### Find Pass Input Socket{
                split_passes = bake_map.pass_name.split(',')
                for i in range(len(split_passes)):
                    split_passes[i] = split_passes[i].strip().casefold()
                
                pass_input = None
                for Pass in split_passes:
                    for tmp_input in pbr.inputs:
                        if tmp_input.name.casefold() == Pass:
                            pass_input = tmp_input
                            break
                # }
                if pass_input:
                    if len(pass_input.links) == 0:
                        imgNode = nodes.new(type = 'ShaderNodeTexImage')
                        imgNode.hide = True
                        imgNode.location = -1400,node_y_shift
                        imgNode.image = bake_image
                        links.new(imgNode.outputs[0], pass_input)
                        links.new(uvm.outputs[2],imgNode.inputs[0])
                        node_y_shift -= 100
                    pass_available = True
                ####### }
            ###### }
        return pass_available
    
    def execute(self, context):
        props = context.scene.BakeLabProps
        active_obj = context.active_object
        selected_objects = context.selected_objects
        baked_data = context.scene.BakeLab_Data
        
        materials_created = False
        for data in baked_data:
            if data == None:
                continue
            self.baked_types = []
            name = context.scene.BakeLabProps.global_image_name
            if len(data.obj_list) == 1:
                if data.obj_list[0].obj != None:
                    name = data.obj_list[0].obj.name
            if len(data.obj_list) == 0:  # Just in case
                continue
            
            mat = self.generate_mat(data.map_list, name)
            if mat is None:
                continue
            
            materials_created = True
            
            for objData in data.obj_list:
                obj = objData.obj
                if obj == None:
                    continue
                
                if 'Normal' in self.baked_types:
                    obj.data.use_auto_smooth = False
                
                if props.apply_only_selected:
                    if obj not in selected_objects:
                        continue
                
                SelectObject(obj)
                if props.make_single_user:
                    bpy.ops.object.make_single_user(object=True, obdata=True)
                if obj.data.uv_layers.active is not None:
                    obj.data.uv_layers.active.active_render = True
                for slot in obj.material_slots:
                    slot.material = mat
        SelectObjects(active_obj, selected_objects)
        
        if materials_created:
            return {'FINISHED'}
        else:
            self.report(type = {'ERROR'}, message = 'No valid baked images to create materials')
            return {'CANCELLED'}
    
class BakeLab_ApplyAO(Operator):
    """Add ambient occlusion materials"""
    bl_idname = "bakelab.apply_ao"
    bl_label = "Apply AO"
    bl_options = {'REGISTER','UNDO'}
        
    def add_ao(self, bake_image, mat):
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        out = None
        for node in nodes:
            if node.type == 'OUTPUT_MATERIAL':
                out = node
                break
        if out == None:
            return
        
        if len(out.inputs) == 0:
            return
        if len(out.inputs[0].links) == 0:
            return
        bsdf = out.inputs[0].links[0].from_node
        
        
        uvm = nodes.new(type = 'ShaderNodeTexCoord')
        uvm.hide = True
        uvm.width = bsdf.width
        uvm.location = bsdf.location[0], bsdf.location[1]+160
        
        imgNode = nodes.new(type = 'ShaderNodeTexImage')
        imgNode.hide = True
        imgNode.width = bsdf.width
        imgNode.location = bsdf.location[0], bsdf.location[1]+100
        imgNode.image = bake_image
        
        ao_mix = nodes.new(type = 'ShaderNodeMixShader')
        ao_mix.location = out.location[:]
        out.location[0] += 200
        ao_dark = nodes.new(type = 'ShaderNodeEmission')
        ao_dark.label = 'Dark'
        ao_dark.location = bsdf.location[0], bsdf.location[1]+50
        ao_dark.width = bsdf.width
        ao_dark.hide = True
        ao_dark.inputs[0].default_value = 0,0,0,0
        ao_dark.inputs[1].default_value = 0
        
        links.new(uvm.outputs[2],imgNode.inputs[0])
        links.new(imgNode.outputs[0], ao_mix.inputs[0])
        links.new(ao_dark.outputs[0], ao_mix.inputs[1])
        links.new(bsdf.outputs[0],    ao_mix.inputs[2])
        links.new(ao_mix.outputs[0],  out.inputs[0])
    
    def execute(self, context):
        props = context.scene.BakeLabProps
        active_obj = context.active_object
        selected_objects = context.selected_objects
        baked_data = context.scene.BakeLab_Data
        
        materials_modified = False
        for data in baked_data:
            if data == None:
                continue
            for mapData in data.map_list:
                if mapData.bake_map == None:
                    continue
                if mapData.bake_map.type != 'AO':
                    continue
                
                for objData in data.obj_list:
                    obj = objData.obj
                    if obj == None:
                        continue
                    if props.apply_only_selected:
                        if obj not in selected_objects:
                            continue
                    
                    SelectObject(obj)
                    if props.make_single_user:
                        bpy.ops.object.make_single_user(object=True, obdata=True)
                    
                    if obj.data.uv_layers.active is not None:
                        obj.data.uv_layers.active.active_render = True
                    
                    if len(obj.material_slots) == 0:
                        bpy.ops.object.material_slot_add()
                    for slot in obj.material_slots:
                        if slot.material == None:
                            slot.material = bpy.data.materials.new(obj.name+'_AO')
                            slot.material.use_nodes = True
                        if slot.material.users > 1:
                            mat_name = slot.material.name
                            slot.material = slot.material.copy()
                            slot.material.name = mat_name + '_' + obj.name + '_AO'
                        self.add_ao(mapData.image, slot.material)
                        materials_modified = True
                break
        
        SelectObjects(active_obj, selected_objects)
        if materials_modified:
            return {'FINISHED'}
        else:
            self.report(type = {'ERROR'}, message = 'No valid baked images or objects to add AO')
            return {'CANCELLED'}
    
class BakeLab_ApplyDisplace(Operator):
    """Apply material displacement as real geometry"""
    bl_idname = "bakelab.apply_displace"
    bl_label = "Apply Displacement"
    bl_options = {'REGISTER','UNDO'}
        
    def add_displacement(self, texture, obj):
        mod = obj.modifiers.new(name = 'Displacement', type = 'DISPLACE')
        mod.direction = 'RGB_TO_XYZ'
        mod.texture_coords = 'UV'
        mod.texture = texture
        mod.show_in_editmode = True
        mod.show_on_cage = True
    
    def execute(self, context):
        props = context.scene.BakeLabProps
        baked_data = context.scene.BakeLab_Data
        objects_modified = False
        for data in baked_data:
            if data == None:
                continue
            for mapData in data.map_list:
                if mapData.bake_map == None:
                    continue
                if mapData.bake_map.type != 'Displacement':
                    continue

                name = context.scene.BakeLabProps.global_image_name
                if len(data.obj_list) == 1:
                    if data.obj_list[0].obj != None:
                        name = data.obj_list[0].obj.name
                tex = bpy.data.textures.new(name = name, type = 'IMAGE')
                tex.intensity = 1.5
                tex.image = mapData.image
                
                for objData in data.obj_list:
                    obj = objData.obj
                    if obj == None:
                        continue
                    if props.apply_only_selected:
                        if not obj.select_get():
                            continue
                    
                    self.add_displacement(tex, obj)
                    objects_modified = True
                break
        
        if objects_modified:
            return {'FINISHED'}
        else:
            self.report(type = {'ERROR'}, message = 'No valid baked images or objects to add Displacement')
            return {'CANCELLED'}

class BakeLab_Finish(Operator):
    """Finish"""
    bl_label = "Finish"
    bl_idname = "bakelab.finish"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.BakeLabProps
        context.scene.BakeLab_Data.clear()
        props.bake_state = 'NONE'
        return {'FINISHED'}

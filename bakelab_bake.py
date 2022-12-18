import os
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

from math import log2
from os.path import abspath, join, exists

from .bakelab_tools import (
    SelectObject,
    SelectObjects,
    IsValidMesh
)
    
class Baker(Operator):
    """Bake"""
    bl_label = "BakeLab Bake"
    bl_info = "BakeLab"
    bl_idname = "bakelab.bake"
    bl_options = {'REGISTER', 'UNDO'}
    
    _timer = None
    TMP_EMPTY_MAT_NAME = "BAKELAB_TMP_EMPTY_MAT"
    TMP_IMAGE_NODE_NAME = "BAKELAB_TMP_IMAGE_NODE"
    
    def save_defaults(self, context):
        scene = context.scene
        render = scene.render
        
        # Image settings{
        img_settings = render.image_settings
        self.default_image_format = img_settings.file_format
        self.default_color_mode   = img_settings.color_mode
        self.default_color_depth  = img_settings.color_depth
        
        self.default_compression  = img_settings.compression
        self.default_quality      = img_settings.quality
        self.default_exr_codec    = img_settings.exr_codec
        # }
        
        # Scene settings{
        self.default_active_object = context.active_object
        self.default_selected_objects = context.selected_objects
        self.default_engine = render.engine
        self.default_cycles_device = scene.cycles.device
        self.default_cycles_pause = scene.cycles.preview_pause
        # }
        
        # Bake settings{
        bake_settings = context.scene.render.bake
        self.default_use_s2a = bake_settings.use_selected_to_active
        self.default_use_clear = bake_settings.use_clear
        self.default_use_cage = bake_settings.use_cage
        self.default_cage_extrusion = bake_settings.cage_extrusion
        self.default_bake_margin    = bake_settings.margin
        self.default_samples = scene.cycles.samples
        self.default_normal_space = bake_settings.normal_space
        
        self.default_use_pass_direct   = bake_settings.use_pass_direct
        self.default_use_pass_indirect = bake_settings.use_pass_indirect
        self.default_use_pass_color    = bake_settings.use_pass_color
        
        self.default_use_pass_diffuse  = bake_settings.use_pass_diffuse
        self.default_use_pass_glossy   = bake_settings.use_pass_glossy
        self.default_use_pass_trans    = bake_settings.use_pass_transmission
        #self.default_use_pass_sss      = bake_settings.use_pass_subsurface # No Longer in 2.83
        #self.default_use_pass_ao       = bake_settings.use_pass_ambient_occlusion # No Longer in 3.0
        self.default_use_pass_emit     = bake_settings.use_pass_emit
    
        self.default_use_cage          = bake_settings.use_cage
        self.default_cage_extrusion    = bake_settings.cage_extrusion
        self.default_cage_object       = bake_settings.cage_object
        # }
        
    def restore_defaults(self, context):
        scene = context.scene
        render = scene.render
        
        # Image settings{
        img_settings = render.image_settings
        img_settings.file_format         = self.default_image_format
        img_settings.color_mode          = self.default_color_mode
        img_settings.color_depth         = self.default_color_depth
        
        img_settings.compression         = self.default_compression
        img_settings.quality             = self.default_quality
        img_settings.exr_codec           = self.default_exr_codec
        # }
        
        # Scene settings{
        SelectObjects(self.default_active_object, self.default_selected_objects)
        render.engine = self.default_engine
        scene.cycles.device = self.default_cycles_device
        scene.cycles.preview_pause = self.default_cycles_pause
        # }
        
        # Bake settings{
        bake_settings = context.scene.render.bake
        bake_settings.use_selected_to_active = self.default_use_s2a
        bake_settings.use_clear = self.default_use_clear
        bake_settings.use_cage = self.default_use_cage
        bake_settings.cage_extrusion = self.default_cage_extrusion
        bake_settings.margin  = self.default_bake_margin
        scene.cycles.samples = self.default_samples
        bake_settings.normal_space             = self.default_normal_space
        
        bake_settings.use_pass_direct          = self.default_use_pass_direct
        bake_settings.use_pass_indirect        = self.default_use_pass_indirect
        bake_settings.use_pass_color           = self.default_use_pass_color
    
        bake_settings.use_pass_diffuse           = self.default_use_pass_diffuse
        bake_settings.use_pass_glossy            = self.default_use_pass_glossy
        bake_settings.use_pass_transmission      = self.default_use_pass_trans
        #bake_settings.use_pass_subsurface        = self.default_use_pass_sss # No Longer in 2.83
        #bake_settings.use_pass_ambient_occlusion = self.default_use_pass_ao # No Longer in 3.0
        bake_settings.use_pass_emit              = self.default_use_pass_emit
    
        bake_settings.use_cage                 = self.default_use_cage
        bake_settings.cage_extrusion           = self.default_cage_extrusion
        bake_settings.cage_object              = self.default_cage_object
        # }
    
    def passes_to_rgb(self, node, src_socket, nodes, links, passes):
        has_bsdf_inputs = False
        for input in node.inputs:
            if input.type == 'SHADER':
                has_bsdf_inputs = True
                if len(input.links):
                    self.passes_to_rgb(input.links[0].from_node, input,
                                    nodes, links, passes)
        
        if not has_bsdf_inputs:
            emit = nodes.new(type = 'ShaderNodeEmission')
            emit.inputs[0].default_value = 0, 0, 0, 0
            links.new(emit.outputs[0], src_socket)
            ####### Find Pass Input Socket{
            pass_input = None
            for Pass in passes:
                for tmp_input in node.inputs:
                    if tmp_input.name.casefold() == Pass:
                        pass_input = tmp_input
                        break
            ####### }
            if pass_input:
                if len(pass_input.links):
                    links.new(pass_input.links[0].from_socket, emit.inputs[0])
                else:
                    if   pass_input.type == 'RGBA':
                        emit.inputs[0].default_value[0] = pass_input.default_value[0]
                        emit.inputs[0].default_value[1] = pass_input.default_value[1]
                        emit.inputs[0].default_value[2] = pass_input.default_value[2]
                        emit.inputs[0].default_value[3] = pass_input.default_value[3]
                    elif pass_input.type == 'VECTOR':
                        emit.inputs[0].default_value[0] = pass_input.default_value[0]
                        emit.inputs[0].default_value[1] = pass_input.default_value[1]
                        emit.inputs[0].default_value[2] = pass_input.default_value[2]
                        emit.inputs[0].default_value[3] = 1
                    elif pass_input.type == 'VALUE':
                        emit.inputs[0].default_value[0] = pass_input.default_value
                        emit.inputs[0].default_value[1] = pass_input.default_value
                        emit.inputs[0].default_value[2] = pass_input.default_value
                        emit.inputs[0].default_value[3] = 1
    
    def passes_to_emit_node(self, mat, passes):
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        out = self.find_node(nodes, 'OUTPUT_MATERIAL')
            
        if out:
        #### Modify Nodes
            split_passes = passes.split(',')
            for i in range(len(split_passes)):
                split_passes[i] = split_passes[i].strip().casefold()
            self.passes_to_rgb(out, None, nodes, links, split_passes)
        else:
        #### Create Default Texture Nodes
            out = nodes.new(type = 'ShaderNodeOutputMaterial')
            emit = nodes.new(type = 'ShaderNodeEmission')
            emit.inputs[0].default_value = 0, 0, 0, 0
            links.new(emit.outputs[0], out.inputs[0])
            
    def copy_node(self, dst_nodes, node):
        try:
            new_node = dst_nodes.new(type = node.bl_idname)
        except:
            return None
        for member in dir(node):
            try:
                value = getattr(node, member)
                if value is None:
                    continue
                setattr(new_node, member, value)
            except:
                pass
        for src_input in node.inputs:
            dst_input = self.get_socket(new_node.inputs, src_input.identifier)
            if dst_input is not None:
                if hasattr(src_input, 'default_value') and \
                        hasattr(dst_input, 'default_value'):
                    dst_input.default_value = src_input.default_value
        return new_node
    
    def find_node(self, nodes, type):
        for node in nodes:
            if node.type == type:
                if type == "OUTPUT_MATERIAL":
                    if node.is_active_output:
                        return node
                else:
                    return node
        return None
    
    def get_socket(self, sockets, identifier):
        for socket in sockets:
            if socket.identifier == identifier:
                return socket
        return None
    
    def extract_nodes_rc(
                self, gr_node, gr_in, gr_out,
                nodes, links, n_group, node_dict):
        if gr_node.name in node_dict:
            return node_dict[gr_node.name]
        
        node = self.copy_node(nodes, gr_node)
        node_dict[gr_node.name] = node
        
        if node is None:
            return None
        
        ### Inputs {
        for src_input in gr_node.inputs:
            dst_input = self.get_socket(node.inputs, src_input.identifier)
            if dst_input is None:
                continue
            for link in src_input.links:
                from_node = link.from_node
                
                if from_node == gr_in:
                    ng_input = self.get_socket(n_group.inputs, link.from_socket.identifier)
                    if ng_input is None:
                        continue
                    dst_input.default_value = ng_input.default_value
                    for ng_link in ng_input.links:
                        links.new(ng_link.from_socket, dst_input)
                else:
                    link_node = self.extract_nodes_rc(
                        from_node, gr_in, gr_out,
                        nodes, links, n_group, node_dict)
                    if link_node is not None:
                        link_output = self.get_socket(link_node.outputs, link.from_socket.identifier)
                        if link_output is not None:
                            links.new(link_output, dst_input)
        ### }
        ### Outputs {
        for src_output in gr_node.outputs:
            dst_output = self.get_socket(node.outputs, src_output.identifier)
            if dst_output is None:
                continue
            for link in src_output.links:
                to_node = link.to_node
                
                if to_node == gr_out:
                    ng_output = self.get_socket(n_group.outputs, link.to_socket.identifier)
                    if ng_output is None:
                        continue
                    for ng_link in ng_output.links:
                        links.new(dst_output, ng_link.to_socket)
                else:
                    link_node = self.extract_nodes_rc(
                        to_node, gr_in, gr_out,
                        nodes, links, n_group, node_dict)
                    if link_node is not None:
                        link_input = self.get_socket(link_node.inputs, link.to_socket.identifier)
                        if link_input is not None:
                            links.new(dst_output, link_input)
        ### }
        return node
    
    def ungroup_nodes(self, node_tree):
        nodes = node_tree.nodes
        links = node_tree.links
        while True:
            group_exists = False
            ungroup_nodes = [n for n in nodes]
            for node in ungroup_nodes:
                if node.type != 'GROUP':
                    continue
                group_exists = True
                
                node_dict = {}
                gr_nodes = node.node_tree.nodes
                gr_in  = self.find_node(gr_nodes, 'GROUP_INPUT')
                gr_out = self.find_node(gr_nodes, 'GROUP_OUTPUT')
                if gr_in is None: continue
                if gr_out is None: continue
                
                for gr_node in gr_nodes:
                    if gr_node == gr_in:
                        continue
                    if gr_node == gr_out:
                        continue
                    self.extract_nodes_rc(
                        gr_node, gr_in, gr_out,
                        nodes, links, node, node_dict)
                node_dict.clear()
                nodes.remove(node)
            if not group_exists:
                break
            
    def displacement_to_color(self, mat):
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        out = self.find_node(nodes, 'OUTPUT_MATERIAL')
        if out == None:
            return

        if len(out.inputs[2].links) == 0:
            emit = nodes.new(type = 'ShaderNodeEmission')
            emit.inputs[0].default_value = 0, 0, 0, 0
            links.new(emit.outputs[0], out.inputs[0])
        else:
            from_socket = out.inputs[2].links[0].from_socket
            v_transform = nodes.new(type = 'ShaderNodeVectorTransform')
            links.remove(out.inputs[2].links[0])
            
            links.new(from_socket, v_transform.inputs[0])
            links.new(v_transform.outputs[0], out.inputs[0])
    
    def init_bake_settings(self, context, map):
        context.scene.cycles.samples = map.samples
        bake_settings = context.scene.render.bake
        bake_settings.normal_space             = map.normal_space
        
        if map.type == 'Combined':
            bake_settings.use_pass_direct            = map.combined_direct
            bake_settings.use_pass_indirect          = map.combined_indirect
    
            bake_settings.use_pass_diffuse           = map.combined_diffuse
            bake_settings.use_pass_glossy            = map.combined_glossy
            bake_settings.use_pass_transmission      = map.combined_transmission
            #bake_settings.use_pass_subsurface        = map.combined_subsurface
            #bake_settings.use_pass_ambient_occlusion = map.combined_ambient_occlusion
            bake_settings.use_pass_emit              = map.combined_emit
        else:
            bake_settings.use_pass_direct          = map.bake_direct
            bake_settings.use_pass_indirect        = map.bake_indirect
            bake_settings.use_pass_color           = map.bake_color
        
        m_type = map.type
        if m_type == 'Albedo':
            bake_type = 'EMIT'
        if m_type == 'Combined':
            bake_type = 'COMBINED'
        if m_type == 'AO':
            bake_type = 'AO'
        if m_type == 'Displacement':
            bake_type = 'EMIT'
        if m_type == 'Shadow':
            bake_type = 'SHADOW'
        if m_type == 'Normal':
            bake_type = 'NORMAL'
        if m_type == 'UV':
            bake_type = 'UV'
        if m_type == 'Roughness':
            bake_type = 'ROUGHNESS'
        if m_type == 'Emission':
            bake_type = 'EMIT'
        if m_type == 'Environment':
            bake_type = 'ENVIRONMENT'
        if m_type == 'Diffuse':
            bake_type = 'DIFFUSE'
        if m_type == 'Glossy':
            bake_type = 'GLOSSY'
        if m_type == 'Subsurface':
            bake_type = 'TRANSMISSION'
        if m_type == 'CustomPass':
            bake_type = 'EMIT'
        return bake_type
    
    def calc_surf_area(self, obj):
        import bmesh
        bm = bmesh.new(use_operators=False)
        bm.from_mesh(obj.data)
        bm.transform(obj.matrix_world)
        bm.faces.ensure_lookup_table()
        
        area = 0.0
        for face in bm.faces:
            area += face.calc_area()
        return area
    
    def round_to_power_of_2(self, num):
        return pow(2,round(log2(num)))
    
    def PrepareImage(self, context, map, objs, name):
        props = context.scene.BakeLabProps
        self.SetSaveImageSettings(context, map)
        
        if props.image_size == 'FIXED':
            map.target_width  = map.width
            map.target_height = map.height
        elif props.image_size == 'ADAPTIVE':
            area = 0
            for obj in objs:
                area += self.calc_surf_area(obj)
            size = pow(area, 0.5) * props.texel_per_unit
            if props.round_adaptive_image:
                size = self.round_to_power_of_2(size)
            map.target_width  = size
            map.target_height = size
            
        map.final_aa = props.anti_alias
        if map.aa_override > 0:
            map.final_aa = map.aa_override
        bake_image = bpy.data.images.new(
            name = map.img_name.replace('*', name),
            width  = map.target_width  * map.final_aa, 
            height = map.target_height * map.final_aa
        )
        bake_image.use_generated_float = map.float_depth
        try:
            bake_image.colorspace_settings.name = map.color_space
        except:
            try:
                if map.color_space == 'sRGB':
                    bake_image.colorspace_settings.name = 'sRGB EOTF'
                elif map.color_space == 'Non-Color':
                    bake_image.colorspace_settings.name = 'Non-Colour Data'
            except:
                self.report(type = {'WARNING'}, message = "Couldn't change color space of image")
        
        context.scene.render.bake.margin = props.bake_margin * map.final_aa
        if props.save_or_pack == 'PACK':
            bake_image.pack()
        else:
            extension = "."
            if map.file_format == 'PNG':
                extension = '.png'
            if map.file_format == 'JPEG':
                extension = '.jpg'
            if map.file_format == 'OPEN_EXR':
                extension = '.exr'
            
            abs_save_path = bpy.path.abspath(props.save_path)
            if not os.path.isdir(abs_save_path):
                os.makedirs(abs_save_path, 0o777)
            
            if props.create_folder:
                if props.bake_mode == "ALL_TO_ONE":
                    bake_image.filepath = abspath(join(abs_save_path, props.folder_name, bake_image.name + extension))
                else:
                    bake_image.filepath = abspath(join(abs_save_path, name, bake_image.name + extension))
            else:
                bake_image.filepath = abspath(join(abs_save_path, bake_image.name + extension))
            
            bake_image.save_render(bake_image.filepath)
        
        return bake_image
    
    def SetSaveImageSettings(self, context, map):
        img_settings = context.scene.render.image_settings
        img_settings.file_format = map.file_format
        
        if map.file_format == 'PNG':
            img_settings.color_mode  = map.png_channels
            img_settings.color_depth = map.png_depth
            img_settings.compression = map.png_compression
        if map.file_format == 'JPEG':
            img_settings.color_mode = map.jpg_channels
            img_settings.quality    = map.jpg_quality
        if map.file_format == 'OPEN_EXR':
            img_settings.color_mode = map.exr_channels
            img_settings.color_depth = map.exr_depth
            if map.exr_depth == '32':
                img_settings.exr_codec    = map.exr_codec_32
            if map.exr_depth == '16':
                img_settings.exr_codec    = map.exr_codec_16
    
    def ReserveMaterials(self, obj):
        selected_objects = bpy.context.selected_objects
        active_object    = bpy.context.active_object
        
        SelectObject(obj)
        if len(obj.material_slots) == 0:
            bpy.ops.object.material_slot_add()
        for slot in obj.material_slots:
            self.object_slots.append(slot)
            self.original_materials.append(slot.material)
            if slot.material is not None:
                slot.material = slot.material.copy()
        
        SelectObjects(active_object,selected_objects)
        
        return (self.object_slots, self.original_materials)
    
    def RestoreMaterials(self):
        for i in range(0, min(len(self.object_slots), len(self.original_materials))):
            if self.object_slots[i] is not None:
                if self.object_slots[i].material is not None:
                    bpy.data.materials.remove(self.object_slots[i].material)
                self.object_slots[i].material = self.original_materials[i]
        self.object_slots.clear()
        self.original_materials.clear()
    
    def PrepareMaterials(self, context, dst_obj, src_obj_list, map, bake_image):
        active_obj = context.active_object
        selected_objects = context.selected_objects
        
        for obj in src_obj_list:
            SelectObject(obj)
            if len(obj.material_slots) == 0:
                bpy.ops.object.material_slot_add()
            for slot in obj.material_slots:
                if slot.material is None:
                    slot.material = self.GetEmptyMaterial()
                mat = slot.material
                mat.use_nodes = True
                
                if map.type == 'CustomPass':
                    if map.deep_search:
                        self.ungroup_nodes(mat.node_tree)
                    self.passes_to_emit_node(mat, map.pass_name)
                if map.type == 'Albedo':
                    self.ungroup_nodes(mat.node_tree)
                    self.passes_to_emit_node(mat, 'Albedo,Color,Base Color,Col,Paint Color')
                if map.type == 'Displacement':
                    self.displacement_to_color(mat)
                    
        ###################
        
        SelectObject(dst_obj)
        if len(dst_obj.material_slots) == 0:
            bpy.ops.object.material_slot_add()
        for slot in dst_obj.material_slots:
            if slot.material is None:
                slot.material = self.GetEmptyMaterial()
            mat = slot.material
            mat.use_nodes = True
            if self.TMP_IMAGE_NODE_NAME in mat.node_tree.nodes:
                img_node = mat.node_tree.nodes[self.TMP_IMAGE_NODE_NAME]
            else:
                img_node = mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
                img_node.name = self.TMP_IMAGE_NODE_NAME
            mat.node_tree.nodes.active = img_node
            img_node.image = bake_image
            
        SelectObjects(active_obj, selected_objects)
            
    def GetEmptyMaterial(self):
        mat = bpy.data.materials.new(self.TMP_EMPTY_MAT_NAME)
        mat.use_nodes = True
        img_node = mat.node_tree.nodes.new(type = 'ShaderNodeTexImage')
        img_node.name = self.TMP_IMAGE_NODE_NAME
        return mat
    
    def create_merged_object(self, context, object_list):
        ##### Create New Object{
        merged_mesh = bpy.data.meshes.new('BAKELAB_MERGED_MESH_TMP')
        merged_obj  = bpy.data.objects.new('BAKELAB_MERGED_OBJ_TMP', merged_mesh)
        merged_obj.location = 0, 0, 0
        context.scene.collection.objects.link(merged_obj)
        merged_mesh.update()
        ##### }
        
        for obj in object_list:
            SelectObject(obj)
            bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
            obj_clone = context.active_object
            
            #### Apply modifiers{
            for modifier in obj_clone.modifiers:
                if modifier.show_render:
                    if modifier.type == 'SUBSURF':
                        modifier.levels = modifier.render_levels
                    bpy.ops.object.modifier_apply(modifier = modifier.name)
            ##### }
            
            #### Merge{
            SelectObject(merged_obj)
            obj_clone.select_set(True)
            
            clone_data = obj_clone.data
            bpy.ops.object.join()
            bpy.data.meshes.remove(clone_data)
            #### }
        
        while len(merged_obj.material_slots)>0:
            bpy.ops.object.material_slot_remove()
        merged_mesh.update()
        return merged_obj
    
    def down_scale(self, img, props, map):
        if map.final_aa == 1:
            return
        img.scale(map.target_width, map.target_height)
    
    def UpdateDisplayStatus(self, props, obj, map, image):
        props.baking_obj_name = obj.name
        if map.type == 'CustomPass':
            props.baking_map_type = map.pass_name + '(Custom Pass)'
        else:
            props.baking_map_type = map.type
        props.baking_map_name = image.name
        props.baking_map_size = str(map.target_width) + 'x' + str(map.target_height)
        if map.final_aa != 1:
            props.baking_map_size += str(' (' + str(map.final_aa)+'X)')
    
    def Bake(self, context):
        yield 1
        scene = context.scene
        render = scene.render
        props = scene.BakeLabProps
        self.original_materials = []
        self.object_slots = []
        self.save_defaults(context)
        
        props.bake_state = 'BAKING'
        scene.render.engine = 'CYCLES'
        scene.cycles.device = props.compute_device
        scene.cycles.preview_pause = True
        scene.render.bake.use_cage = True
        scene.render.bake.cage_extrusion = props.cage_extrusion
        scene.render.bake.cage_object = None
        
        
        if len(self.default_selected_objects) == 0:
            self.report(type = {'ERROR'}, message = 'Select some objects')
            yield -1
        selected_objects = [obj for obj in self.default_selected_objects if IsValidMesh(self, obj)]
        active_object = self.default_active_object
        if len(selected_objects) == 0:
            self.report(type = {'ERROR'}, message = 'No valid objects selected, see console for more info')
            yield -1
            
        if len(scene.BakeLabMaps) == 0:
            self.report(type = {'ERROR'}, message = 'Add bake maps')
            yield -1
        
        props.baking_map_index = 0
        props.baking_obj_index = 0
        props.baking_map_count = 0
        for map in scene.BakeLabMaps:
            if map.enabled:
                props.baking_map_count += 1
        props.baking_obj_count = len(selected_objects)
        
        ##########################################################################################
        if props.bake_mode == "INDIVIDUAL":
            for obj in selected_objects:
                if len(obj.data.uv_layers) == 0:
                    self.report(type = {'ERROR'}, message = 'Not all objects have UV maps')
                    yield -1
                    
            render.bake.use_selected_to_active = False
            
            for obj in selected_objects:
                # Save baking data {
                baked_data = scene.BakeLab_Data.add()
                baked_data.AddObj(obj)
                # }
                props.baking_obj_index += 1
                SelectObject(obj)
                props.baking_map_index = 0
                for map in scene.BakeLabMaps:
                    if not map.enabled:
                        continue
                    props.baking_map_index += 1
                    
                    self.ReserveMaterials(obj)
                    bake_image = self.PrepareImage(context, map, {obj}, obj.name)
                    self.PrepareMaterials(context, obj, {obj}, map, bake_image)
                    bake_type = self.init_bake_settings(context, map)
                    
                    self.UpdateDisplayStatus(props,obj,map,bake_image)
                    
                    # Bake {
                    while bpy.ops.object.bake('INVOKE_DEFAULT', type = bake_type) != {'RUNNING_MODAL'}:
                        yield 1
                    while not bake_image.is_dirty:
                        yield 1
                    # }

                    self.down_scale(bake_image, props, map)
                    if props.save_or_pack == 'PACK':
                        bake_image.pack()
                    else:
                        bake_image.save_render(bake_image.filepath)
                    
                    baked_data.AddMap(map, bake_image) # Save baking data
                    self.RestoreMaterials()
        ##########################################################################################
        elif props.bake_mode == "ALL_TO_ONE":
             # Check UVs {
            for obj in selected_objects:
                if len(obj.data.uv_layers) == 0:
                    self.report(type = {'ERROR'}, message = 'Not all objects have UV maps')
                    yield -1
            # }
            
             # Save baking data {
            baked_data = scene.BakeLab_Data.add()
            for obj in selected_objects:
                baked_data.AddObj(obj)
            # }
            
            if props.pre_join_mesh:
                render.bake.use_selected_to_active = True
                render.bake.use_cage = True
                render.bake.cage_extrusion = props.cage_extrusion
            
                merged_object = self.create_merged_object(context, selected_objects)
                SelectObjects(merged_object, selected_objects)
            else:
                render.bake.use_selected_to_active = False
                
            props.baking_map_index = 0
            
            for map in scene.BakeLabMaps:
                if not map.enabled:
                    continue
                props.baking_map_index += 1
                
                if props.pre_join_mesh:
                    for obj in selected_objects:
                        self.ReserveMaterials(obj)
                    
                    bake_image = self.PrepareImage(context, map, {merged_object}, props.global_image_name)
                    self.PrepareMaterials(context, merged_object, selected_objects, map, bake_image)
                    bake_type = self.init_bake_settings(context, map)
                    
                    self.UpdateDisplayStatus(props,obj,map,bake_image)
                    
                    # Bake {
                    while bpy.ops.object.bake('INVOKE_DEFAULT', type = bake_type) != {'RUNNING_MODAL'}:
                        yield 1
                    while not bake_image.is_dirty:
                        yield 1
                    # }

                    self.RestoreMaterials()

                    self.down_scale(bake_image, props, map)
                    if props.save_or_pack == 'PACK':
                        bake_image.pack()
                    else:
                        bake_image.save_render(bake_image.filepath)
                else:
                    render.bake.use_clear = False
                    bake_image = self.PrepareImage(context, map, selected_objects, props.global_image_name)
                    for obj in selected_objects:
                        SelectObject(obj)
                        self.ReserveMaterials(obj)
                        
                        self.PrepareMaterials(context, obj, {obj}, map, bake_image)
                        bake_type = self.init_bake_settings(context, map)
                        
                        self.UpdateDisplayStatus(props, obj, map, bake_image)
                        
                        # Bake {
                        while bpy.ops.object.bake('INVOKE_DEFAULT', type = bake_type) != {'RUNNING_MODAL'}:
                            yield 1
                        while not bake_image.is_dirty:
                            yield 1
                        # }
                        
                        if props.save_or_pack == 'PACK':
                            bake_image.pack()
                        else:
                            bake_image.save_render(bake_image.filepath)
                        
                        self.RestoreMaterials()

                    self.down_scale(bake_image, props, map)
                    if props.save_or_pack == 'PACK':
                        bake_image.pack()
                    else:
                        bake_image.save_render(bake_image.filepath)
                    
                baked_data.AddMap(map, bake_image) # Save baking data

            if props.pre_join_mesh:
                merged_data = merged_object.data
                bpy.data.objects.remove(merged_object)
                bpy.data.meshes.remove(merged_data)
        ##########################################################################################
        elif props.bake_mode == "TO_ACTIVE":
            if len(selected_objects) < 2:
                self.report(type = {'ERROR'}, message = 'Select atleast two mesh objects')
                yield -1
            if active_object.type != 'MESH':
                self.report(type = {'ERROR'}, message = 'Active object is not mesh type')
                yield -1
            if len(active_object.data.uv_layers) == 0:
                self.report(type = {'ERROR'}, message = 'Active object does not have UV maps')
                yield -1
                
            render.bake.use_selected_to_active = True
            render.bake.use_cage = True
            render.bake.cage_extrusion = props.cage_extrusion
            
             # Save baking data {
            baked_data = scene.BakeLab_Data.add()
            baked_data.AddObj(active_object)
            # }
            
            SelectObjects(active_object, selected_objects)
                
            props.baking_map_index = 0
                
            for map in scene.BakeLabMaps:
                if not map.enabled:
                    continue
                props.baking_map_index += 1
                
                for obj in selected_objects:
                    self.ReserveMaterials(obj)
                
                bake_image = self.PrepareImage(context, map, {active_object}, active_object.name)
                self.PrepareMaterials(
                    context, 
                    active_object, 
                    [obj for obj in selected_objects 
                        if obj is not active_object], 
                    map, 
                    bake_image
                )
                bake_type = self.init_bake_settings(context, map)
                
                self.UpdateDisplayStatus(props,obj,map,bake_image)
                
                # Bake {
                while bpy.ops.object.bake('INVOKE_DEFAULT', type = bake_type) != {'RUNNING_MODAL'}:
                    yield 1
                while not bake_image.is_dirty:
                    yield 1
                # }

                self.down_scale(bake_image, props, map)
                if props.save_or_pack == 'PACK':
                    bake_image.pack()
                else:
                    bake_image.save_render(bake_image.filepath)
                
                baked_data.AddMap(map, bake_image) # Save baking data
                self.RestoreMaterials()
        ##########################################################################################
        props.bake_state = 'BAKED'
        yield 0 #Done
        
    
    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            self.cancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if context.scene.BakeLabProps.bake_state == 'BAKING':
                context.area.tag_redraw() # Update UI
            result = next(self.BakeCrt)
            if result == -1:
                self.cancel(context)
                return {'CANCELLED'}
            if result == 0:
                self.finish(context)
                return {'FINISHED'}

        return {'RUNNING_MODAL'}
        
    def cancel(self, context):
        context.scene.BakeLabProps.bake_state = 'NONE'
        self.finish(context)
            
    def finish(self, context):
        self.restore_defaults(context)
        if self.BakeCrt.gi_running:
            self.BakeCrt.close()
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)

    def execute(self, context):
        self.BakeCrt = self.Bake(context)
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

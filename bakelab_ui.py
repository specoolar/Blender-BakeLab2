from bpy.types import (
            Panel
        )

class BakeLabUI(Panel):
    bl_label = "BakeLab"
    bl_space_type = 'VIEW_3D'
    bl_idname = "BAKELAB_PT_ui"
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = "BakeLab"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        layout.use_property_decorate = False
        props = scene.BakeLabProps

        if props.bake_state == 'NONE':
            col = layout.column()
            col.scale_y = 1.5
            col.operator("bakelab.bake", text = 'Bake', icon='RENDER_STILL')
            
            row = layout.row(align = True)
            row.operator("bakelab.unwrap", icon='UV')
            row.operator("bakelab.clear_uv", icon='UV')

            layout.separator()
            
            col = layout.column(align=True)
            col.label(text="Bake mode:")
            row = col.row(align = True)
            row.prop(props, "bake_mode", text='')
            row.prop(props, "show_bake_settings", icon = 'PREFERENCES')
            if props.show_bake_settings:
                box = col.box()
                col = box.column()
                col.use_property_split = True
                col.use_property_decorate = False
                col.prop(props, "bake_margin")
                if props.bake_mode == "TO_ACTIVE":
                    col.prop(props, "cage_extrusion")
                if props.bake_mode == "ALL_TO_ONE":
                    col.prop(props, "global_image_name")
                    col.prop(props, "pre_join_mesh")
                    if props.pre_join_mesh:
                        col.prop(props, "cage_extrusion")
            
            layout.separator()
            
            layout.prop(props, "compute_device")
            col = layout.column(align=True)
            col.use_property_split = True
            col.use_property_decorate = False
            row = col.row(align=True)
            row.prop(props, "image_size")
            if props.image_size == 'ADAPTIVE':
                row.prop(props, "adaptive_image_Settings", icon='PREFERENCES')
                if props.adaptive_image_Settings:
                    box = col.box()
                    col = box.column()
                    col.prop(props, "texel_per_unit")
                    row = col.row(align = True)
                    row.use_property_split = False
                    row.prop(props, "image_min_size")
                    row.prop(props, "image_max_size")
                    col.prop(props, "round_adaptive_image")
                
            layout.use_property_split = True
            layout.prop(props, "anti_alias")
            layout.prop(props, "save_or_pack", expand=True)
            layout.use_property_split = False
            if props.save_or_pack == "SAVE":
                layout.prop(props, "save_path")
                layout.prop(props, "create_folder")
                if props.bake_mode == "ALL_TO_ONE":
                    layout.prop(props, "folder_name")
            else:
                layout.label(text = "")
            col = layout.column()
            col.label(text = "Maps:")
            box = col.box()
            col = box.column(align = True)
            row = col.split(align = True)
            row.operator("bakelab.newmapitem", icon='ADD', text="")
            row.operator("bakelab.removemapitem", icon='REMOVE', text="")
            
            col.template_list("BAKELAB_MAP_UL_list", "", scene,
                            "BakeLabMaps", scene, "BakeLabMapIndex", rows=2, maxrows=5)
            
            ##################################################
            if scene.BakeLabMapIndex >= 0 and scene.BakeLabMaps:
                item = scene.BakeLabMaps[scene.BakeLabMapIndex]
                col = col.column()
                col.use_property_split = True
                col.use_property_decorate = False
                col.enabled = item.enabled
                col.separator()
                subcol = col.column(align = True)
                row = subcol.row(align = True)
                row.prop(item, "type")
                row.prop(props, "show_map_settings", icon = 'PREFERENCES')
                
                if props.show_map_settings:
                    box = subcol.box()
                    scol = box.column()
                    scol.prop(item, 'aa_override')
                    if item.type != 'CustomPass':
                        scol.prop(item, 'color_space')
                    if item.type in {
                        'Combined',
                        'Diffuse',
                        'Glossy',
                        'Transmission',
                        'Subsurface',
                        'Normal'
                    }:
                        row = box.row()
                        row.use_property_split = False
                        if item.type == 'Combined':
                            row = box.row(align = True)
                            row.use_property_split = False
                            row.prop(item, "combined_direct", toggle = True)
                            row.prop(item, "combined_indirect", toggle = True)
                            
                            sub_box_col = box.column(align = True)
                            sub_box_col.use_property_split = False
                            row = sub_box_col.row(align = True)
                            row.prop(item, "combined_diffuse", toggle = True)
                            #row.prop(item, "combined_subsurface", toggle = True)
                            
                            row = sub_box_col.row(align = True)
                            row.prop(item, "combined_glossy", toggle = True)
                            #row.prop(item, "combined_ambient_occlusion", toggle = True)
                            
                            row = sub_box_col.row(align = True)
                            row.prop(item, "combined_transmission", toggle = True)
                            row.prop(item, "combined_emit", toggle = True)
                            
                        if item.type in {
                            'Diffuse',
                            'Glossy',
                            'Transmission',
                            'Subsurface'
                        }:
                            row = box.row(align = True)
                            row.use_property_split = False
                            row.prop(item, "bake_direct", toggle = True)
                            row.prop(item, "bake_indirect", toggle = True)
                            row.prop(item, "bake_color", toggle = True)
                            
                        if item.type == 'Normal':
                            box.prop(item, "normal_space")
                            
                        subcol.separator()
                        
                if item.type == 'CustomPass':
                    col.label(text='Property Name')
                    row = col.row(align = True)
                    row.use_property_split = False
                    row.prop(item, "pass_name", text='')
                    row.operator_menu_enum(
                        'bakelab.show_pass_presets',
                        'pass_presets',
                        icon = 'PRESET',
                        text = ''
                    )
                    col.prop(item, 'color_space')
                    col.prop(item, "deep_search")
                
                if item.type == 'Displacement':
                    if not item.float_depth:
                        col.label(text="Use 32 bit float type", icon = 'INFO')
                    if props.save_or_pack == 'SAVE':
                        if item.file_format != 'OPEN_EXR':
                            col.label(text="Use EXR format", icon = 'INFO')
                
                col.separator()
                    
                col.prop(item, "samples")
                
                col.separator()
                col.prop(item, "img_name")
                
                subcol = col.column(align = True)
                if props.image_size == 'FIXED':
                    subcol.prop(item, "width")
                    subcol.prop(item, "height")
                elif props.image_size == 'ADAPTIVE':
                    subcol.prop(item, "image_scale")
                
                col.separator()
                col.prop(item, "float_depth")
                if props.save_or_pack == 'SAVE':
                    row = col.row()
                    row.prop(item, "file_format")
                    row.prop(props, "show_file_settings", icon = 'PREFERENCES')
                    if props.show_file_settings:
                        subcol = col.column()
                        if item.file_format == "PNG":
                            row = subcol.row()
                            row.prop(item, "png_channels", expand = True)
                            row = subcol.row()
                            row.prop(item, "png_depth", expand = True)
                            subcol.prop(item, "png_compression")
                        if item.file_format == "JPEG":
                            row = subcol.row()
                            row.prop(item, "jpg_channels", expand = True)
                            subcol.prop(item, "jpg_quality")
                        if item.file_format == "OPEN_EXR":
                            row = subcol.row()
                            row.prop(item, "exr_channels", expand = True)
                            row = subcol.row()
                            row.prop(item, "exr_depth", expand = True)
                            if item.exr_depth == '32':
                                subcol.prop(item, "exr_codec_32")
                            if item.exr_depth == '16':
                                subcol.prop(item, "exr_codec_16")
        
        else:
            if props.bake_state == 'BAKING':
                layout.label(text = 'Baking', icon = 'RENDER_STILL')
                if props.bake_mode == 'INDIVIDUAL':
                    row = layout.row()
                    row.label(text = 'Objects:')
                    row.label(
                        text = 
                            str(props.baking_obj_index) + ' of ' + 
                            str(props.baking_obj_count)
                    )
                row = layout.row()
                row.label(text = 'Maps:')
                row.label(
                    text = 
                        str(props.baking_map_index) + ' of ' + 
                        str(props.baking_map_count)
                )
                
                layout.separator()
                
                if props.bake_mode == 'INDIVIDUAL':
                    row = layout.row()
                    row.label(text = 'Current Object:')
                    row.label(text = props.baking_obj_name)
                
                row = layout.row()
                row.label(text = 'Current Image:')
                row.label(text = props.baking_map_name)
                row = layout.row()
                row.label(text = '')
                row.label(text = props.baking_map_size)
                
                row = layout.row()
                row.label( text = 'Type:')
                row.label( text = props.baking_map_type)
                layout.template_running_jobs()
            elif props.bake_state == 'BAKED':
                layout.label(text = 'Baked', icon = 'CHECKMARK')
                
                if props.bake_mode == 'INDIVIDUAL':
                    row = layout.row()
                    row.label(text = 'Objects:')
                    row.label(text = str(props.baking_obj_count))
                
                row = layout.row()
                row.label(text = 'Total images: ')
                if props.bake_mode == 'INDIVIDUAL':
                    row.label(text = str(props.baking_map_count*props.baking_obj_count))
                else:
                    row.label(text = str(props.baking_map_count))
                
                layout.separator()
                
                layout.prop(props, "apply_only_selected")
                layout.prop(props, "make_single_user")
                layout.operator("bakelab.generate_mats", icon='MATERIAL')
                layout.operator("bakelab.apply_ao", icon='SHADING_RENDERED')
                layout.operator("bakelab.apply_displace", icon='RNDCURVE')
                layout.separator()
                layout.operator("bakelab.finish")

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

class BakeLabMap(PropertyGroup):
    enabled : BoolProperty(name = '', default = True)
    type : EnumProperty(
            name = 'Type',
            items =  (
                    ('Albedo',      'Albedo',''),
                    ('Normal',      'Normal',''),
                    ('Glossy',      'Glossy',''),
                    ('Roughness',   'Roughness',''),
                    ('Emission',    'Emission',''),
                    ('Diffuse',     'Diffuse',''),
                    ('Subsurface',  'Subsurface',''),
                    ('Transmission','Transmission',''),
                    ('Shadow',      'Shadow',''),
                    ('Environment', 'Environment',''),
                    ('UV',          'UV',''),
                    None,
                    ('Combined',    'Combined',''),
                    ('CustomPass',  'Custom Pass',''),
                    ('AO',          'Ambient Occlusion',''),
                    ('Displacement','Displacement','')
            ),
            default = 'Albedo'
        )
    pass_name   : StringProperty(name = 'Property name', default = 'Color,Base Color,Albedo,Paint Color')
    deep_search : BoolProperty(
        name = 'Deep Search',
        description = 'Search inside of node groups',
        default = True
    )
    
    img_name : StringProperty(name = 'Image name', default = '*')
    width  : IntProperty( 
                name = 'Width', 
                default = 1024 ,
                min = 1, soft_max = 16384
            )
    height : IntProperty(
                name = 'Height',
                default = 1024,
                min = 1, soft_max = 16384
            )
    target_width  : IntProperty(name = 'Target Width')
    target_height : IntProperty(name = 'Target Height')
    image_scale : FloatProperty(
                name = 'Image Scale',
                default = 1,
                min = 0
            )
    aa_override : IntProperty(
                name = 'Anti-alias Override',
                description = 'Use individual anti-aliasing (0 to use global value)',
                default = 0,
                min = 0, soft_max = 8
            )
    final_aa : IntProperty(name = 'Final Anti-alias')

    
    float_depth: BoolProperty(name = '32 bit float', default = False)
    color_space : EnumProperty(
                name = 'Color Space',
                description = 'Color Space',
                items =  (('sRGB','sRGB',''),
                        ('Non-Color','Non-Color','')),
                default = 'sRGB'
            )
    file_format : EnumProperty(
                name = 'Format',
                items =  (
                    ('PNG',  'PNG', ''),
                    ('JPEG', 'JPEG', ''),
                    ('OPEN_EXR',  'OpenEXR', '')
                )
            )
    png_channels : EnumProperty(
                name = 'Color',
                items =  (('BW','BW',''),
                        ('RGB','RGB',''),
                        ('RGBA','RGBA','')),
                default = 'RGB'
            )
    png_depth : EnumProperty(
                name = 'Depth',
                description = 'Color Depth',
                items =  (('8','8 byte',''),
                        ('16','16 byte','')),
                default = '8'
            )
    png_compression : IntProperty(
                name = 'Compression', 
                default = 15,
                description = 'Compression',
                min = 0, max = 100
            )
    jpg_channels : EnumProperty(
                name = 'Color',
                items =  (('BW','BW',''),
                        ('RGB','RGB','')),
                default = 'RGB'
            )
    jpg_quality : IntProperty(
                name = 'Quality',  
                default = 90,
                description = 'Quality',
                min = 0, max = 100
            )
    exr_channels : EnumProperty(
                name = 'Color',
                items =  (('RGB','RGB',''),
                        ('RGBA','RGBA','')),
                default = 'RGB'
            )
    exr_depth : EnumProperty(
                name = 'Color Depth',
                description = 'Bits depth per channel',
                items =  (('16', 'Half (16)',''),
                        ('32',   'Full (32)','')),
                default = '32'
            )
    exr_codec_32 : EnumProperty(
                name = 'Codec',
                items =  (
                    ('NONE', 'None',           ''),
                    ('PXR24','Pxr24 (lossy)',  ''),
                    ('ZIP',  'ZIP (lossless)', ''),
                    ('PIZ',  'PIZ (lossless)', ''),
                    ('RLE',  'RLE (lossless)', ''),
                    ('ZIPS', 'ZIPS (lossless)',''),
                    ('DWAA', 'DWAA (lossy)',   '')
                ),
                default = 'ZIP'
            )
    exr_codec_16 : EnumProperty(
                name = 'Codec',
                items =  (
                    ('NONE', 'None',           ''),
                    ('PXR24','Pxr24 (lossy)',  ''),
                    ('ZIP',  'ZIP (lossless)', ''),
                    ('PIZ',  'PIZ (lossless)', ''),
                    ('RLE',  'RLE (lossless)', ''),
                    ('ZIPS', 'ZIPS (lossless)',''),
                    ('B44',  'B44 (lossy)',   ''),
                    ('B44A', 'B44A (lossy)',   ''),
                    ('DWAA', 'DWAA (lossy)',   '')
                ),
                default = 'ZIP'
            )
    samples : IntProperty(
                name = 'Samples',default = 6,
                description = 'Amount of Samples',
                min = 1, soft_max = 1024
            )
    
    normal_space : EnumProperty(
                name = 'Normal Space',
                items =  (
                    ('TANGENT','Tangent Space',''),
                    ('OBJECT', 'Object Space','')
                )
            )
                    
    bake_direct            : BoolProperty(name = 'Direct',       default = False)
    bake_indirect          : BoolProperty(name = 'Indirect',     default = False)
    bake_color             : BoolProperty(name = 'Color',        default = True)
    
    combined_direct            : BoolProperty(name = 'Direct',       default = True)
    combined_indirect          : BoolProperty(name = 'Indirect',     default = True)
    
    combined_diffuse           : BoolProperty(name = 'Diffuse',      default = True)
    combined_glossy            : BoolProperty(name = 'Glossy',       default = True)
    combined_transmission      : BoolProperty(name = 'Transmission', default = True)
    #combined_subsurface        : BoolProperty(name = 'Subsurface',   default = True)
    #combined_ambient_occlusion : BoolProperty(name = 'AO',           default = True)
    combined_emit              : BoolProperty(name = 'Emit',         default = True)
################################################################
################################################################

class BakeLabAddMapItem(bpy.types.Operator):
    """Add a new bake map"""
    bl_idname = "bakelab.newmapitem"
    bl_label = "Add bake map"
    bl_options = {'REGISTER','UNDO'}
    
    type: EnumProperty(
            name = 'Type',
            items =  (
                    ('Albedo',      'Albedo',''),
                    ('Normal',      'Normal',''),
                    ('Glossy',      'Glossy',''),
                    ('Roughness',   'Roughness',''),
                    ('Emission',    'Emission',''),
                    ('Diffuse',     'Diffuse',''),
                    ('Subsurface',  'Subsurface',''),
                    ('Transmission','Transmission',''),
                    ('Shadow',      'Shadow',''),
                    ('Environment', 'Environment',''),
                    ('UV',          'UV',''),
                    None,
                    ('Combined',    'Combined',''),
                    ('CustomPass',  'Custom Pass',''),
                    ('AO',          'Ambient Occlusion',''),
                    ('Displacement','Displacement','')
            ),
            default = 'Albedo'
        )
    width: IntProperty(name = 'Width',default = 1024,
                                    min = 1, soft_max = 16384)
    height: IntProperty(name = 'Height',default = 1024,
                                    min = 1, soft_max = 16384)
    image_scale: FloatProperty(name = 'Image Scale',default = 1,
                                    min = 0)
    
    float_depth: BoolProperty(name = '32 bit float', default = False)            
    file_format : EnumProperty(
                name = 'Format',
                items =  (
                    ('PNG',  'PNG', ''),
                    ('JPEG', 'JPEG', ''),
                    ('OPEN_EXR',  'OpenEXR', '')
                )
            )
    png_channels : EnumProperty(
                name = 'Color',
                items =  (('BW','BW',''),
                        ('RGB','RGB',''),
                        ('RGBA','RGBA','')),
                default = 'RGB'
            )
    png_depth : EnumProperty(
                name = 'Depth',
                description = 'Color Depth',
                items =  (('8','8 byte',''),
                        ('16','16 byte','')),
                default = '8'
            )
    png_compression : IntProperty(
                name = 'Compression', 
                default = 15,
                description = 'Compression',
                min = 0, max = 100
            )
    jpg_channels : EnumProperty(
                name = 'Color',
                items =  (('BW','BW',''),
                        ('RGB','RGB','')),
                default = 'RGB'
            )
    jpg_quality : IntProperty(
                name = 'Quality',  
                default = 90,
                description = 'Quality',
                min = 0, max = 100
            )
    exr_channels : EnumProperty(
                name = 'Color',
                items =  (('RGB','RGB',''),
                        ('RGBA','RGBA','')),
                default = 'RGB'
            )
    exr_depth : EnumProperty(
                name = 'Color Depth',
                description = 'Bits depth per channel',
                items =  (('16', 'Half (16)',''),
                        ('32',   'Full (32)','')),
                default = '32'
            )
    exr_codec_32 : EnumProperty(
                name = 'Codec',
                items =  (
                    ('NONE', 'None',           ''),
                    ('PXR24','Pxr24 (lossy)',  ''),
                    ('ZIP',  'ZIP (lossless)', ''),
                    ('PIZ',  'PIZ (lossless)', ''),
                    ('RLE',  'RLE (lossless)', ''),
                    ('ZIPS', 'ZIPS (lossless)',''),
                    ('DWAA', 'DWAA (lossy)',   '')
                ),
                default = 'ZIP'
            )
    exr_codec_16 : EnumProperty(
                name = 'Codec',
                items =  (
                    ('NONE', 'None',           ''),
                    ('PXR24','Pxr24 (lossy)',  ''),
                    ('ZIP',  'ZIP (lossless)', ''),
                    ('PIZ',  'PIZ (lossless)', ''),
                    ('RLE',  'RLE (lossless)', ''),
                    ('ZIPS', 'ZIPS (lossless)',''),
                    ('B44',  'B44 (lossy)',   ''),
                    ('B44A', 'B44A (lossy)',   ''),
                    ('DWAA', 'DWAA (lossy)',   '')
                ),
                default = 'ZIP'
            )
                    
    def calcItemSettings(self,context,item):
        if self.type == 'Albedo':
            item.img_name = '*_t'
            item.samples  = 4
        if self.type == 'Combined':
            item.img_name = '*_c'
            item.samples  = 64
        if self.type == 'Normal':
            item.img_name = '*_n'
            item.samples  = 16
            item.color_space = 'Non-Color'
            item.aa_override = 1 #Because cycles has buildin anti-aliasing for normals
        if self.type == 'Displacement':
            item.img_name = '*_h'
            item.samples  = 4
            item.color_space = 'Non-Color'
        if self.type == 'AO':
            item.img_name = '*_ao'
            item.samples  = 64
            item.color_space = 'Non-Color'
        if self.type == 'Shadow':
            item.img_name = '*_sh'
            item.samples  = 32
        if self.type == 'Glossy':
            item.img_name = '*_s'
            item.samples  = 8
        if self.type == 'Roughness':
            item.img_name = '*_r'
            item.samples  = 4
            item.color_space = 'Non-Color'
        if self.type == 'Diffuse':
            item.img_name = '*_d'
            item.samples  = 8
        if self.type == 'Emission':
            item.img_name = '*_e'
            item.samples  = 4
        if self.type == 'Transmission':
            item.img_name = '*_a'
            item.samples  = 8
        if self.type == 'UV':
            item.img_name = '*_uv'
            item.samples  = 1
        if self.type == 'Environment':
            item.img_name = '*_env'
            item.samples  = 16
        if self.type == 'Subsurface':
            item.img_name = '*_sss'
            item.samples  = 64
        if self.type == 'CustomPass':
            item.img_name = '*_pass'
            item.samples  = 4
            item.color_space = 'Non-Color'
    
    def draw(self,context):
        layout = self.layout
        props = context.scene.BakeLabProps
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        layout.prop(self, "type")
        if props.image_size == 'FIXED':
            col = layout.column(align = True)
            col.prop(self, "width")
            col.prop(self, "height")
        elif props.image_size == 'ADAPTIVE':
            layout.prop(self, "image_scale")
            
        layout.prop(self, "float_depth")
        if props.save_or_pack == 'SAVE':
            row = layout.row()
            row.prop(self, "file_format")
            
            col = layout.column()
            if self.file_format == "PNG":
                row = col.row()
                row.prop(self, "png_channels", expand = True)
                row = col.row()
                row.prop(self, "png_depth", expand = True)
                col.prop(self, "png_compression")
            if self.file_format == "JPEG":
                row = col.row()
                row.prop(self, "jpg_channels", expand = True)
                col.prop(self, "jpg_quality")
            if self.file_format == "OPEN_EXR":
                row = col.row()
                row.prop(self, "exr_channels", expand = True)
                row = col.row()
                row.prop(self, "exr_depth", expand = True)
                if self.exr_depth == '32':
                    col.prop(self, "exr_codec_32")
                if self.exr_depth == '16':
                    col.prop(self, "exr_codec_16")
        
    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def execute(self,context):
        context.area.tag_redraw()
        item = context.scene.BakeLabMaps.add()
        
        item.type        = self.type
        item.width       = self.width
        item.height      = self.height
        item.image_scale = self.image_scale
        
        item.float_depth      = self.float_depth
        item.file_format      = self.file_format
        item.png_channels     = self.png_channels
        item.png_depth        = self.png_depth
        item.png_compression  = self.png_compression
        item.jpg_channels     = self.jpg_channels
        item.jpg_quality      = self.jpg_quality
        item.exr_channels     = self.exr_channels
        item.exr_depth        = self.exr_depth
        item.exr_codec_32     = self.exr_codec_32
        item.exr_codec_16     = self.exr_codec_16
        
        self.calcItemSettings(context, item)
        context.scene.BakeLabMapIndex = len(context.scene.BakeLabMaps)-1
        return {'FINISHED'}
        
class BakeLabRemoveMapItem(bpy.types.Operator):
    """Remove selected bake map"""
    bl_idname = "bakelab.removemapitem"
    bl_label = "remove bake map"
    bl_options = {'REGISTER','UNDO'}
    
    @classmethod
    def poll(cls,context):
        return context.scene.BakeLabMaps
    
    def execute(self,context):
        context.area.tag_redraw()
        context.scene.BakeLabMaps.remove(context.scene.BakeLabMapIndex)
        context.scene.BakeLabMapIndex = max(context.scene.BakeLabMapIndex - 1,0)
        context.scene.BakeLabMapIndex = min(context.scene.BakeLabMapIndex, len(context.scene.BakeLabMaps))
        return {'FINISHED'}
    
class BakeLabShowPassPresets(Operator):
    """Show Presets"""
    bl_idname = "bakelab.show_pass_presets"
    bl_label = "BakeLab Show Pass Presets"
    pass_presets : EnumProperty(
            name   = 'Pass Presets',
            items  =  (
                ('Color,Base Color,Albedo,Paint Color',  'Color/Albedo',''),
                ('Metallic',                             'Metallic',''),
                ('Specular,Glossiness,Glossy',           'Specular',''),
                ('Roughness',                            'Roughness',''),
                ('Anisotropic',                          'Anisotropic',''),
                ('Sheen',                                'Sheen',''),
                ('Clearcoat',                            'Clearcoat',''),
                ('Transmission',                         'Transmission ',''),
                ('Alpha',                                'Alpha ','')
            )
        )
    
    def execute(self,context):
        context.area.tag_redraw()
        scene = context.scene
        if scene.BakeLabMapIndex>=0 and scene.BakeLabMaps:
            item = scene.BakeLabMaps[scene.BakeLabMapIndex]
            if item:
                item.pass_name = self.pass_presets
        return {'FINISHED'}

################################################################

class BakeLabMapListUI(bpy.types.UIList):
    bl_idname = "BAKELAB_MAP_UL_list"
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if item.type == 'CustomPass':
                layout.label(text = item.pass_name, icon = 'NONE')
            else:
                layout.label(text = item.type, icon = 'NONE')
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text = "", icon = 'TEXTURE')
        layout.prop(item, 'enabled')

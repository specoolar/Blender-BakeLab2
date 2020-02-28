import bpy

def SelectObject(obj):
    bpy.ops.object.select_all(action = 'DESELECT')
    if obj:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
def SelectObjects(active_obj, selected_objs):
    SelectObject(active_obj)
    for obj in selected_objs:
        if obj:
            obj.select_set(True)
            
def IsValidMesh(self, obj):
    if obj.type != 'MESH':
        self.report(type = {'WARNING'}, message = 'Object ' + obj.name + ' is not mesh type')
        return False
    if len(obj.data.polygons) == 0:
        self.report(type = {'WARNING'}, message = 'Object ' + obj.name + ' has no faces')
        return False
    return True
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

try:
    init_data
    reload(BezierCurve)
    reload(BezierSegmentIterator)
except:
    from blender_curve_to_mesh import BezierCurve
    from blender_curve_to_mesh import BezierSegmentIterator

init_data = True

bl_addon_info = {
    "name": "Curve to Uniform Mesh",
    "author": "Denis Declara",
    "version": (0, 2),
    "blender": (2, 5, 3),   # I am not so sure about the compatibility :(
    "api": 32411,
    "location": "Toolshelf > search > Curve to Uniform Mesh",
    "description": "This script converts bezier curves or text objects to a mesh",
    "warning": "Beta",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Curve"}

"""
This script converts curves and text objects to an even mesh.
"""

##############################
import bpy
from bpy.props import *
import mathutils
from mathutils import Vector

def main(context, obj, options):
    #options = [
    #    self.fillMesh,      #0
    #    self.lengthApp,     #1
    #    self.density,       #2
    #    self.offset,        #3
    #    self.beautifyIters, #4
    #    self.execscript]    #5

    # main vars
    fillMesh = options[0]
    lengthApp = options[1]
    density = options[2]
    offset = options[3]
    beautifyIters = options[4]
    if(options[5] == False): # If the execute checkbox is not checked leave the method
        return;

    verts = []
    faces = []
    curVertex = 0;

    originalName = obj.name
    #try:
    #    if ("uniform_" + originalName) in bpy.data.objects.keys():
    #        context.scene.unlink(bpy.data.objects["uniform_" + originalName])
    #        bpy.data.objects.remove(bpy.data.objects["uniform_" + originalName])
    #    if ("uniform_"+originalName) in bpy.data.meshes.keys():
    #        bpy.data.meshes.remove(bpy.data.meshes["uniform_" + originalName])
    #finally:
    #    print("Couldn't delete old object")

    #isFontObject = (obj.type == 'FONT')
    #if isFontObject:
    #    # Convert font objects into curves
    #    bpy.ops.object.select_all(action='DESELECT')
    #    obj.select = True
    #    context.scene.objects.active = obj
    #    bpy.ops.object.convert(target='CURVE', keep_original=True)
    #    obj = bpy.context.active_object

    # Deselect all of the objects in the scene
    bpy.ops.object.select_all(action='DESELECT')
    scene = context.scene
    splines = obj.data.splines.values()

    # create a mesh datablock
    mesh = bpy.data.meshes.new("uniform_"+originalName)

    # go through splines
    for spline in splines:
        # test if spline is a bezier curve, otherwise skip it
        # also test if the curve has one or no points skip it
        if spline.type == 'BEZIER' and len(spline.bezier_points) > 1:
            # Convert blender's bpy bezier class in to my own bezier class
            bezier = BezierCurve.BezierCurve()
            bezier.controlPoints = [] # Shouldn't this reset automaticly by calling the constructor???
            for bp in spline.bezier_points:
                bezier.appendSegment(bp.handle_left, bp.co, bp.handle_right)
            bezier.controlPoints.append(bezier.controlPoints[0])
            bezier.controlPoints.pop(0)

            # Sample the curve uniformly and store the points in ip
            ip = None
            if offset == 0.0:
                ip = bezier.toPointCloud(lengthApp, density)
            else:
                ip = bezier.toOfsettedPointCloud(offset, lengthApp, density)

            # Prepare the data to be added to blender
            firstVertexId =  curVertex
            for point in ip:
                verts.append([point.x, point.y, point.z])
                faces.append([curVertex, curVertex + 1, curVertex])
                curVertex+=1
            # Fix the mesh, closing the last edge
            faces[curVertex -1][1] = firstVertexId

    # Add geometry to mesh object
    print("mesh.from_pydata(#" + str(len(verts)) + ", #0, #" + str(len(faces)) + ")");
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    # Create object and link it to the scene
    newMesh = bpy.data.objects.new("uniform_"+originalName, mesh)
    scene.objects.link(newMesh)
    newMesh.select = True
    scene.objects.active = newMesh
    newMesh.matrix_world = obj.matrix_world
    newMesh.data.show_all_edges = True

    # Remove double vertices
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.mesh.remove_doubles()

    # If the user decides to fill the mesh, fill it with the
    # internal operators
    if fillMesh == True:
        bpy.ops.mesh.fill()
        # Repeat the beautify fill a couple of times as it may not
        # yield a perfect result the first time
        for i in range(0, beautifyIters):
            bpy.ops.mesh.beautify_fill()
        # Quadrangulate the mesh using blender ops
        bpy.ops.mesh.tris_convert_to_quads()

    # Switch back to object mode
    bpy.ops.object.mode_set(mode = 'OBJECT')

    # create ne object and put into scene

    #if isFontObject == True:
    #    scene.objects.unlink(obj)

    #print("________END________\n")
    return

###########################
##### Curves OPERATOR #####
###########################
class CURVE_OT_toUniformMesh(bpy.types.Operator):
    ''''''
    bl_idname = "curve.toUniformMesh"
    bl_label = "Convert Curve To Uniform Mesh"
    bl_description = "converts curve to an uniform mesh"
    bl_options = {'REGISTER', 'UNDO'}

    # Whetever or not to execute the modifier
    execscript = BoolProperty(name="Execute",
                            description="execute the modifier",
                            default=True)

    # Whetever or not to fill the mesh
    fillMesh = BoolProperty(name="Fill mesh",
                            description="fill the mesh",
                            default=False)

    # Precision (number of segments) of the length approximation
    lengthApp = IntProperty(name="Length approximation",
                            min=1, soft_min=1,
                            default=8,
                            description="precision of the length approximation")

    # Number of times to execute blender's beautify_fill
    beautifyIters = IntProperty(name="Beautify fill iterations",
                            min=1, soft_min=1,
                            default=5,
                            description="number of time to execute beautify fill on the mesh")

    # Amount of vertices per blender unit to compute
    density = FloatProperty(name="Density",
                            description="amount of vertices per 1 blender unit to compute",
                            min=1, soft_min=1,
                            default=32.0, precision=3)

    # Amount of vertices per blender unit to compute
    offset = FloatProperty(name="Curve offset",
                            description="Curve offset in blender units",
                            min=-100,
                            default=0.0, precision=3, max=100)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, 'execscript')
        col.prop(self, 'fillMesh')
        col.prop(self, 'density')
        col.prop(self, 'beautifyIters')
        col.prop(self, 'offset')
        col.prop(self, 'lengthApp')

    ## Check for curve or text object
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        #if (obj and (obj.type == 'CURVE' or obj.type == 'FONT')):
        #    return True
        if obj and obj.type == 'MESH' and obj.name.startswith("uniform_"):
            if obj.name[8:] in bpy.context.scene.objects:
                if bpy.context.scene.objects[obj.name[8:]].type == 'CURVE' or bpy.context.scene.objects[obj.name[8:]].type == 'FONT':
                    return True
        #return False
        return bpy.context.active_object.type == 'CURVE';

    ## execute
    def execute(self, context):
        #print("------START------")

        options = [
                self.fillMesh,      #0
                self.lengthApp,     #1
                self.density,       #2
                self.offset,        #3
                self.beautifyIters, #4
                self.execscript]    #5

        bpy.context.user_preferences.edit.use_global_undo = False

        # Go into object mode
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        # Grab the current object
        obj = context.active_object
        if obj.type == 'MESH':
            tempobj = obj
            print("---" + str(obj.name))
            obj = bpy.context.scene.objects[obj.name[8:]]
            print(">>>" + str(obj.name))
            bpy.context.scene.objects.active = obj;
            bpy.context.scene.objects.unlink(tempobj)

        main(context, obj, options)

        bpy.context.user_preferences.edit.use_global_undo = True

        #print("-------END-------")
        return {'FINISHED'}

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

#################################################
#### REGISTER ###################################
#################################################
# We don't need any registration!
def register():
    pass

# We do not need any registration either!
def unregister():
    pass

if __name__ == "__main__":
    register()
bl_info = {
    "name": "SR2 chunk_pc",
    "description": "Imports MDN files from Metal Gear Solid 4.",
    "author": "MyRightArmTheGodHand",
    "version": (0, 0, 1),
    "blender": (2, 80, 0), # I have no clue on compatibility. I'm running this on 2.90.10
    "category": "Import-Export"
    }
import bpy
import struct
import os.path
from bpy.props import CollectionProperty

def read_byte(file_object, endian = '>'):
    data = struct.unpack(endian+'B', file_object.read(1))[0]
    return data
def read_short(file_object, endian = '>'):
    data = struct.unpack(endian+'H', file_object.read(2))[0]
    return data
def read_uint(file_object, endian = '>'):
    data = struct.unpack(endian+'I', file_object.read(4))[0]
    return data
def read_int(file_object, endian = '>'):
    data = struct.unpack(endian+'i', file_object.read(4))[0]
    return data
def read_float(file_object, endian = '>'):
    data = struct.unpack(endian+'f', file_object.read(4))[0]
    return data
def read_float32(file_object, endian = '>'):
    data = struct.unpack(endian+'f', file_object.read(4))[0]
    return data
def read_half(file_object):
    float16 = read_short(file_object)
    s = int((float16 >> 15) & 0x00000001)    # sign
    e = int((float16 >> 10) & 0x0000001f)    # exponent
    f = int(float16 & 0x000003ff)            # fraction
    if e == 0:
        if f == 0:
            return int(s << 31)
        else:
            while not (f & 0x00000400):
                f = f << 1
                e -= 1
            e += 1
            f &= ~0x00000400
    elif e == 31:
        if f == 0:
            return int((s << 31) | 0x7f800000)
        else:
            return int((s << 31) | 0x7f800000 | (f << 13))
    e = e + (127 -15)
    f = f << 13
    temp = int((s << 31) | (e << 23) | f)
    str = struct.pack('I',temp)
    return struct.unpack('f',str)[0]
def read_cstr(f):
    return ''.join(iter(lambda: f.read(1).decode('ascii'), '\x00'))
def modify_bit( n,  p,  b):
    mask = 1 << p
    return (n & ~mask) | ((b << p) & mask)
def SeekToNextRow(f):
    # At multiple points the file continues at the next address where the least significant number is 0 (like 0xXXX0).
    # This fn seeks there.

    offset = f.tell()
    # check if we're already at the beginning of the next row
    if offset & 0xfffffff0 == offset:
        pass
    else:
        # Add 16 to get to next row
        offset += 16
        # Zero 4 least significant bits to get to beginning of this row
        offset = offset & 0xfffffff0
        f.seek(offset)

    
class SR2_Prop:
    Pos = []                # Prop spawn world position, doesn't affect culling.
    Unknown0: bytearray     # Unknown 72 bytes
    Unknown1: int           # this is always FFFFFFFF?
    Model_Destroyed: int    # Sets the model loaded when prop is destroyed
    Unknown2: int

class SR2_chunk_pc_mesh:
    vertCount: int
    indexCount: int
    vertices = []
    faces = []
    unknown0: int
    unknown1: int

def chunk_pc_mesh_vertices(f, count):
    vertices = []
    for _ in range(count):
        X = read_float(f, '<')
        Z = read_float(f, '<')
        Y = read_float(f, '<')
        vertices.append([X, Y, Z])
    return(vertices)

def chunk_pc_mesh_faces(f, count):
    faces = []
    for i in range (count-2):
        face = [read_short(f, '<'),read_short(f, '<'),read_short(f, '<')]
        if(i < count-3):
            f.seek(-4,os.SEEK_CUR)
        faces.append(face)
    return(faces)

def import_meshes(Meshes, main_collection):
    new_collection = bpy.data.collections.new('Mesh0')
    #bpy.context.scene.collection.children.link(new_collection)
    main_collection.children.link(new_collection)
    for sr2_mesh in Meshes:
        new_mesh = bpy.data.meshes.new('mesh')
        new_mesh.from_pydata(sr2_mesh.vertices, [], sr2_mesh.faces)
        new_mesh.update()
        new_object = bpy.data.objects.new('object', new_mesh)
        new_collection.objects.link(new_object)

def chunk_pc_mesh2_faces(f, count):
    faces = []
    for _ in range (count):
        face = [read_short(f, '<'),read_short(f, '<'),read_short(f, '<')]
        faces.append(face)
    return(faces)

def read_some_data(context, filepath, ImportProps, ImportMesh):
    print()
    print("Opening file: ", filepath)
    f = open(filepath, 'rb')
    
    
# --- Create Collection --- #
    if ImportMesh:
        main_collection = bpy.data.collections.new(os.path.basename(filepath))
        bpy.context.scene.collection.children.link(main_collection)

# --- Header --- #
    print("Header:              ", hex(f.tell()))
    chunk_pc_Header0            = f.read(12) # This is same in every file?
    chunk_pc_HeaderB            = read_uint(f, '<')  # int: zero every file except for sr2_meshlibrary.chunk_pc, which says 2
    chunk_pc_HeaderC            = read_uint(f, '<')  # an int? this seems to be 30 or lower in every file
    chunk_pc_Header1            = f.read(24) # Unknown
    chunk_pc_Header2            = f.read(8)  # null
    chunk_pc_Header3            = f.read(40) # Unknown
    chunk_pc_Header4            = f.read(4)  # null
    chunk_pc_Header5            = f.read(20) # Unknown
    chunk_pc_Header6            = f.read(4)  # null
    chunk_pc_Header5            = f.read(136)# Unknown


# --- Texture List --- #
    print("Texture list:        ", hex(f.tell()))
    chunk_pc_TexCount           = read_uint(f, '<')
    
    # null byte filler, length is TexCount*4
    f.seek(chunk_pc_TexCount*4,os.SEEK_CUR)

    # Null terminated strings
    chunk_pc_TexList = []
    for _ in range (chunk_pc_TexCount):
        chunk_pc_TexList.append(read_cstr(f))
    
    SeekToNextRow(f)
    
    
# --- Header 1 --- #
    print("Header 1:            ", hex(f.tell()))
    chunk_pc_UnknownCount0      = read_uint(f, '<')
    chunk_pc_PropCount          = read_uint(f, '<')
    chunk_pc_Model0Count      = read_uint(f, '<')
    chunk_pc_UnknownCount3      = read_uint(f, '<')
    chunk_pc_UnknownCount4      = read_uint(f, '<')

    SeekToNextRow(f)
    
    
# --- Unknown0 --- #
    print("Unknown0:            ", hex(f.tell()))
    Unknown0 = []
    for _ in range (chunk_pc_UnknownCount0):
        _temp = f.read(24)
    SeekToNextRow(f)
    

# --- Prop Data 0 --- #
    print("Props0:              ", hex(f.tell()))
    Props = []
    for _ in range (chunk_pc_PropCount):
        prop = SR2_Prop()
        X = read_float(f, '<')
        Z = read_float(f, '<')
        Y = read_float(f, '<')
        prop.Pos = [X, Y, Z]
        prop.Unknown0 = f.read(72)
        prop.Unknown1 = read_uint(f, '<')
        prop.Model_Destroyed = read_uint(f, '<')
        prop.Unknown2 = read_uint(f, '<')
        Props.append(prop)


# --- Unknown3 --- #
    print("Unknown3:            ", hex(f.tell()))
    for _ in range(chunk_pc_UnknownCount3):
        f.read(100)
    SeekToNextRow(f)


# --- Unknown4 ---#
    print("Unknown4:            ", hex(f.tell()))
    for _ in range(chunk_pc_UnknownCount4):
        f.read(52)
    SeekToNextRow(f)

# --- Unknown5 World Pos --- #
    print("Unknown5:            ", hex(f.tell()))
    chunk_pc_UnknownCount5 = read_uint(f, '<')
    Unknown5List =[]
    for _ in range(chunk_pc_UnknownCount5):
        X = read_float(f, '<')
        Z = read_float(f, '<')
        Y = read_float(f, '<')
        Unknown5List.append([X, Y, Z])


# --- Unknown 6 --- #
    print("Unknown6:            ", hex(f.tell()))
    chunk_pc_UnknownCount6 = read_uint(f, '<')
    f.read(chunk_pc_UnknownCount6 * 3)  # What is this garbage??


# --- Unknown 7 --- #
    print("Unknown7:            ", hex(f.tell()))
    chunk_pc_UnknownCount7 = read_uint(f, '<')
    for _ in range (chunk_pc_UnknownCount7):
        read_uint(f, '<')


# --- Unknown 8 --- #
    print("Unknown8:            ", hex(f.tell()))
    chunk_pc_UnknownCount8 = read_uint(f, '<')
    for _ in range(chunk_pc_UnknownCount8):
        f.read(12)
    SeekToNextRow(f)


# --- Unknown 9 MOPP --- #
    print("Unknown9 MOPP:       ", hex(f.tell()))
    chunk_pc_Unknown9Length = read_uint(f, '<')
    SeekToNextRow(f)
    f.read(chunk_pc_Unknown9Length)
    
    if f.tell() & 0xfffffffc != f.tell():
        f.read(4)
        f.seek(f.tell() & 0xfffffffc)
    #SeekToNextRow(f)


# --- Unknown 10 2x World Pos --- #
    print("Unknown10:           ", hex(f.tell()))
    X = read_float(f, '<')
    Z = read_float(f, '<')
    Y = read_float(f, '<')
    X1 = read_float(f, '<')
    Z1 = read_float(f, '<')
    Y1 = read_float(f, '<')
    #print (X, Y, Z)
    #print (X1, Y1, Z1)
    SeekToNextRow(f)

# --- Models 0 --- #
    print("Models 0:            ", hex(f.tell()))
    class chunk_pc_model0_mesh:
        vertCount: int
        indexCount: int
        vertices = []
        faces = []
        unknown0: int
        unknown1: int

        header1count: int
        unknown2 = []

    # --- Header --- #
    model0_list = []
    print("Models 0 header0:    ", hex(f.tell()))
    for _ in range(chunk_pc_Model0Count):
        mesh = chunk_pc_model0_mesh()
        mesh.unknown0 = read_short(f, '<')      # Can only be either 7 or 0?? If 0, skip the mesh
        mesh.header1count = read_short(f, '<')
        mesh.indexCount = read_uint(f, '<')
        f.read(8)   # FF bytes
        f.read(4)   # null bytes
        model0_list.append(mesh)
    print("Models 0 header1:    ", hex(f.tell()))
    for mesh in model0_list:
        for _ in range(mesh.header1count):
            mesh.unknown1 = read_uint(f, '<')
            mesh.vertCount = read_uint(f, '<')
            f.read(4)   # FF bytes
            f.read(4)   # null bytes
    #f.read(16)  # null bytes
    SeekToNextRow(f)

    # --- Mesh Data --- #
    print("Models 0 mesh data:  ", hex(f.tell()))
    for mesh in model0_list:
        if mesh.unknown0 == 7:
            mesh.vertices = chunk_pc_mesh_vertices(f, mesh.vertCount)
            SeekToNextRow(f)
            mesh.faces = chunk_pc_mesh_faces(f, mesh.indexCount)
            SeekToNextRow(f)
    
    # --- Import --- #
    if(ImportMesh): import_meshes(model0_list, main_collection)


    return {'FINISHED'}

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator


class ImportSomeData(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "import_test.some_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Some Data"

    # ImportHelper mixin class uses this
    filename_ext = ".chunk_pc"

    filter_glob: StringProperty(
        default="*.chunk_pc",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    ImportProps: BoolProperty(
        #name="Prop Visualization",
        name="Unused",
        description="Create a mesh with vertices at prop positions",
        default=False,
    )

    ImportMesh: BoolProperty(
        name="Import Meshes",
        description="Only works with sr2_chunk028_terminal!!!",
        default=True,
    )

    type: EnumProperty(
        name="Example Enum",
        description="Choose between two items",
        items=(
            ('FILE', "Import File", "Description one"),
            ('DIR', "Import Dir", "Import whole folder"),
        ),
        default='FILE',
    )

    def execute(self, context):
        if self.type == 'FILE':
            return read_some_data(context, self.filepath, self.ImportProps, self.ImportMesh)
        else:
            dirname = os.path.dirname(self.filepath)
            files = sorted(os.listdir(dirname))
            chunks = [item for item in files if item.endswith('.chunk_pc')]
            for chunk in chunks:
                read_some_data(context, dirname + '\\' + chunk, self.ImportProps, self.ImportMesh)
        return {'FINISHED'} 



# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportSomeData.bl_idname, text="Text Import Operator")


def register():
    bpy.utils.register_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)


def unregister():
    bpy.utils.unregister_class(ImportSomeData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_test.some_data('INVOKE_DEFAULT')
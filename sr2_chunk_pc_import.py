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
    if offset & 4294967280 == offset:
        pass
    else:
        # Add 16 to get to next row
        offset += 16
        # Zero 4 least significant bits to get to beginning of this row
        offset = offset & 4294967280
        f.seek(offset)

    
class SR2_Prop:
    Pos = []                # Prop spawn world position, doesn't affect culling.
    Unknown0: bytearray     # Unknown 72 bytes
    Unknown1: int           # this is always FFFFFFFF?
    Model_Destroyed: int    # Sets the model loaded when prop is destroyed
    Unknown2: int


def read_some_data(context, filepath, propvis):
    #filepath = "J:\Games\_Modding\SR2\\file\_wjork\sr2_chunk028_terminal.chunk_pc"
    #print()
    #print("Opening file: ", filepath)
    #print()
    f = open(filepath, 'rb')
    
    
    # --- Header --- #
    f.seek(0)
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
    #print("--- Header data ---")


    # --- Texture List --- #
    chunk_pc_TexCount           = read_uint(f, '<')
    
    # null byte filler, length is TexCount*4
    f.seek(chunk_pc_TexCount*4,os.SEEK_CUR)
    
    # Null terminated strings
    chunk_pc_TexList = []
    for i in range (chunk_pc_TexCount):
        chunk_pc_TexList.append(read_cstr(f))
    
    #print("Textures Count:         ", chunk_pc_TexCount)
    #print("Tex List Length Verify: ", len(chunk_pc_TexList))
    #print()
    
    SeekToNextRow(f)
    
    
    # --- Numbers --- #
    
    chunk_pc_UnknownCount0      = read_uint(f, '<')
    chunk_pc_PropCount          = read_uint(f, '<')
    chunk_pc_UnknownCount1      = read_uint(f, '<')
    chunk_pc_UnknownCount2      = read_uint(f, '<')
    
    #print("Unknown Count0:         ", chunk_pc_UnknownCount0)
    #print("PropCount:              ", chunk_pc_PropCount)
    #print("Unknown Count1:         ", chunk_pc_UnknownCount1)
    #print("Unknown Count2:         ", chunk_pc_UnknownCount2)
    #print()
    
    # filler
    f.seek(16,os.SEEK_CUR)
    
    
    # --- Unknown Pattern 0 --- #
    Unknown0 = []
    for i in range (chunk_pc_UnknownCount0):
        _temp = f.read(24)
    SeekToNextRow(f)
    

    # --- Prop Data 0 --- #
    Props = []
    for i in range (chunk_pc_PropCount):
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
    

    # --- Prop Data 1 (maybe) --- #
    class SR2_Prop1:
        Pos = []

    do_prop1 = False # Only works for sr2_chunk028_terminal.chunk_pc, see below

    if (do_prop1):
        chunk_pc_Prop1Count = 1944          # <-- Figure out these if you wanna open another file
        chunk_pc_Prop1Offset = 0x001099b0   # <--
        
        f.seek(chunk_pc_Prop1Offset)
        SR2_Prop1_List = []
        for i in range(chunk_pc_Prop1Count):
            prop1 = SR2_Prop1()
            
            X = read_float(f, '<')
            Z = read_float(f, '<')
            Y = read_float(f, '<')
            prop1.Pos = [X, Y, Z]
            f.seek(68,os.SEEK_CUR)
            SR2_Prop1_List.append(prop1)
        propnames = []
        for i in range(chunk_pc_Prop1Count):
            propname = read_cstr(f)
            propnames.append(propname)
            print(propname)
        print(len(propnames))


    # --- Prop Visualization --- #
    # Create a mesh with vertices in place of any prop.
    if(propvis):
        vertices = []
        edges = []
        faces = []  
        for i in range (chunk_pc_PropCount):
            vertices.append([ Props[i].Pos[0], Props[i].Pos[1], Props[i].Pos[2] ]) 

        new_mesh = bpy.data.meshes.new('prop visualization')
        new_mesh.from_pydata(vertices, edges, faces)
        new_mesh.update()
        # make object from mesh
        new_object = bpy.data.objects.new('Prop Visualization', new_mesh)
        # make collection
        new_collection = bpy.data.collections.new(os.path.basename(filepath))
        bpy.context.scene.collection.children.link(new_collection)
        # add object to scene collection
        new_collection.objects.link(new_object)
    
    
    # --- Prop 1 Visualization --- #
    if(do_prop1):

        # make collection
        new_collection = bpy.data.collections.new(os.path.basename(filepath) + "_1")
        bpy.context.scene.collection.children.link(new_collection)

        for i in range (chunk_pc_Prop1Count):
            vert = [[ SR2_Prop1_List[i].Pos[0], SR2_Prop1_List[i].Pos[1], SR2_Prop1_List[i].Pos[2] ]] 

            new_mesh = bpy.data.meshes.new('mesh')
            new_mesh.from_pydata(vert, [], [])
            new_mesh.update()
            # make object from mesh
            new_object = bpy.data.objects.new(propnames[i], new_mesh)

            # add object to scene collection
            new_collection.objects.link(new_object)
    

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
    propvis: BoolProperty(
        name="Prop Visualization",
        description="Create a mesh with vertices at prop positions",
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
            return read_some_data(context, self.filepath, self.propvis)
        else:
            dirname = os.path.dirname(self.filepath)
            files = sorted(os.listdir(dirname))
            chunks = [item for item in files if item.endswith('.chunk_pc')]
            for chunk in chunks:
                read_some_data(context, dirname + '\\' + chunk, self.propvis)
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
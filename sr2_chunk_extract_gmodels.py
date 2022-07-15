
import sys
import os.path
import time

import utils.g_chunker
import utils.modelhandler

from utils.binny import *
from utils.sr2_chunk_classes import *

    
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

class SR2_cityobj:
    name: str
    posx: float
    posy: float
    posz: float
    pos1x: float
    pos1y: float
    pos1z: float

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
        face = [read_ushort(f, '<'),read_ushort(f, '<'),read_ushort(f, '<')]
        if(i < count-3):
            f.seek(-4,os.SEEK_CUR)
        faces.append(face)
    return(faces)

def chunk_pc_mesh2_faces(f, count):
    faces = []
    for _ in range (count):
        face = [read_ushort(f, '<'),read_ushort(f, '<'),read_ushort(f, '<')]
        faces.append(face)
    return(faces)


def main(filepath, ImportMesh):
    timer = time.time()
    print()
    print("Opening file: ", filepath)
    f = open(filepath, 'rb')
    g_chunk_filepath = os.path.splitext(filepath)[0]+".g_chunk_pc"

    export_dir = os.path.splitext(filepath)[0]

# --- Header --- #

    # Header 256B
    CHUNK_MAGIC                 = read_uint(f, '<')
    CHUNK_VERSION               = read_uint(f, '<')     # sr2 pc chunks are ver. 121
    header_2                    = read_uint(f, '<')     # This is same in every file?
    header_3                    = read_uint(f, '<')     # Always zero except for sr2_meshlibrary.chunk_pc, which says 2
    
    header_4                    = read_uint(f, '<')     # Unknown count

    f.seek(0x94)
    header_cullboxcount         = read_uint(f, '<')
    header_19                   = read_uint(f, '<')
    f.read(4)
    header_20                   = read_uint(f, '<')
    f.read(16)
    header_doorcount            = read_uint(f, '<') # Probably doors and some other stuff
    f.read(8)
    header_door2                = read_uint(f, '<') # 
    header_door3                = read_uint(f, '<') # 
    header_door4                = read_uint(f, '<') # 
    f.seek(0xD4)
    header_21                   = read_uint(f, '<') # --- World Pos X? --- #
    header_22                   = read_uint(f, '<') # --- World Pos Y? --- #
    header_23                   = read_uint(f, '<') # --- World Pos Z? --- #
    header_24                   = read_uint(f, '<') # --- World Pos X? --- #
    header_25                   = read_uint(f, '<') # --- World Pos Y? --- #
    header_26                   = read_uint(f, '<') # --- World Pos Z? --- #
    header_27                   = read_uint(f, '<') # --- float
    
    header_unknownF0            = read_uint(f, '<') # can be 0 - 38?

    SeekToNextRow(f)

    if CHUNK_MAGIC != 0xBBCACA12:
        print("Incorrect Magic byte. Are you sure this is the correct file?")
        return {'CANCELLED'}
    if CHUNK_VERSION != 121:
        print("Unexpected version: ", CHUNK_VERSION, "Expected: 121. Is this from some secret dev build??")
        return {'CANCELLED'}


# --- Texture List --- #
    chunk_texlist = []
    chunk_texcount = read_uint(f, '<')
    f.seek(chunk_texcount * 4, os.SEEK_CUR) # null filler
    for _ in range (chunk_texcount):
        chunk_texlist.append(read_cstr(f))
    SeekToNextRow(f)
    
    
# --- Models Header --- #
    #32B
    g_chunk_modelcount      = read_uint(f, '<')
    chunk_cityobjcount      = read_uint(f, '<')
    chunk_pc_Model0Count    = read_uint(f, '<')
    chunk_pc_UnknownCount3  = read_uint(f, '<')
    chunk_pc_UnknownCount4  = read_uint(f, '<')
    f.read(12)  # null
    
    
# --- gmodel data? --- #
    # 24B
    for _ in range (g_chunk_modelcount):    # these don't seem to affect anything.
        unk1 = read_uint(f, '<')
        f.read(12)   # null?
        unk5 = read_uint(f, '<')    # often ff
        unk6 = read_uint(f, '<')
    SeekToNextRow(f)
    

# --- City objects --- #
    # 96B
    chunk_city_objects = []
    for _ in range (chunk_cityobjcount):
        prop = chunk_city_object()

        x = read_float(f, '<')
        y = read_float(f, '<')
        z = read_float(f, '<')
        prop.pos = (x, y, z)

        f.read(72)  # contains rotation quaternion(s)? and something

        prop.unk1 = read_uint(f, '<')   # ff
        prop.model = read_uint(f, '<')
        prop.unk2 = read_uint(f, '<')   # changes crash game

        chunk_city_objects.append(prop)


# --- Unknown3 --- #
    # 100B
    for _ in range(chunk_pc_UnknownCount3):
        f.read(100)
    SeekToNextRow(f)


# --- Unknown4 ---#
    # 52B
    for _ in range(chunk_pc_UnknownCount4):
        x = read_float(f, '<')
        y = read_float(f, '<')
        z = read_float(f, '<')

        f.read(52 - 12)
    SeekToNextRow(f)

# --- Unknown5 World Pos --- #
    # 12B
    chunk_pc_UnknownCount5 = read_uint(f, '<')
    Unknown5List =[]
    for _ in range(chunk_pc_UnknownCount5):
        X = read_float(f, '<')
        Z = read_float(f, '<')
        Y = read_float(f, '<')
        Unknown5List.append([X, Y, Z])


# --- Unknown 6 --- #
    # 3B ??
    chunk_pc_UnknownCount6 = read_uint(f, '<')
    f.read(chunk_pc_UnknownCount6 * 3)


# --- Unknown 7 --- #
    # 4B
    chunk_pc_UnknownCount7 = read_uint(f, '<')
    for _ in range (chunk_pc_UnknownCount7):
        read_uint(f, '<')


# --- Unknown 8 --- #
    # 12B
    chunk_pc_UnknownCount8 = read_uint(f, '<')
    for _ in range(chunk_pc_UnknownCount8):
        f.read(12)
    SeekToNextRow(f)


# --- Havok Mopp Collision tree --- #
    chunk_pc_Havok_Mopp_length = read_uint(f, '<')
    SeekToNextRow(f)
    f.read(chunk_pc_Havok_Mopp_length)
    
    # Byte alignment 4
    if f.tell() & 0xfffffffc != f.tell():
        f.read(4)
        f.seek(f.tell() & 0xfffffffc)


# --- Unknown 10 2x World Pos --- #

    # 24B total
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
    
    # 20B
    for _ in range(chunk_pc_Model0Count):
        mesh = chunk_pc_model0_mesh()

        mesh.unknown0 = read_ushort(f, '<')      # Can only be either 7 or 0?? If 0, skip the mesh
        mesh.header1count = read_ushort(f, '<')
        mesh.indexCount = read_uint(f, '<')
        f.read(8)   # FF bytes
        f.read(4)   # null bytes
        model0_list.append(mesh)

    # 16B

    g_chunk_unk1s = []
    g_chunk_vsizes = []
    g_chunk_vcounts = []

    for mesh in model0_list:
        for _ in range(mesh.header1count):
            
            # physmodel
            if mesh.unknown0 == 7:
                mesh.unknown1 = read_uint(f, '<')
                mesh.vertCount = read_uint(f, '<')
                f.read(4)   # FF
                f.read(4)   # null

            # g_chunk model
            else:
                g_chunk_unk1s.append(read_ushort(f, '<'))    # unk1
                g_chunk_vsizes.append(read_ushort(f, '<'))   # vert length
                g_chunk_vcounts.append(read_uint(f, '<'))   # vert count
                f.read(4)   # FF
                f.read(4)   # null
    SeekToNextRow(f)

    # --- Static phys models, probably --- #
    for mesh in model0_list:
        if mesh.unknown0 == 7:
            mesh.vertices = chunk_pc_mesh_vertices(f, mesh.vertCount)
            SeekToNextRow(f)
            mesh.faces = chunk_pc_mesh_faces(f, mesh.indexCount)
            SeekToNextRow(f)



# --- Materials --- #
    chunk_materials = []

    chunk_material_count = read_uint(f, '<') # Matches Texture List length? Shaders??
    SeekToNextRow(f)
    chunk_shader_floats_count = read_uint(f, '<')
    f.read(8)
    chunk_pc_UnknownCount11c = read_uint(f, '<')
    chunk_pc_Unknown11c = read_uint(f, '<')

    # So I think the logic to get the length is this:
    # Unk11d = short at 0xc of this pattern
    # length = sum of every Unk11d value + 2 bytes for every Unk11d that's an odd number
    # This may still be wrong but it worked with every chunk I tried so far. What a pain.

    Unk11d_total = 0
    Unk11d_count = 0
    Unk11d_odds = 0

    Unk11f_total = 0
    Unk11f_count = 0

    Unk11f2_total = 0
    
    #24B
    for i in range(chunk_material_count):            
        mat = chunk_material()
        f.read(8)
        
        f.read(4)

        Unk11d = read_ushort(f, '<')
        if Unk11d != 0:
            Unk11d_total += Unk11d
            Unk11d_count += 1
            if Unk11d % 2 != 0:
                Unk11d_odds += 1
        
        mat.texcount = read_ushort(f, '<')
        if mat.texcount != 0:
            Unk11f_total += mat.texcount
            Unk11f_count += 1

        f.read(2)

        Unk11f2 = read_ushort(f, '<')
        if Unk11f2 != 0:
            Unk11f2_total += Unk11f2

        chunk_materials.append(mat)
        f.read(4)

    # --- Shaders --- #
    #6B
    for _ in range(Unk11d_total):   # Bit flags, maybe? Messing with these toggled uv repeat on for ultor flags.
        read_ushort(f, '<')
        read_ushort(f, '<')
        read_ushort(f, '<')

    #2B
    for _ in range(Unk11d_odds):
        read_ushort(f, '<')

    # Byte alignment 4
    if f.tell() & 0xfffffffc != f.tell():
        f.read(4)
        f.seek(f.tell() & 0xfffffffc)

    #16B
    for _ in range(chunk_material_count): # Messing with these break shaders.
        f.read(4)
        f.read(4)
        f.read(4)
        f.read(4)
    SeekToNextRow(f)

    #4B
    for _ in range(chunk_shader_floats_count):
        read_float(f, '<')  # Mostly colors, sometimes affects scrolling texture speed and probably more things.

    # 64B
    for i, mat in enumerate(chunk_materials):
        mat.textures = []
        mat.texflags = []
        for ii in range(16):
            tex_id = read_ushort(f, '<')
            tex_fl = read_ushort(f, '<')

            if ii == mat.texcount:
                f.read((15-ii) * 4)
                break
            
            mat.textures.append(tex_id)
            mat.texflags.append(tex_fl)

    Unk11g_total = 0
    for _ in range((chunk_pc_UnknownCount11c)):
        f.read(8)
        Unk11g_total += read_ushort(f, '<')
        read_ushort(f, '<')  # no visible effect
        f.read(4)

    for _ in range((Unk11g_total)):
        f.read(4)   # no visible changes

    # --- g_chunk models --- #
    gmodels = []
    for i in range(g_chunk_modelcount):
        gmodel = g_chunk_model()

        check_y = False

        f.read(24)  # 6 floats, a box?
        f.read(4)   # null?
        f.read(4)   # always uint 1?
        f.read(4)   # unk ff flag
        if read_uint(f, '<') == 0xffffFFFF: check_y = True
        SeekToNextRow(f)
        
        # get x
        read_ushort(f, '<')  # short
        gmodel.xcount       = read_ushort(f, '<')
        read_uint(f,'<')    # ff flag
        gmodel.unkx         = read_uint(f, '<')
        SeekToNextRow(f)

        # get y
        gmodel.ycount = 0
        if check_y:
            f.read(2)       # short
            gmodel.ycount   = read_ushort(f, '<')
            f.read(4)       # ff flag
            gmodel.unky     = read_uint(f, '<')
            SeekToNextRow(f)

        gmodel.meshes0 = []
        for _ in range(gmodel.xcount):
            mesh = g_chunk_model_mesh0()

            mesh.vert_bank      = read_uint(f, '<')
            mesh.index_offset   = read_uint(f, '<')
            mesh.vert_offset    = read_uint(f, '<')
            mesh.index_count    = read_ushort(f, '<')
            mesh.mat            = read_ushort(f, '<')

            gmodel.meshes0.append(mesh)

        for _ in range(gmodel.ycount):
            f.read(12)        # null?
            read_uint(f, '<') # no effect?

        gmodels.append(gmodel)
    # pull models from g_chunk
    models = utils.g_chunker.gchunk2mesh(g_chunk_filepath, g_chunk_vsizes, g_chunk_vcounts, model0_list[0].indexCount, gmodels)

    temp_i = 0

    if not os.path.exists(export_dir): os.mkdir(export_dir)

    # example: sr2_chunk102.mtl
    export_mtl_name = export_mtl_name = os.path.basename(filepath).split('.', 1)[0] + ".mtl"
    
    # example: /path/to/sr2_chunk102/sr2_chunk102.mtl
    export_mtl_path = os.path.join(export_dir, export_mtl_name)

    for mesh in models:
        export_obj_name = os.path.join(export_dir, "g_mdl_" + str(temp_i) + ".obj")
        #print("exporting: " + export_name)
        utils.modelhandler.export_obj(mesh, export_obj_name, export_mtl_name)
        temp_i +=1


    # --- Cullbox --- #
    cullboxes = []

    #80B
    for i in range(header_cullboxcount):
        cullbox = chunk_cullbox()

        x0 = read_float(f, '<') # box max
        y0 = read_float(f, '<')
        z0 = read_float(f, '<')

        f.read(4)   # null

        x1 = read_float(f, '<') # box min
        y1 = read_float(f, '<')
        z1 = read_float(f, '<')

        cullbox.box      = (x0, y0, z0, x1, y1, z1)
        cullbox.distance = read_float(f, '<')
        f.read(16)
        read_uint(f, '<')   # Bit flags. 11th bit will fix transparent textures.
        read_uint(f, '<')   # Value is always 2^n. If too small the model doesn't appear.
        f.read(8)

        cullbox.model    = read_uint(f, '<') # gchunk_model

        f.read(12)

        cullboxes.append(cullbox)
        
    for i in range (header_cullboxcount):
        cullboxes[i].name = read_cstr(f)

    SeekToNextRow(f)

    timer = time.time() - timer
    print("end, ", hex(f.tell()), "\nfinished in ",timer, " seconds")
    return {'FINISHED'}

import_models = False
main(sys.argv[1], import_models)
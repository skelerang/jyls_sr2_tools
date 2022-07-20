import sys
import os.path
import shutil
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
    dirname = os.path.dirname(filepath)
    basename = os.path.basename(filepath)
    g_filepath = os.path.splitext(filepath)[0]+".g_chunk_pc"
    g_basename = os.path.basename(g_filepath)


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
    
    OFF_MODELHEADER = f.tell()

    # 20B
    for _ in range(chunk_pc_Model0Count):
        mesh = chunk_pc_model0_mesh()

        mesh.unknown0 = read_ushort(f, '<')      # Can only be either 7 or 0?? If 0, skip the mesh
        mesh.header1count = read_ushort(f, '<')
        mesh.indexCount = read_uint(f, '<')
        f.read(8)   # FF bytes
        f.read(4)   # null bytes
        model0_list.append(mesh)

    
    g_chunk_vtypes = []
    g_chunk_vsizes = []
    g_chunk_vcounts = []

    # 16B
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
                # vtypes: This somehow tells what types of data the vert contains?
                # null for physmodels (which obviously don't have any extra data like uv's)
                g_chunk_vtypes.append(read_ushort(f, '<'))
                g_chunk_vsizes.append(read_ushort(f, '<'))  # vert length
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
    OFF_GMODELS = f.tell()

    gmodel_entries = []
    for i in range(g_chunk_modelcount):
        gmodel = g_model_entry()

        check_x = False
        check_y = False

        gmodel.bbox = (
            read_float(f, '<'), # x
            read_float(f, '<'), # y
            read_float(f, '<'), # z
            read_float(f, '<'), # x
            read_float(f, '<'), # y
            read_float(f, '<'), # z
        )
        gmodel.unk0 = read_uint(f, '<')
        gmodel.unk1 = read_uint(f, '<')
        
        if read_uint(f, '<') == 0: gmodel.mesh0_count = 0
        else: check_x = True
        if read_uint(f, '<') == 0: gmodel.y_count = 0
        else: check_y = True
        SeekToNextRow(f)
        
        if check_x:
            gmodel.mesh0_unk0   = read_ushort(f, '<')
            gmodel.mesh0_count  = read_ushort(f, '<')
            gmodel.mesh0_unk1   = read_uint(f, '<') # ff flag
            gmodel.mesh0_unk2   = read_uint(f, '<')
            SeekToNextRow(f)

        if check_y:
            gmodel.y_unk0       = read_ushort(f, '<')
            gmodel.y_count      = read_ushort(f, '<')
            gmodel.y_unk1       = read_uint(f, '<') # ff flag
            gmodel.y_unk2       = read_uint(f, '<')
            SeekToNextRow(f)

        gmodel.mesh0_entries = []
        for _ in range(gmodel.mesh0_count):
            mesh = g_model_mesh0_entry()
            mesh.vert_bank      = read_uint(f, '<')
            mesh.index_offset   = read_uint(f, '<')
            mesh.vert_offset    = read_uint(f, '<')
            mesh.index_count    = read_ushort(f, '<')
            mesh.mat            = read_ushort(f, '<')
            gmodel.mesh0_entries.append(mesh)

        gmodel.y_entries = []
        for _ in range(gmodel.y_count):
            y = g_model_y_entry()
            y.unk0 = read_uint(f, '<')
            y.unk1 = read_uint(f, '<')
            y.unk2 = read_uint(f, '<')
            y.unk3 = read_ushort(f, '<')
            y.mat = read_ushort(f, '<')
            gmodel.y_entries.append(y)

        gmodel_entries.append(gmodel)

    OFF_GMODELS_END = f.tell()


    meshes = []
    for fname in sorted(os.listdir(export_dir)):
        if fname.endswith(".obj"):
            meshes.append(utils.modelhandler.import_obj(os.path.join(export_dir, fname)))

    utils.g_chunker.split_part2(g_filepath, g_chunk_vsizes, g_chunk_vcounts, model0_list[0].indexCount)
    gmodel_entries, total_indices, total_verts = utils.g_chunker.build_part1(g_filepath, meshes, gmodel_entries)


    new_chunk_path = os.path.join(dirname, "new_" + basename)
    new_g_chunk_path = os.path.join(dirname, "new_" + g_basename)

    #shutil.copy(filepath, new_chunk_path)
    new_chunk = open(new_chunk_path, 'w+b')
    
    new_g_chunk = open(new_g_chunk_path, 'wb')

    part1 = open(g_filepath + ".part1", 'rb')
    part2 = open(g_filepath + ".part2", 'rb')
    new_g_chunk.write(part1.read())
    new_g_chunk.write(part2.read())
    part1.close()
    part2.close()
    new_g_chunk.close()
    os.remove(g_filepath + ".part1")
    os.remove(g_filepath + ".part2")

    # --- New chunk pre-gmodel
    f.seek(0)
    new_chunk.write(f.read(OFF_GMODELS))

    new_chunk.seek(OFF_MODELHEADER)
    for i, mesh in enumerate(model0_list):
        new_chunk.read(2) # mesh.unknown0
        new_chunk.read(2) # mesh.header1count
        if i == 0:
            write_uint(total_indices, new_chunk, '<')#indexCount
        else:
            new_chunk.read(4)
        new_chunk.read(8)   # FF bytes
        new_chunk.read(4)   # null bytes


    for i, mesh in enumerate(model0_list):
        for ii in range(mesh.header1count):
            
            # physmodel
            if mesh.unknown0 == 7:
                pass

            # g_chunk model
            else:
                if i == 0:
                    if ii == 0:
                        write_ushort(258, new_chunk, '<')   #?? vert data type
                        write_ushort(20, new_chunk, '<')    # v length
                        write_uint(total_verts, new_chunk, '<')
                        new_chunk.read(4)   # FF
                        new_chunk.read(4)   # null
                    else:
                        write_ushort(0, new_chunk, '<')
                        write_ushort(0, new_chunk, '<')
                        write_uint(0, new_chunk, '<')
                        new_chunk.read(4)   # FF
                        new_chunk.read(4)   # null
                
    SeekToNextRow(new_chunk)

    new_chunk.seek(OFF_GMODELS)

    # --- New chunk gmodel

    for gmodel in gmodel_entries:

        for value in gmodel.bbox:
            write_float(value, new_chunk, '<')
        
        write_uint(gmodel.unk0, new_chunk, '<')
        write_uint(gmodel.unk1, new_chunk, '<')
        
        if gmodel.mesh0_count == 0: write_uint(0, new_chunk, '<')
        else:                       write_uint(0xffffFFFF, new_chunk, '<')

        if gmodel.y_count == 0: write_uint(0, new_chunk, '<')
        else:                       write_uint(0xffffFFFF, new_chunk, '<')

        WriteToNextRow(new_chunk)
        
        if gmodel.mesh0_count != 0:
            write_ushort(gmodel.mesh0_unk0, new_chunk, '<')
            write_ushort(gmodel.mesh0_count, new_chunk, '<')
            write_uint(gmodel.mesh0_unk1, new_chunk, '<') # ff flag
            write_uint(gmodel.mesh0_unk2, new_chunk, '<')
            WriteToNextRow(new_chunk)

        if gmodel.y_count != 0:
            write_ushort(gmodel.y_unk0, new_chunk, '<')
            write_ushort(gmodel.y_count, new_chunk, '<')
            write_uint(gmodel.y_unk1, new_chunk, '<') # ff flag
            write_uint(gmodel.y_unk2, new_chunk, '<')
            WriteToNextRow(new_chunk)

        for mesh in gmodel.mesh0_entries:
            write_uint(mesh.vert_bank, new_chunk, '<')
            write_uint(mesh.index_offset, new_chunk, '<')
            write_uint(mesh.vert_offset, new_chunk, '<')
            write_ushort(mesh.index_count, new_chunk, '<')
            write_ushort(mesh.mat, new_chunk, '<')

        for y in gmodel.y_entries:
            write_uint(y.unk0, new_chunk, '<')
            write_uint(y.unk1, new_chunk, '<')
            write_uint(y.unk2, new_chunk, '<')
            write_ushort(y.unk3, new_chunk, '<')
            write_ushort(y.mat, new_chunk, '<')


    #new_chunk.close()
#
    #return

    # --- New chunk post-gmodel
    f.seek(OFF_GMODELS_END)
    new_chunk.write(f.read())






    

    #new_chunk.seek(OFF_GMODELS)
    #imesh = 0
    #for gmodel in gmodel_entries:
#
    #    check_y = False
#
    #    new_chunk.read(40)
    #    SeekToNextRow(new_chunk)
    #    
    #    new_chunk.read(12)
    #    SeekToNextRow(new_chunk)
#
    #    if gmodel.y_count > 0:
    #        new_chunk.read(12)
    #        SeekToNextRow(new_chunk)
    #    
    #    for i, mesh in enumerate(gmodel.mesh0_entries):
    #        print("patching entry in chunk...",imesh)
    #        write_uint(0, new_chunk, '<')#mesh.vert_bank      = read_uint(f, '<')
    #        write_uint(gdata[1][imesh], new_chunk, '<')#mesh.index_offset   = read_uint(f, '<')
    #        write_uint(gdata[2][imesh], new_chunk, '<')#mesh.vert_offset    = read_uint(f, '<')
    #        write_ushort(gdata[3][imesh], new_chunk, '<')#mesh.index_count    = read_ushort(f, '<')
    #        write_ushort(gdata[4][imesh], new_chunk, '<')#mesh.mat            = read_ushort(f, '<')
    #        imesh += 1
#
    #    for _ in range(gmodel.y_count):
    #        new_chunk.read(16)        # null?

    timer = time.time() - timer
    print("end, ", hex(new_chunk.tell()), "\nfinished in ",timer, " seconds")
    f.close()
    new_chunk.close()
    return {'FINISHED'}

import_models = False
main(sys.argv[1], import_models)
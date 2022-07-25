# --- Jyl's SR2 g_chunk utility --- #
#

import os.path

from utils.binny import *
from utils.sr2_chunk_classes import *

if __name__ == '__main__':
    print("Run the main chunk importer instead!")

# g_chunks are all model data.

# --- Part 1:
# Vertices are stored in a couple different blobs, like 7 or 8 of them.
# Indices are in one continuous blob after verts.

# --- Part 2:
# Not blobs. Separate models
# Vsize varies with each model. No clue where to get anything.

def gchunk2mesh(filepath, unk2bcounts, uvcounts, vsizes, vcounts, icount, gmodels):

    f = open(filepath, 'r+b')

    # --- Part 1 --- #
    vblob_count = len(vsizes)

    models = []

    vert_banks = []
    index_blob = []

    # --- Vertices --- #
    for i in range(vblob_count):
        vert_blob = []
        print(i, hex(f.tell()))

        for _ in range(vcounts[i]):
            x = read_float(f, '<')
            y = read_float(f, '<')
            z = read_float(f, '<')

            for _ in range(unk2bcounts[i]):
                f.read(2)
            
            uvs = []
            for _ in range(uvcounts[i]):
                u = read_short(f, '<') / 256
                v = read_short(f, '<') / 256
                uvs.append((u, v))
            if uvcounts[i] == 0: uvs.append((0, 0)) # It's *possible* to have no UVs
            
            u = uvs[0][0]   # for now we just ignore the extras.
            v = uvs[0][1]

            vert_blob.append((x, y, z, u, v))
        vert_banks.append(vert_blob)
        SeekToNextRow(f)


    # --- Indices --- #
    for _ in range(icount):
        index_blob.append(read_ushort(f, '<'))

    # --- Assemble this mess --- #
    models = []

    for i, gmodel in enumerate(gmodels):
        model = []
        for gmesh in gmodel.mesh0_entries:
            mesh = [[],[],[],0]   # [verts], [uvs], [faces], material
            gmesh.vert_count = 0

            # --- V count isn't stored explicitly so gotta pull it if from indices.
            for ind_i in range(gmesh.index_count):
                index = index_blob[gmesh.index_offset + ind_i]
                gmesh.vert_count = max(gmesh.vert_count, index + 1)

            # --- Vertices
            for v_i in range(gmesh.vert_count):
                vert = vert_banks[gmesh.vert_bank][gmesh.vert_offset + v_i]
                mesh[0].append((vert[0],vert[1], vert[2]))  # x, y, z
                mesh[1].append((vert[3], vert[4]))  # u, v
            
            # --- Faces
            for ind_i in range(gmesh.index_count-2):
                # Odd faces are flipped
                if (ind_i % 2) == 0:
                    i0 = index_blob[gmesh.index_offset + ind_i]+1
                    i1 = index_blob[gmesh.index_offset + ind_i+1]+1
                    i2 = index_blob[gmesh.index_offset + ind_i+2]+1
                else:
                    i2 = index_blob[gmesh.index_offset + ind_i]+1
                    i1 = index_blob[gmesh.index_offset + ind_i+1]+1
                    i0 = index_blob[gmesh.index_offset + ind_i+2]+1

                mesh[2].append((i0,i1,i2))

            # --- Material
            mesh[3] = gmesh.mat

            model.append(mesh)
        if len(model) != 0:
            models.append(model)

    # --- Part 2 --- #
    # You tell me ¯\_(ツ)_/¯
    f.close()
    return models

def get_part2off(filepath, vsizes, vcounts, icount):

    f = open(filepath, 'r+b')
    vblob_count = len(vsizes)

    # --- Vertices --- #
    for i in range(vblob_count):
        f.seek(vsizes[i] * vcounts[i], os.SEEK_CUR)
        SeekToNextRow(f)

    # --- Indices --- #
    f.seek(icount * 2, os.SEEK_CUR)
    SeekToNextRow(f)

    f.close()
    return f.tell()

def split_part2(filepath, vsizes, vcounts, icount):

    f = open(filepath, 'r+b')

    # --- Skip part1 --- #
    vblob_count = len(vsizes)
    for i in range(vblob_count):
        f.seek(vsizes[i] * vcounts[i], os.SEEK_CUR)
        SeekToNextRow(f)
    f.seek(icount * 2, os.SEEK_CUR)
    SeekToNextRow(f)
    
    # --- Save part2 --- #
    filepath2 = filepath + ".part2"
    f_p2 = open(filepath2, 'wb')
    f_p2.write(f.read())

    f_p2.close()
    f.close()



# input mesh structure
# [ mesh
#     [(x, y, z, u, v), ...], # verts
#     [(0, 1, 2), ...], # triangles
#     0 # mat
# ]

def build_part1(filepath, models, gmodel_entries):
    f = open(filepath + ".part1", 'wb')

    # vert_banks = []
    # index_offsets = []
    # vert_offsets = []
    # index_counts = []
    # materials = []
    verts_total = 0

    # --- Vert Blob --- #
    for i, model in enumerate(models):
        print("gchunk p1 mdl", i, "/", len(models)-1)
        entries = []
        for ii, mesh in enumerate(model):
            entry = g_model_mesh0_entry()
            entry.vert_bank = 0
            for vert in mesh[0]:
                write_float(vert[0], f, '<')    # x
                write_float(vert[1], f, '<')    # y
                write_float(vert[2], f, '<')    # z
                write_uint(0x7FFF7F7F, f)       # dunno what this is.
                write_short(int(vert[3] * 256), f, '<')     # u
                write_short(int(vert[4] * 256), f, '<')     # v
            entry.vert_offset = verts_total
            entry.vert_count = len(mesh[0])
            entry.mat = mesh[2]
            #vert_offsets.append(verts_total)
            #materials.append(mesh[2])
            verts_total += entry.vert_count
            entries.append(entry)
        gmodel_entries[i].mesh0_entries = entries
    
    # byte alignment
    while True:
        if f.tell() & 0xfffffff0 == f.tell():
            break
        write_ubyte(0, f)

    # --- Index buffer blob --- #
    # Index buffer is compressed: if successive tris share an edge,
    # they are represented with just 4 indices instead of 6
    # This doesn't even try to optimise the order but that shouldn't matter.
    buffer_blob = []
    indices_total = 0
    for i, model in enumerate(models):
        for ii, mesh in enumerate(model):
            gmodel_entries[i].mesh0_entries[ii].index_offset = indices_total
            buffer = []
            gmodel_entries[i].mesh0_entries[ii].index_count = 0
            for iii, tri in enumerate(mesh[1]):

                # Odd faces are flipped
                if (iii % 2) == 0:
                    A = tri[0]
                    B = tri[1]
                    C = tri[2]
                else:
                    A = tri[2]
                    B = tri[1]
                    C = tri[0]

                if iii == 0:
                    buffer.append(A)
                    buffer.append(B)
                    buffer.append(C)
                    gmodel_entries[i].mesh0_entries[ii].index_count += 3

                else:
                    # Best case, new tri with just one index
                    if buffer[-2] == A and buffer[-1] == B:
                        buffer.append(C)
                        gmodel_entries[i].mesh0_entries[ii].index_count += 1

                    # Neutral case, new tri takes 3 indices  
                    elif buffer[-1] == A:
                        # same vert twice makes degenerate tris, which are ignored
                        # so the previous legit tri and this don't mix
                        buffer.append(A)
                        buffer.append(B)
                        buffer.append(C)
                        gmodel_entries[i].mesh0_entries[ii].index_count += 3

                    # Worst case, new tri takes 5 indices. It's probably rare enough to offset the cost.
                    else:
                        buffer.append(buffer[-1]) # Make degen triangles
                        buffer.append(A) # Make degen triangles again
                        buffer.append(A)
                        buffer.append(B)
                        buffer.append(C)
                        gmodel_entries[i].mesh0_entries[ii].index_count += 5
            
            for index in buffer:
                buffer_blob.append(index)

            #index_counts.append(index_count)
            indices_total += gmodel_entries[i].mesh0_entries[ii].index_count
            
    for index in buffer_blob:
        write_short(index, f, '<')
    
    # byte alignment
    while True:
        if f.tell() & 0xfffffff0 == f.tell():
            break
        write_ubyte(0, f)
    f.close()
    return gmodel_entries, indices_total, verts_total #[vert_banks, index_offsets, vert_offsets, index_counts, materials, verts_total]
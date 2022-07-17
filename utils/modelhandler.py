from collections import OrderedDict

# We're splitting the model into multiple meshes by material.
# This function is terrible.
def import_obj(filepath):
    f = open(filepath, 'r')
    print("reading", filepath)

    meshes = []
    vertbuf = []
    uvbuf = []
    materials = []
    temp_vbuffers = []
    temp_ibuffers = []
    currentmesh = -1

    while (line := f.readline().rstrip()):
        words = line.split()

        if len(words) > 1:
            match words[0]:

                case "v":
                    vertbuf.append((float(words[1]),float(words[2]),float(words[3])))

                case "vt":
                    uvbuf.append((float(words[1]),float(words[2])))

                case "usemtl":  # Usemtl is expected before faces.
                    print(line)
                    materials.append(int(words[1][3:]))
                    temp_vbuffers.append(OrderedDict())
                    temp_ibuffers.append([])
                    currentmesh += 1
            
                case "f":
                    # if no materials, like in physmodel
                    if currentmesh < 0:
                        currentmesh = 0

                    # Example line: f 57/71/57 63/82/63 53/72/53
                    # Format is v/vt/vn, vn is ignored.
                    A = words[1].split("/")
                    B = words[2].split("/")
                    C = words[3].split("/")

                    # --- Vert tuples --- #
                    #
                    # It is assumed that v and vt match; in wavefront pos and uv are
                    # by loop and not by vertex so they don't match, uv's will break.
                    #
                    # Verts are written to each buffer every time a face mentions them.
                    # Maybe dumb, but this ensures that every v used by a face is stored
                    # and not one unused. So verts may be written multiple times,
                    # overwriting the prev and potentially pulling a different uv.

                    temp_vbuffers[currentmesh][A[0]] = (
                        vertbuf[int(A[0])-1][0],    # x
                        vertbuf[int(A[0])-1][1],    # y
                        vertbuf[int(A[0])-1][2],    # z
                        uvbuf[int(A[1])-1][0],      # u
                        uvbuf[int(A[1])-1][1],      # v
                        )
                    temp_vbuffers[currentmesh][B[0]] = (
                        vertbuf[int(B[0])-1][0],
                        vertbuf[int(B[0])-1][1],
                        vertbuf[int(B[0])-1][2],
                        uvbuf[int(B[1])-1][0],
                        uvbuf[int(B[1])-1][1],
                        )
                    temp_vbuffers[currentmesh][C[0]] = (
                        vertbuf[int(C[0])-1][0],
                        vertbuf[int(C[0])-1][1],
                        vertbuf[int(C[0])-1][2],
                        uvbuf[int(C[1])-1][0],
                        uvbuf[int(C[1])-1][1],
                        )

                    # Faces
                    temp_ibuffers[currentmesh].append((A[0], B[0], C[0]))

    for i, vbuf in enumerate(temp_vbuffers):
        meshes.append([[],[],materials[i]])
        for v in vbuf.values():
            meshes[i][0].append(v)


    for i, ibuf in enumerate(temp_ibuffers):
        for tri in ibuf:
            A = -1
            B = -1
            C = -1

            # Here we skip unused vert numbers in ibufs.
            # So we turn the numbers
            # from like this:    7, 23, 76, 334, ...
            # to like this:      0, 1, 2, 3, ...
            # Now they match vbufs which lack the unused vertices.

            # You seriously need to do this to get index from key.
            for iterator, key in enumerate(temp_vbuffers[i].keys()):
                if key == tri[0]:
                    A = iterator
                if key == tri[1]:
                    B = iterator
                if key == tri[2]:
                    C = iterator
                if A!=-1 and B!=-1 and C!=-1:
                    break
            meshes[i][1].append((A,B,C))

    return meshes
            

# export_obj vs export_obj_v2
# gonna remove v1 at some point
#
# input model structure v1
# [ model
#   [ mesh
#     [(x, y, z), ...], # verts
#     [(u, v),    ...], # uv
#     [(0, 1, 2), ...], # faces
#     uint mat
#   ],
#   ...
# ]

# input model structure v2
# [ model
#   [ mesh
#     [(x, y, z, u, v), ...], # verts
#     [(0, 1, 2), ...], # faces
#     uint mat
#   ],
#   ...
# ]
        

def export_obj_v2(model, filepath, mtlfilepath):
    with open(filepath, 'w') as f:
        v_off = 0
        f.write("mtllib " + mtlfilepath + "\n")
        for i, mesh in enumerate(model):
            #f.write("g group" + str(i) + "\n")
            f.write("usemtl mat" + str(mesh[2]) + "\n")
            for vert in mesh[0]:
                f.write("v " + str(vert[0]) + " " + str(vert[1]) + " " + str(vert[2]) + "\n")

            for vert in mesh[0]:
                f.write("vt " + str(vert[3]) + " " + str(vert[4]) + "\n")

            for face in mesh[1]:
                v1 = str(face[0] + 1 + v_off)
                v2 = str(face[1] + 1 + v_off)
                v3 = str(face[2] + 1 + v_off)
                # example output:
                # f 1/1 2/2 3/3 
                # where 1/1 means v1/vt1
                f.write("f " + v1 + "/" + v1 + " " + v2 + "/" + v2 + " " + v3 + "/" + v3 + "\n")
                
            v_off += len(mesh[0])
        f.close()


def export_obj(model, filepath, mtlfilepath):
    with open(filepath, 'w') as f:
        v_off = 0
        f.write("mtllib " + mtlfilepath + "\n")
        for i, mesh in enumerate(model):
            #f.write("g group" + str(i) + "\n")
            f.write("usemtl mat" + str(mesh[3]) + "\n")
            for vert in mesh[0]:
                f.write("v " + str(vert[0]) + " " + str(vert[1]) + " " + str(vert[2]) + "\n")

            for uv in mesh[1]:
                f.write("vt " + str(uv[0]) + " " + str(uv[1]) + "\n")

            for face in mesh[2]:
                v1 = str(face[0] + v_off)
                v2 = str(face[1] + v_off)
                v3 = str(face[2] + v_off)
                # example output:
                # f 1/1 2/2 3/3 
                # where 1/1 means v1/vt1
                f.write("f " + v1 + "/" + v1 + " " + v2 + "/" + v2 + " " + v3 + "/" + v3 + "\n")
                
            v_off += len(mesh[0])
        f.close()

# input material structure
# [ materials
#   (int texture, )
# ]
def export_mtl(materials, filepath):
    with open(filepath, 'w') as f:
        f.write("# Material count: " + str(len(materials)))
        for i, mat in enumerate(materials):
            f.write("newmtl mat" + str(i) + "\n")
            for ii, tex in enumerate(mat):
                if ii == 0:
                    f.write("map_Kd ./textures/" + tex + "\n")
                else:
                    f.write("# tex"+str(ii)+" ./textures/" + tex + "\n")
            f.write("\n")
        f.close()

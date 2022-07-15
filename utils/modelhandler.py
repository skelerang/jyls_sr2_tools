

# input model structure
# [ model
#   [ mesh
#     [(x, y, z), ...], # verts
#     [(u, v),    ...], # uv
#     [(0, 1, 2), ...], # faces
#     uint mat
#   ],
# ]

class mdl_export_format:
    verts: []
    faces: []
    uvs: []

def export_obj(model, filename, mtlfilename):
    with open(filename, 'w') as f:
        v_off = 0
        f.write("mtllib " + mtlfilename + "\n")
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
def export_mtl(materials, filename):
    with open(filename, 'w') as f:
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

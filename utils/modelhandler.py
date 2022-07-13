

# input model structure
# [ model
#   [ mesh
#     [(x, y, z), ...] # verts
#     [(u, v),    ...] # uv
#     [(0, 1, 2), ...] # faces
#   ],
# ]

class mdl_export_format:
    verts: []
    faces: []
    uvs: []

def export(model, filename):
    with open(filename, 'w') as f:
        v_off = 0
        for i, mesh in enumerate(model):
            f.write("o obj" + str(i) + "\n")
            for vert in mesh[0]:
                f.write("v " + str(vert[0]) + " " + str(vert[1]) + " " + str(vert[2]) + "\n")

            for uv in mesh[1]:
                f.write("vt " + str(uv[0]) + " " + str(uv[1]) + "\n")

            for face in mesh[2]:
                f.write("f " + str(face[0] + v_off) + " " + str(face[1] + v_off) + " " + str(face[2] + v_off) + "\n")
                
            v_off += len(mesh[0])
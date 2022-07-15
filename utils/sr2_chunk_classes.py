class chunk_material:
    texcount: int
    textures: [] # up to 16 ushorts.
    texflags: [] # probably? 2B for each tex.

class chunk_city_object:
    pos: ()
    # rotation
    unk1: int # ff flag?
    model: int
    unk2: int

class chunk_cullbox:    # TODO: can this be merged with chunk_city_object?
    box: ()             # (max_x, max_y, max_z, min_x, min_y, min_z)
    distance: float
    model: int
    name: str

class g_chunk_model_mesh0:
    vert_bank: int
    index_offset: int
    index_count: int
    vert_offset: int
    vert_count: int # Not stored explicitly. Get this from indices.
    mat: int


class g_chunk_model:
    bbox: tuple # 6 floats, probs a box
    xcount: int
    unkx: int
    ycount: int
    unky: int
    meshes0: []
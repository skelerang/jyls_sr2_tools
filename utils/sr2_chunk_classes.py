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

# g_ means g_chunk
class g_model_mesh0_entry:
    vert_bank: int
    index_offset: int
    index_count: int
    vert_offset: int
    vert_count: int # Not stored explicitly. Get this from indices.
    mat: int

class g_model_y_entry:
    unk0: int   # always null?
    unk1: int   # always null?
    unk2: int   # always null?
    unk3: int   # unknown
    mat: int

class g_model_entry:
    bbox: tuple # 6 floats, probs a box
    unk0: int   # 0?
    unk1: int   # 1?

    mesh0_unk0: int
    mesh0_count: int
    mesh0_unk1: int  # ff flag?
    mesh0_unk2: int

    y_unk0: int
    y_count: int
    y_unk1: int  # ff flag?
    y_unk2: int
    
    mesh0_entries: []
    y_entries: []
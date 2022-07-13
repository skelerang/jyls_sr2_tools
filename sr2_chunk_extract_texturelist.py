import sys
import os.path

from utils.binny import *



def main(filepath):
    print()
    print("Opening file: ", filepath)
    f = open(filepath, 'rb')

    export_dir = os.path.splitext(filepath)[0]
    if not os.path.exists(export_dir): os.mkdir(export_dir)


# --- Header --- #
    # Header 256B total
    CHUNK_MAGIC                 = read_uint(f, '<')
    CHUNK_VERSION               = read_uint(f, '<')     # sr2 pc chunks are ver. 121

    if CHUNK_MAGIC != 0xBBCACA12:
        print("Incorrect Magic byte. Are you sure this is the correct file?")
        return {'CANCELLED'}
    if CHUNK_VERSION != 121:
        print("Unexpected version: ", CHUNK_VERSION, "Expected: 121. Is this from some secret dev build??")
        return {'CANCELLED'}

    f.seek(0x100)

# --- Texture List --- #
    chunk_texlist = []
    chunk_texcount = read_uint(f, '<')
    f.seek(chunk_texcount * 4, os.SEEK_CUR) # null filler
    for _ in range (chunk_texcount):
        chunk_texlist.append(read_cstr(f))
    SeekToNextRow(f)
    
    export_name = os.path.join(export_dir, "texturelist.txt")
    print(export_name)
    out = open(export_name, 'w')

    for i, tex in enumerate(chunk_texlist):
        out.write(str(i) + ": " + tex + "\n")

main(sys.argv[1])
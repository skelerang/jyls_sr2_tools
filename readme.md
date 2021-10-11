chunk_pc_import_mesh0.py:
  This imports models from the chunk, it's probably the one you're after.
  Warning: Works on some chunks, causes Blender to crash on others.

sr2_chunk_pc_import.py:
  Old, broken.
  
traverse_the_file.py:
  For development

Knobby:
The chunk_pc file is a loadable part of the world. It is what is needed for a physical chunk of the world. This includes the level geometry, level collision, sidewalk data, traffic splines, world objects, textures, etc. I say etc, but it really is probably just the tip of the iceberg. This is a massive monolithic file full of all kinds of things.

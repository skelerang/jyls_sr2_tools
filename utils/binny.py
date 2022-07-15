# --- Binny --- #
# collection of binary data functions

import struct

#TODO: write missing funcs
def read_byte(file_object, endian = '>'):
    data = struct.unpack(endian+'B', file_object.read(1))[0]
    return data
def write_byte(n, file_object, endian = '>'):
    data = struct.pack(endian+'B', n)
    file_object.write(data)

def read_short(file_object, endian = '>'):
    data = struct.unpack(endian+'h', file_object.read(2))[0]
    return data
def write_short(n, file_object, endian = '>'):
    data = struct.pack(endian+'h', n)
    file_object.write(data)

def read_ushort(file_object, endian = '>'):
    data = struct.unpack(endian+'H', file_object.read(2))[0]
    return data
def write_ushort(n, file_object, endian = '>'):
    data = struct.pack(endian+'H', n)
    file_object.write(data)

def read_int(file_object, endian = '>'):
    data = struct.unpack(endian+'i', file_object.read(4))[0]
    return data
def write_int(n, file_object, endian = '>'):
    data = struct.pack(endian+'i', n)
    file_object.write(data)

def read_uint(file_object, endian = '>'):
    data = struct.unpack(endian+'I', file_object.read(4))[0]
    return data
def write_uint(n, file_object, endian = '>'):
    data = struct.pack(endian+'I', n)
    file_object.write(data)

def read_float(file_object, endian = '>'):
    data = struct.unpack(endian+'f', file_object.read(4))[0]
    return data
def write_float(n, file_object, endian = '>'):
    data = struct.pack(endian+'f', n)
    file_object.write(data)

def read_half(file_object, endian = '>'):# Sometimes I feel dumb.
    data = struct.unpack(endian+'e', file_object.read(2))[0]
    return data
def write_half(n, file_object, endian = '>'):
    data = struct.pack(endian+'e', n)
    file_object.write(data)

def read_cstr(f):
    return ''.join(iter(lambda: f.read(1).decode('ascii'), '\x00'))

def modify_bit( n,  p,  b):
    mask = 1 << p
    return (n & ~mask) | ((b << p) & mask)

def SeekToNextRow(f):    # Byte alignment seek so least significant number is 0 (like 0xXXX0).
    offset = f.tell()
    if offset & 0xfffffff0 != offset:
        offset += 16                    # get to next row
        offset = offset & 0xfffffff0    # get to beginning of this row
        f.seek(offset)
def unpack_float32(data: bytes) -> list[float]:
    """Deserializes the "raw bytes" format into a list of floats"""
    from struct import unpack
    num_floats = len(data) // 4  # each float32 is 4 bytes
    return list(unpack("%sf" % num_floats, data))
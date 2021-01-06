import hashlib as hash

__all__ = ['sha1_hex']

# 4 MB at a time
BLOCKSIZE = 4 * 1024 * 1024


def sha1_hex(path):
    """return sha1 hex digest of a file"""
    sha = hash.sha1()
    with open(path, 'rb') as kali_file:
        file_buffer = kali_file.read(BLOCKSIZE)
        while len(file_buffer) > 0:
            sha.update(file_buffer)
            file_buffer = kali_file.read(BLOCKSIZE)
    return sha.hexdigest()

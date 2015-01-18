import array
# ripped off from  mervbot(snrubb) but not right...

G4_MODIFIER = 0x77073096  # I am pretty sure these "constants"
G16_MODIFIER = 0x076dc419  # are all constants.  That is to
G64_MODIFIER = 0x1db71064  # say, maybe they are dependant on
G256_MODIFIER = 0x76dc4190  # the key provided to the algorithm.


class FileChecksum():
    def __init__(self):
        # self.d= []
        # for i in range(256):
        #    self.d.append(int(0))
        self.d = array.array("L", [0] * 256)

    def get_file_checksum(self, filename):
        data = open(filename, "rb").read()
        key = -1
        i = 0
        while i < len(data):
            index = self.d[(key & 255) ^ ord(data[i])]
            key = (key >> 8) ^ index
            i += 1
        return ~key

    def generate_4(self, offset, key):
        self.d[offset] = key
        self.d[offset+1] = key ^ G4_MODIFIER
        key ^= (G4_MODIFIER << 1)
        self.d[offset+2] = key
        self.d[offset+3] = key ^ G4_MODIFIER

    def generate_16(self, offset, key):
        self.generate_4(offset, key)
        self.generate_4(offset + 4, key ^ G16_MODIFIER)
        key ^= (G16_MODIFIER << 1)
        self.generate_4(offset + 8, key)
        self.generate_4(offset + 12, key ^ G16_MODIFIER)

    def generate_64(self, offset, key):
        self.generate_16(offset, key)
        self.generate_16(offset + 16, key ^ G64_MODIFIER)
        key ^= (G64_MODIFIER << 1)
        self.generate_16(offset + 32, key)
        self.generate_16(offset + 48, key ^ G64_MODIFIER)

    def generate_checksum_array(self, key):
        self.generate_64(0, key)
        self.generate_64(64, key ^ G256_MODIFIER)
        key ^= (G256_MODIFIER << 1)
        self.generate_64(128, key)
        self.generate_64(192, key ^ G256_MODIFIER)

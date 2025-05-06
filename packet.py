import struct
import zlib

class Packet:
    HEADER_FORMAT = "!HBI"  # seq (2 bytes), type (1 byte), checksum (4 bytes)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, seq=0, pkt_type=0, data=b""):
        self.seq = seq
        self.pkt_type = pkt_type
        self.data = data
        self.checksum = self.calculate_checksum()

    def calculate_checksum(self):
        return zlib.crc32(self.data) & 0xFFFFFFFF

    def to_bytes(self):
        header = struct.pack(self.HEADER_FORMAT, self.seq, self.pkt_type, self.checksum)
        return header + self.data

    @classmethod
    def from_bytes(cls, packet_bytes):
        header = packet_bytes[:cls.HEADER_SIZE]
        data = packet_bytes[cls.HEADER_SIZE:]
        seq, pkt_type, checksum = struct.unpack(cls.HEADER_FORMAT, header)
        packet = cls(seq, pkt_type, data)
        if packet.checksum != checksum:
            raise ValueError("Checksum inválido.")
        return packet
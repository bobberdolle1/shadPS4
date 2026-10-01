import struct

# Word 1: 13030 = 0x32E6
# Word 2: 23767 = 0x5CD7
dw = 13030 | (23767 << 16)
print(f"DWORD = 0x{dw:08x}")

# 8:8:8:8
b0 = dw & 0xff
b1 = (dw >> 8) & 0xff
b2 = (dw >> 16) & 0xff
b3 = (dw >> 24) & 0xff
print(f"Bytes: {b0} (0x{b0:02x}), {b1} (0x{b1:02x}), {b2} (0x{b2:02x}), {b3} (0x{b3:02x})")

# Unorm8
print(f"Unorm8: {b0/255.0:.4f}, {b1/255.0:.4f}, {b2/255.0:.4f}, {b3/255.0:.4f}")

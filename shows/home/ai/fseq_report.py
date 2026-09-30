#!/usr/bin/env python3
"""Print per-prop mean brightness over time from a rendered .fseq (v2, zstd).
usage: fseq_report.py <file.fseq>   (needs: pip install zstandard numpy)"""
import struct, sys, zstandard, numpy as np
d = open(sys.argv[1], 'rb').read()
off = struct.unpack('<H', d[4:6])[0]; chans = struct.unpack('<I', d[10:14])[0]; frames = struct.unpack('<I', d[14:18])[0]
step = d[18]; nblocks = ((d[20] >> 4) << 8) | d[21]; nsparse = d[22]; p = 32; blocks = []
for i in range(nblocks):
    blocks.append(struct.unpack('<II', d[p:p + 8])); p += 8
sparse = []
for i in range(nsparse):
    sparse.append((int.from_bytes(d[p:p + 3], 'little'), int.from_bytes(d[p + 3:p + 6], 'little'))); p += 6
if not sparse:
    sparse = [(0, chans)]
dctx = zstandard.ZstdDecompressor(); out = bytearray(); q = off
for fr, ln in blocks:
    if ln:
        out += dctx.decompress(d[q:q + ln], max_output_size=chans * 512); q += ln
a = np.frombuffer(bytes(out), dtype=np.uint8)[:frames * chans].reshape(frames, chans)
def col(absch):
    c = absch - 1; base = 0
    for s, n in sparse:
        if s <= c < s + n:
            return base + (c - s)
        base += n
    return None
# absolute 1-based channel ranges for this show (from xlights_rgbeffects.xml / xlights_networks.xml)
PROPS = {'Tree': (1, 7200), 'Icicles EveL+Rail': (8161, 9960), 'Icicles EveR': (9961, 10860), 'Matrix UL': (10861, 12180),
         'Matrix UR': (12181, 13500), 'Win Upper R': (13501, 13896), 'Win Upper L': (13897, 14292), 'Win Porch R': (15301, 15696),
         'Canes': (15811, 16530), 'Matrix Bay': (16531, 21930), 'Win Bay': (21931, 22560)}
fps = 1000 // step; sec = frames // fps
print(f'{frames} frames @ {step} ms; mean brightness (0-255) per 10 s, columns start at 0 s')
for n, (a1, b1) in PROPS.items():
    c1, c2 = col(a1), col(b1)
    if c1 is None or c2 is None:
        print(f'{n:18s} (not in file)'); continue
    m = a[:sec * fps, c1:c2 + 1].reshape(sec, fps, -1).mean(axis=(1, 2))
    print(f'{n:18s}', ' '.join(f'{int(v):3d}' for v in m[::10]))

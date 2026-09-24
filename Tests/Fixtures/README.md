These are tiny synthetic fixtures created for this repository, with no external
image assets. They are covered by the repository license. cwebp and webpmux 1.6.0
produced them; `python3 Tests/RegenerateFixtures.py` reproduces the source pixels
and encodings (requires those two 1.6.0 tools on PATH).

- `lossless.webp`: exact 2×2 RGBA pixels: opaque red, half-transparent green
  (alpha 128), opaque blue, and transparent white. Encoding retains invisible RGB.
- `lossy.webp`: 4×4 opaque black, quality 90. RGB decode tolerance is three levels.
- `animation.webp`: two opaque 2×2 lossless frames, red then green, durations
  40 and 60 ms, no blending, loop count three. EXIF is a minimal little-endian
  TIFF with zero directory entries, prefixed by `Exif\0\0`.

`ImportDecoder.swift` embeds the same `lossless.webp` bytes so a SwiftPM consumer
needs no resource loading. Regeneration refreshes that array too.

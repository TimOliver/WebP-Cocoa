Run `python3 scripts/test-artifacts.py` after building all XCFrameworks. For a
macOS-only development build, use `--slices macos`. `--dist PATH` selects another
XCFramework directory and `--package PATH` selects the matching local SwiftPM
package, so the same tests can consume downloaded release assets. `--skip-swiftpm`
is a development-only shortcut; release CI must run the SwiftPM consumer.

The runner checks each product's XCFramework platform/variant declarations,
exact architecture lists, static archive signatures, Mach-O build platform and
deployment minimum, symbol separation (including decoder-only purity and bundled
SharpYUV), absence of embedded bitcode, headers and module maps. It compiles **and links**
C upstream-style includes, Objective-C modules, and Swift imports for every
advertised platform/architecture, for both the decoder+demux and full+demux+mux
library combinations. This includes the historical `WebP.Decoder` module and
standalone `WebP`/`WebPDecoder` imports with no other library's headers available.

Native macOS tests exercise lossless pixels (including alpha/invisible RGB),
lossy pixels, buffer decoding, incremental decoding, malformed/truncated input,
animated frame iteration, animation timestamps/pixels/reset and EXIF extraction.
The full library additionally runs a lossless encode/decode round trip, XMP
mux/demux and lossy encoding with `use_sharp_yuv=1`. Four actual SwiftPM executable
consumers build and run against `WebPImageIO`, `WebPFull`, `WebPDecoder` and `WebP`
products.

Mobile, simulator and Catalyst binaries are cross-linked, not executed by this
runner. Native runtime tests run on the current host architecture; the other
macOS architecture is cross-linked. No simulator installation or device boot is
required. All outputs and compiler/SwiftPM caches remain under `build/tests/`;
failed runs are retained for inspection. The synthetic fixtures and reproduction
instructions are documented in [Fixtures/README.md](Fixtures/README.md).

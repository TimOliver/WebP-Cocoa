This is a real iOS application project with two shared schemes:

- `DecodingSmoke` consumes the SwiftPM `WebPDecoding` product and imports
  `WebPDecoder` and `WebPDemux` together.
- `FullSmoke` consumes `WebPFull` and imports `WebP`, the legacy `WebP.Decoder`
  submodule, `WebPDemux` and `WebPMux` together.

Run `python3 scripts/test-xcode-consumer.py` from the repository after building the
XCFrameworks. Use `--package PATH` for an extracted release package or a checkout
whose `Package.swift` uses the published binary URLs and checksums. The runner
copies this fixture into `build/tests/`, substitutes the package location and
builds both schemes for generic iOS devices and simulators with signing disabled.
Xcode, through SwiftPM, selects and stages the XCFrameworks. The project supplies
no manual header, module or framework search paths.

The runner checks that each expected XCFramework went through Xcode's
`ProcessXCFramework` build step and that app binaries contain all advertised iOS
architectures. Build logs and result bundles are retained under `build/tests/`.
This catches duplicate staged header/module-map output paths that command-line
`swift build` cannot detect. App code calls decode/demux and, for the full product,
encode/mux functions so imports and linking must work. CI does not launch these
apps; runtime decoding is covered by the native macOS artifact tests.

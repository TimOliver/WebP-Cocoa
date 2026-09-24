<p align="center">
    <img src="https://github.com/TimOliver/WebP-Cocoa/raw/main/banner.png" width="731" alt="WebP-Cocoa Banner" />
</p>

# WebP-Cocoa

Static [libwebp](https://chromium.googlesource.com/webm/libwebp/) XCFrameworks for Apple platforms, built directly from upstream CMake with Ninja. SwiftPM packages and manual downloads use the same checksummed GitHub Release archives.

The source and toolchain are pinned in [toolchain.json](toolchain.json): libwebp **1.6.0**, Xcode **26.3 (17C529)** with Apple **26.2 SDKs**, CMake **4.1.1**, Ninja **1.13.2**, and CI Python **3.13.7**. The official source archive and downloaded build tools are SHA-256 verified before use. No Autotools, Fastlane, Ruby, Homebrew installation, or bitcode is required.

## Products and compatibility

| SwiftPM product | Binary modules | Use |
| --- | --- | --- |
| **WebPDecoding** | `WebPDecoder`, `WebPDemux` | Decode pixels, inspect metadata, enumerate frames, and decode animations |
| **WebPFull** | `WebP`, `WebPDemux`, `WebPMux` | Decode, encode, demux, and mux |
| `WebPDecoder` | `WebPDecoder` | Standalone decoder |
| `WebP` | `WebP` | Standalone encoder and decoder; includes its SharpYUV dependency |
| `WebPDemux` | `WebPDemux` | Advanced composition; also link **one** of `WebPDecoder` or `WebP` |
| `WebPMux` | `WebPMux` | Advanced composition; also link `WebP` for the full mux/animation API |

Choose either `WebPDecoding` or `WebPFull` for a complete dependency set. `WebP` and `WebPDecoder` contain overlapping decoder symbols; do not combine them or combine the two convenience products in one executable. Decoder/demux archives do not contain encoder or SharpYUV code. Binary targets cannot declare dependencies themselves, so convenience products group the required targets explicitly.

The four historical module names and `import WebP.Decoder` remain available. Upstream flat header includes and `<webp/decode.h>`-style includes are supported. The old `--enable-swap-16bit-csp` behavior is retained with `WEBP_ENABLE_SWAP_16BIT_CSP=ON`. This affects packed 16-bit output; RGBA output keeps its usual byte order.

## Platforms

| Platform | Minimum OS | Device/native architectures | Simulator architectures |
| --- | --- | --- | --- |
| iOS / iPadOS | 15.0 | arm64 | arm64, x86_64 |
| Mac Catalyst | 15.0 | arm64, x86_64 | — |
| macOS | 11.0 | arm64, x86_64 | — |
| tvOS | 15.0 | arm64 | arm64, x86_64 |
| watchOS | 8.0 (arm64 device: 26.0) | arm64, arm64_32 | arm64, x86_64 |
| visionOS | 1.0 | arm64 | arm64 |

Device, simulator, and Catalyst slices are separate XCFramework entries. `lipo` combines architectures only within a single platform/variant. Each of the four XCFrameworks contains all ten entries. watchOS includes arm64 for Apple's [2026 64-bit requirement](https://developer.apple.com/news/?id=zt8rydnt), while retaining arm64_32 for watchOS 8 and later. The watchOS arm64 device objects target watchOS 26 explicitly; simulator objects retain the watchOS 8 minimum. Both floors are recorded in the lockfile and build provenance.

The 2026 pipeline raises the old deployment targets and drops armv7, armv7s, armv7k, and i386. Projects requiring those architectures or older OS releases can continue using the existing [v1.2.2 release](https://github.com/TimOliver/WebP-Cocoa/releases/tag/v1.2.2). Those historical assets are unchanged. This is a deployment compatibility change; review the table before updating.

## Swift Package Manager

Use a **published release tag** from [GitHub Releases](https://github.com/TimOliver/WebP-Cocoa/releases). The first release produced by this pipeline is intended to be `1.6.0`; it is not published merely by checking in these scripts.

After that release is published:

```swift
// In your Package.swift:
dependencies: [
    .package(url: "https://github.com/TimOliver/WebP-Cocoa.git", exact: "1.6.0")
],
targets: [
    .target(name: "YourImageTarget", dependencies: [
        .product(name: "WebPDecoding", package: "WebP-Cocoa")
    ])
]
```

```swift
import WebPDecoder
import WebPDemux
```

Release commits contain remote `.binaryTarget` URLs with checksums computed from the actual uploaded ZIPs. The `main` branch uses local `dist/*.xcframework` paths for development; build the artifacts before adding a local package. Do not use `main` as a remote binary dependency.

For manual installation, download and extract the required `NAME.xcframework.zip` archives from a release. Add both `WebPDecoder.xcframework` and `WebPDemux.xcframework` for decoding/animation, or `WebP.xcframework`, `WebPDemux.xcframework`, and `WebPMux.xcframework` for the full API. Select **Do Not Embed**: the archives are static. Keep the included `Licenses` directory with your redistribution notices.

The previous per-platform ZIP names and `Carthage.zip` are replaced by four universal XCFramework ZIPs. Each archive has its XCFramework at the ZIP root, as SwiftPM requires. No CocoaPods or Carthage specification is added; the separate [SDWebImage/libwebp-Xcode](https://github.com/SDWebImage/libwebp-Xcode) project remains an option for those dependency managers.

## Build and test locally

Install full Xcode with all SDKs in the table. Select the pinned release of Xcode, then install the pinned CMake/Ninja binaries into this checkout:

```sh
export DEVELOPER_DIR=/Applications/Xcode_26.3.app/Contents/Developer
bash scripts/bootstrap-tools.sh
export PATH="$PWD/build/tools/bin:$PATH"
./build.sh all
python3 scripts/test-artifacts.py
python3 -m unittest discover -s Tests -p 'test_*.py'
```

Python 3.10 or newer is sufficient for local orchestration. CI and release packaging require the pinned Python version. The build checks Xcode's build number, every selected SDK version, CMake, and Ninja. To validate a different local toolchain explicitly:

```sh
./build.sh macos --allow-toolchain-mismatch
python3 scripts/test-artifacts.py --slices macos
```

Such builds are marked in `dist/build-info.json` and cannot be packaged as releases. A partial build replaces the XCFrameworks in `dist` with only the requested slices; run `all` again before packaging. `./build.sh ios` includes device, simulator, and Catalyst. Other selectors are `macos`, `catalyst`, `tvos`, `watchos`, and `visionos`; `--slices` accepts comma-separated individual slice names from [scripts/config.py](scripts/config.py). Paths resolve relative to the repository, regardless of the caller's working directory.

Source downloads and build logs live in `build/`; outputs live in `dist/`. Each configure uses a fresh per-architecture CMake cache to avoid stale SIMD and platform checks. The build uses upstream `webpdecoder`, `webpdemux`, `webp`, and `libwebpmux` targets. It merges SharpYUV only into `WebP`, since CMake's static target dependencies are not physically included in `libwebp.a`.

Automated validation covers XCFramework platform/architecture metadata, static archive contents, public headers, C/Objective-C and Swift imports, `WebP.Decoder` compatibility, and executable links for every advertised architecture. Host macOS tests decode known lossy/lossless pixels, reject malformed data, extract metadata, iterate animation frames, exercise animation decoding, and check full-codec encoding and muxing. SwiftPM consumers import and link the actual binary products. Cross-platform link tests do not claim on-device runtime coverage.

## Release process

The **Build and release libwebp** workflow runs builds and validation on pull requests and pushes. Its manually dispatched release path accepts the pinned SemVer version and uses the repository's scoped `GITHUB_TOKEN`; no personal token or Fastlane secrets are required. Actions are pinned to immutable commits. The runner family is explicit; hosted images can still change, so exact compiler/SDK checks fail if the pinned Xcode is removed.

The workflow builds all platforms, runs tests, creates the four ZIPs, and computes `SHA256SUMS` plus a remote `Package.swift`. It creates a release commit containing that manifest and pushes a unique `candidate-…` tag pointing at that exact commit, without changing `main`. This candidate tag is not a SwiftPM version. Existing tags/assets are never overwritten.

Release assets are uploaded to a candidate draft, downloaded again, checksum verified, extracted, and tested as local SwiftPM binaries before publication. Draft assets require authentication, so this validation checks the downloaded bytes. With the publish input enabled, GitHub promotes the draft and creates the final SemVer tag at the release commit. The workflow verifies the tag's commit and tests public SwiftPM URLs. A failure at that last step leaves the published release in place for investigation. The candidate tag is retained for provenance.

With publishing disabled, there is no public SemVer tag pointing at private assets. To promote a tested draft later, first confirm the final version tag does not exist, then use the candidate tag and commit SHA printed by the workflow:

```sh
gh release edit CANDIDATE_TAG --repo TimOliver/WebP-Cocoa \
  --tag 1.6.0 --target CANDIDATE_COMMIT_SHA --draft=false
```

Do not simply publish the candidate under its temporary tag: the generated manifest URLs refer to the final version. The workflow's publish option performs this promotion and the subsequent public consumer test automatically.

For local release preparation on the exact toolchain:

```sh
python3 scripts/distribution.py package --tag 1.6.0
# Review dist/release/Package.swift, SHA256SUMS, and build-info.json.
python3 scripts/distribution.py verify --directory dist/release --tag 1.6.0
```

Packaging refuses incomplete architecture sets, development toolchain overrides, missing license files, or an existing `dist/release` directory. ZIP ordering, timestamps, and permissions are normalized; compiler/tool versions and flags are recorded in provenance. This does not promise bit-for-bit compiler output across different macOS hosts.

To update libwebp, change its version, official archive URL and verified checksum in `toolchain.json`, inspect the upstream CMake targets and dependencies, and run the complete validation before releasing. Update the bootstrap tool hashes together with any CMake/Ninja pins. Use a new release version for changed binary bytes; never replace an existing release archive.

## License and credits

Build/distribution code is [BSD-3-Clause](LICENSE). Every XCFramework includes libwebp's `COPYING`, `PATENTS`, and `AUTHORS`, plus this repository's license. Repository created by [Tim Oliver](https://timoliver.com.au/). WebP is developed by Google. Banner artwork by [Simo99](https://commons.wikimedia.org/wiki/User:Simo99) is used under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).

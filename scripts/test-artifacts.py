#!/usr/bin/env python3
"""Validate the shipped archives, Apple imports/linking, decoding and SwiftPM.

No source build is used here: every compile/link consumes only XCFramework
headers and archives. Select --slices for a development build; release CI uses
all configured slices and architectures. Temporary outputs/caches stay in build/.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

from config import BUILD, DIST, LOCK, PRODUCTS, ROOT, SLICES, deployment, triple

TESTS = ROOT / "Tests"
PLATFORMS = {
    "macos": {"1", "MACOS"}, "ios": {"2", "IOS"},
    "tvos": {"3", "TVOS"}, "watchos": {"4", "WATCHOS"},
    "catalyst": {"6", "MACCATALYST"},
    "ios-simulator": {"7", "IOSSIMULATOR"},
    "tvos-simulator": {"8", "TVOSSIMULATOR"},
    "watchos-simulator": {"9", "WATCHOSSIMULATOR"},
    "visionos": {"11", "XROS", "VISIONOS"},
    "visionos-simulator": {"12", "XROSSIMULATOR", "VISIONOSSIMULATOR"},
}
EXPECTED_VERSION = sum(int(number) << shift for number, shift in
                       zip(LOCK["libwebp"]["version"].split("."), (16, 8, 0)))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run(command, *, env=None, capture=False, cwd=None):
    command = [str(argument) for argument in command]
    print("+ " + shlex.join(command), flush=True)
    result = subprocess.run(command, env=env, cwd=cwd, text=True,
                            stdout=subprocess.PIPE if capture else None,
                            stderr=subprocess.PIPE if capture else None)
    if result.returncode:
        if capture:
            print(result.stdout, end="", file=sys.stderr)
            print(result.stderr, end="", file=sys.stderr)
        raise RuntimeError(f"command exited {result.returncode}: {shlex.join(command)}")
    return result.stdout.strip() if capture else ""


def version_tuple(version):
    parts = tuple(int(part) for part in version.split("."))
    return parts + (0,) * (3 - len(parts))


def validate_symbols(product, archive, label):
    output = run(["xcrun", "nm", "-gUj", archive], capture=True)
    symbols = {line.strip() for line in output.splitlines() if line.startswith("_")}
    required = {
        "WebP": {"_WebPDecodeRGBA", "_WebPEncode", "_WebPGetEncoderVersion", "_SharpYuvConvert"},
        "WebPDecoder": {"_WebPDecodeRGBA", "_WebPGetDecoderVersion"},
        "WebPDemux": {"_WebPDemuxInternal", "_WebPAnimDecoderNewInternal", "_WebPGetDemuxVersion"},
        "WebPMux": {"_WebPNewInternal", "_WebPAnimEncoderNewInternal", "_WebPGetMuxVersion"},
    }[product]
    require(required.issubset(symbols), f"{label}: missing definitions: {sorted(required - symbols)}")
    forbidden = []
    if product == "WebPDecoder":
        forbidden = ["_WebPEncode", "_WebPGetEncoder", "_WebPPicture", "_WebPConfig",
                     "_WebPValidateConfig", "_WebPMemoryWriter", "_SharpYuv"]
    elif product in ("WebPDemux", "WebPMux"):
        forbidden = ["_WebPDecode", "_WebPGetDecoder", "_WebPEncode", "_WebPGetEncoder",
                     "_SharpYuv", "_VP8"]
    leaked = sorted(symbol for symbol in symbols if any(symbol.startswith(prefix) for prefix in forbidden))
    require(not leaked, f"{label}: unexpected codec/encoder definitions: {leaked}")


def artifact_slices(dist, selected, work):
    result = {}
    for product, specification in PRODUCTS.items():
        bundle = dist / f"{product}.xcframework"
        with (bundle / "Info.plist").open("rb") as file:
            info = plistlib.load(file)
        entries = info.get("AvailableLibraries", [])
        keys = [(entry["SupportedPlatform"], entry.get("SupportedPlatformVariant", ""))
                for entry in entries]
        require(len(set(keys)) == len(keys), f"{product}: duplicate platform slices")
        expected_keys = {(SLICES[name]["platform"], SLICES[name].get("variant", ""))
                         for name in selected}
        require(expected_keys.issubset(set(keys)), f"{product}: missing selected platform slices")
        if set(selected) == set(SLICES):
            require(set(keys) == expected_keys, f"{product}: unadvertised or missing slices: {keys}")
        for name in selected:
            expected = SLICES[name]
            key = (expected["platform"], expected.get("variant", ""))
            entry = entries[keys.index(key)]
            require(set(entry["SupportedArchitectures"]) == set(expected["archs"]),
                    f"{product}/{name}: plist architecture mismatch")
            slice_root = bundle / entry["LibraryIdentifier"]
            # Xcode copies all raw-library HeadersPath contents into one include
            # directory. Named framework bundles keep products' duplicate
            # upstream header names and module maps in separate namespaces.
            require(entry["LibraryPath"] == f"{product}.framework",
                    f"{product}/{name}: expected a named static framework")
            require("HeadersPath" not in entry,
                    f"{product}/{name}: raw-library headers collide during Xcode staging")
            framework = slice_root / entry["LibraryPath"]
            library = framework / product
            headers = framework / "Headers"
            module_map = framework / "Modules" / "module.modulemap"
            require(module_map.is_file(), f"{product}/{name}: missing framework module map")
            require(f"framework module {product} [system]" in module_map.read_text(),
                    f"{product}/{name}: expected framework module declaration")
            require(not (headers / "module.modulemap").exists(),
                    f"{product}/{name}: module map belongs in framework Modules")
            with (framework / "Info.plist").open("rb") as file:
                framework_info = plistlib.load(file)
            require(framework_info.get("CFBundleExecutable") == product and
                    framework_info.get("CFBundleName") == product and
                    framework_info.get("CFBundlePackageType") == "FMWK",
                    f"{product}/{name}: invalid framework bundle metadata")
            for header in specification["headers"]:
                require((headers / header).is_file(), f"{product}/{name}: missing {header}")
                require((headers / "webp" / header).is_file(),
                        f"{product}/{name}: missing webp/{header} include compatibility")
            actual = run(["xcrun", "lipo", "-archs", library], capture=True).split()
            require(set(actual) == set(expected["archs"]),
                    f"{product}/{name}: archive architectures {actual}, expected {expected['archs']}")
            for arch in expected["archs"]:
                thin = library
                if len(actual) > 1:
                    thin = work / f"{product}-{name}-{arch}.a"
                    run(["xcrun", "lipo", library, "-thin", arch, "-output", thin])
                with thin.open("rb") as file:
                    require(file.read(8) == b"!<arch>\n", f"{product}/{name}/{arch}: not a static archive")
                commands = run(["xcrun", "otool", "-l", "-arch", arch, library], capture=True)
                platforms = re.findall(r"\bplatform\s+(\w+)", commands)
                require(platforms and set(platforms).issubset(PLATFORMS[name]),
                        f"{product}/{name}/{arch}: object platform mismatch: {set(platforms)}")
                minimums = re.findall(r"\bminos\s+([0-9.]+)", commands)
                require(minimums and len(minimums) == len(platforms),
                        f"{product}/{name}/{arch}: missing LC_BUILD_VERSION deployment metadata")
                declared_minimum = deployment(name, arch)
                too_new = {value for value in minimums if version_tuple(value) > version_tuple(declared_minimum)}
                require(not too_new,
                        f"{product}/{name}/{arch}: object minimum {sorted(too_new)} exceeds advertised {declared_minimum}")
                require("__LLVM" not in commands, f"{product}/{name}/{arch}: obsolete embedded bitcode")
                validate_symbols(product, thin, f"{product}/{name}/{arch}")
            result[product, name] = (headers, library)
    return result


def options(artifacts, name, flavor):
    # Do not link libwebp and libwebpdecoder into the same image: both define the
    # decoder API. Demux links to the selected implementation in either flavor.
    products = ["WebPDecoder", "WebPDemux"] if flavor == "Decoder" else ["WebP", "WebPDemux", "WebPMux"]
    headers = [artifacts[product, name][0] for product in products]
    libraries = [artifacts[product, name][1] for product in products]
    return headers, libraries


def compile_slices(artifacts, selected, work, env):
    host = platform.machine()
    require(host in ("arm64", "x86_64"), f"unsupported macOS test host: {host}")
    for name in selected:
        sdk = run(["xcrun", "--sdk", SLICES[name]["sdk"], "--show-sdk-path"], capture=True)
        for arch in SLICES[name]["archs"]:
            destination = work / f"{name}-{arch}"
            destination.mkdir()
            target = triple(name, arch)
            for flavor in ("Decoder", "Full"):
                headers, libraries = options(artifacts, name, flavor)
                frameworks = [argument for header in headers for argument in ("-F", header.parent.parent)]
                includes = [argument for header in headers for argument in ("-I", header)]
                common = ["xcrun", "clang", "-target", target, "-isysroot", sdk,
                          "-Wall", "-Wextra", "-Werror"]
                objc = destination / f"import-{flavor}"
                run([*common, *frameworks, "-fmodules", f"-fmodules-cache-path={work / 'clang-cache'}",
                     TESTS / f"Import{flavor}.m", *libraries, "-o", objc], env=env)
                c = destination / f"headers-{flavor}"
                run([*common, *includes, f"-DWEBP_FULL={int(flavor == 'Full')}", TESTS / "Headers.c",
                     *libraries, "-o", c], env=env)
                swift = destination / f"swift-{flavor}"
                run(["xcrun", "--sdk", SLICES[name]["sdk"], "swiftc", "-target", target, "-sdk", sdk,
                     "-module-cache-path", work / "swift-cache", *frameworks,
                     TESTS / f"Import{flavor}.swift", *libraries, "-o", swift], env=env)
                if name == "macos" and arch == host:
                    for executable in (objc, c, swift):
                        run([executable], env=env)
            # Prove the primary binary products also import with only their own
            # framework search path; the combined consumers must not mask a missing
            # standalone header or module dependency.
            for product in ("WebPDecoder", "WebP"):
                headers, library = artifacts[product, name]
                decoder = product == "WebPDecoder"
                objc = destination / f"standalone-objc-{product}"
                run(["xcrun", "clang", "-target", target, "-isysroot", sdk,
                     "-Wall", "-Wextra", "-Werror", "-F", headers.parent.parent, "-fmodules",
                     f"-fmodules-cache-path={work / 'clang-cache'}",
                     f"-DWEBP_DECODER_ONLY={int(decoder)}", TESTS / "ImportStandalone.m",
                     library, "-o", objc], env=env)
                swift = destination / f"standalone-swift-{product}"
                defines = ["-D", "WEBP_DECODER_ONLY"] if decoder else []
                run(["xcrun", "--sdk", SLICES[name]["sdk"], "swiftc", "-target", target, "-sdk", sdk,
                     "-module-cache-path", work / "swift-cache", "-F", headers.parent.parent,
                     *defines, TESTS / "ImportStandalone.swift", library, "-o", swift], env=env)
                if name == "macos" and arch == host:
                    run([objc], env=env)
                    run([swift], env=env)
            if name == "macos" and arch == host:
                for source, flavor in (("Decode.c", "Decoder"), ("Decode.c", "Full"), ("EncodeMux.c", "Full")):
                    headers, libraries = options(artifacts, name, flavor)
                    includes = [argument for header in headers for argument in ("-I", header)]
                    executable = destination / f"{Path(source).stem}-{flavor}"
                    run(["xcrun", "clang", "-target", target, "-isysroot", sdk,
                         "-Wall", "-Wextra", "-Werror", "-std=c11",
                         f"-DEXPECTED_WEBP_VERSION={EXPECTED_VERSION}", *includes,
                         TESTS / source, *libraries, "-o", executable], env=env)
                    arguments = [TESTS / "Fixtures"] if source == "Decode.c" else []
                    run([executable, *arguments], env=env)
            print(f"PASS: {name}/{arch} Objective-C modules, C headers and Swift import/link", flush=True)


def swiftpm_consumer(package, work, env):
    require((package / "Package.swift").is_file(), f"missing package manifest: {package}")
    consumer = work / "consumer"
    consumer.mkdir()
    # Named local dependency avoids relying on checkout-directory identity.
    manifest = '''// swift-tools-version: 5.9
import PackageDescription
let package = Package(
    name: "WebPArtifactConsumer",
    platforms: [.macOS(.v11)],
    dependencies: [.package(name: "WebPCocoa", path: PACKAGE_PATH)],
    targets: [
        .executableTarget(name: "DecodingSmoke", dependencies: [
            .product(name: "WebPDecoding", package: "WebPCocoa")]),
        .executableTarget(name: "FullSmoke", dependencies: [
            .product(name: "WebPFull", package: "WebPCocoa")]),
        .executableTarget(name: "DecoderOnlySmoke", dependencies: [
            .product(name: "WebPDecoder", package: "WebPCocoa")],
            swiftSettings: [.define("WEBP_DECODER_ONLY")]),
        .executableTarget(name: "WebPOnlySmoke", dependencies: [
            .product(name: "WebP", package: "WebPCocoa")])
    ])
'''.replace("PACKAGE_PATH", json.dumps(str(package)))
    (consumer / "Package.swift").write_text(manifest)
    targets = (("DecodingSmoke", "ImportDecoder.swift"), ("FullSmoke", "ImportFull.swift"),
               ("DecoderOnlySmoke", "ImportStandalone.swift"), ("WebPOnlySmoke", "ImportStandalone.swift"))
    for name, source in targets:
        target = consumer / "Sources" / name
        target.mkdir(parents=True)
        shutil.copy2(TESTS / source, target / "main.swift")
    for name, _ in targets:
        run(["xcrun", "swift", "run", "--package-path", consumer,
             "--scratch-path", consumer / ".build", "--cache-path", work / "spm-cache",
             "--config-path", work / "spm-config", "--security-path", work / "spm-security",
             "--manifest-cache", "local", "--disable-sandbox", "-c", "release", name], env=env)
    print("PASS: real SwiftPM WebPDecoding/WebPFull and standalone WebPDecoder/WebP consumers", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slices", default=",".join(SLICES), help="comma-separated slice names (default: all)")
    parser.add_argument("--dist", type=Path, default=DIST, help="XCFramework directory")
    parser.add_argument("--package", type=Path, default=ROOT, help="SwiftPM package directory consumed by smoke test")
    parser.add_argument("--skip-swiftpm", action="store_true", help="skip host SwiftPM consumer during development")
    args = parser.parse_args()
    selected = list(dict.fromkeys(args.slices.split(",")))
    unknown = set(selected) - set(SLICES)
    require(not unknown, f"unknown slices: {sorted(unknown)}")
    require(sys.platform == "darwin", "Apple artifact tests require macOS with Xcode selected")
    test_root = BUILD / "tests"
    test_root.mkdir(parents=True, exist_ok=True)
    # Keep failure products available for diagnosis, too.
    work = Path(tempfile.mkdtemp(prefix="artifacts-", dir=test_root))
    print(f"Test outputs and compiler caches: {work}", flush=True)
    env = dict(os.environ)
    env.update({"CLANG_MODULE_CACHE_PATH": str(work / "clang-cache"),
                "SWIFTPM_MODULECACHE_OVERRIDE": str(work / "spm-module-cache"),
                "SWIFT_MODULECACHE_PATH": str(work / "swift-cache")})
    artifacts = artifact_slices(args.dist.resolve(), selected, work)
    compile_slices(artifacts, selected, work, env)
    if "macos" in selected and not args.skip_swiftpm:
        swiftpm_consumer(args.package.resolve(), work, env)
    print(f"PASS: {len(selected)} platform slices; all advertised architectures validated", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, KeyError, ValueError) as error:
        raise SystemExit(f"Artifact validation failed: {error}")

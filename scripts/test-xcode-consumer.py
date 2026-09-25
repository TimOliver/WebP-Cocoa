#!/usr/bin/env python3
"""Build real iOS app consumers through Xcode's SwiftPM/XCFramework staging.

Run after building all XCFrameworks. --package may select an extracted release
package or a checkout whose manifest downloads immutable release assets. Nothing
adds headers, modules or archives to Xcode's search paths manually. No signing,
simulator installation or simulator boot is required.
"""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

from config import BUILD, ROOT, SLICES


CONSUMERS = {
    "DecodingSmoke": ("WebPDecoder", "WebPDemux"),
    "FullSmoke": ("WebP", "WebPDemux", "WebPMux"),
}
DESTINATIONS = {
    "ios": ("generic/platform=iOS", "iphoneos"),
    "ios-simulator": ("generic/platform=iOS Simulator", "iphonesimulator"),
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def build_consumer(project, scheme, platform, work, env):
    destination, sdk = DESTINATIONS[platform]
    label = f"{scheme}-{platform}"
    derived = work / label
    log = work / f"{label}.log"
    command = [
        "xcodebuild", "build", "-project", str(project), "-scheme", scheme,
        "-configuration", "Debug", "-destination", destination,
        "-derivedDataPath", str(derived),
        "-clonedSourcePackagesDirPath", str(work / "SourcePackages"),
        "-packageCachePath", str(work / "package-cache"),
        "-resultBundlePath", str(work / f"{label}.xcresult"),
        "CODE_SIGNING_ALLOWED=NO", "CODE_SIGNING_REQUIRED=NO",
        "ONLY_ACTIVE_ARCH=NO", "ARCHS=" + " ".join(SLICES[platform]["archs"]),
        "COMPILER_INDEX_STORE_ENABLE=NO",
        "CLANG_MODULE_CACHE_PATH=" + str(work / "clang-cache"),
    ]
    print("+ " + shlex.join(command), flush=True)
    print(f"Xcode build log: {log}", flush=True)
    with log.open("w") as stream:
        result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                stdout=stream, stderr=subprocess.STDOUT)
    output = log.read_text(errors="replace")
    if result.returncode:
        print("\n".join(output.splitlines()[-100:]), file=sys.stderr)
        raise RuntimeError(f"{label}: xcodebuild exited {result.returncode}; see {log}")
    require("** BUILD SUCCEEDED **" in output, f"{label}: missing build success in {log}")
    for product in CONSUMERS[scheme]:
        require(any(line.startswith("ProcessXCFramework ") and f"/{product}.xcframework " in line
                    for line in output.splitlines()),
                f"{label}: Xcode did not process {product}.xcframework; see {log}")
    app = derived / "Build" / "Products" / f"Debug-{sdk}" / f"{scheme}.app" / scheme
    require(app.is_file(), f"{label}: missing linked iOS application {app}")
    architectures = subprocess.check_output(["xcrun", "lipo", "-archs", str(app)], text=True).split()
    require(set(architectures) == set(SLICES[platform]["archs"]),
            f"{label}: app architectures {architectures}, expected {SLICES[platform]['archs']}")
    print(f"PASS: {label} SwiftPM staging, imports and app link ({', '.join(architectures)})", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=ROOT,
                        help="Swift package with local or released binary targets (default: repository)")
    args = parser.parse_args()
    package = args.package.resolve()
    require((package / "Package.swift").is_file(), f"missing package manifest: {package}")
    (BUILD / "tests").mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="xcode-consumer-", dir=BUILD / "tests"))
    print(f"Xcode consumer outputs: {work}", flush=True)
    consumer = work / "consumer"
    shutil.copytree(ROOT / "Tests" / "XcodeConsumer", consumer)
    project = consumer / "XcodeConsumer.xcodeproj"
    pbxproj = project / "project.pbxproj"
    template = pbxproj.read_text()
    require(template.count('relativePath = "../..";') == 1,
            "Xcode project must have exactly one local package reference")
    pbxproj.write_text(template.replace('relativePath = "../..";',
                                       f"relativePath = {json.dumps(str(package))};"))
    env = os.environ.copy()
    (work / "user-home").mkdir()
    env["CFFIXED_USER_HOME"] = str(work / "user-home")
    env["SWIFTPM_MODULECACHE_OVERRIDE"] = str(work / "swift-cache")
    env["SWIFT_MODULECACHE_PATH"] = str(work / "swift-cache")
    env["XDG_CACHE_HOME"] = str(work / "cache")
    for scheme in CONSUMERS:
        for platform in DESTINATIONS:
            build_consumer(project, scheme, platform, work, env)
    print("PASS: both SwiftPM products built as iOS device and simulator apps", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)

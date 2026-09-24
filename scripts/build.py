#!/usr/bin/env python3
"""Build pinned upstream libwebp with CMake/Ninja, then static XCFrameworks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
import tarfile

from config import BUILD, DIST, LOCK, PRODUCTS, ROOT, SLICES, deployment, triple


def run(args, *, log=None):
    args = [str(arg) for arg in args]
    env = os.environ.copy()
    for key in ("CFLAGS", "CPPFLAGS", "LDFLAGS", "CPATH", "LIBRARY_PATH", "SDKROOT",
                "MACOSX_DEPLOYMENT_TARGET", "IPHONEOS_DEPLOYMENT_TARGET",
                "TVOS_DEPLOYMENT_TARGET", "WATCHOS_DEPLOYMENT_TARGET", "XROS_DEPLOYMENT_TARGET"):
        env.pop(key, None)
    env["ZERO_AR_DATE"] = "1"
    if log is None:
        return subprocess.check_output(args, text=True, env=env).strip()
    with log.open("a") as stream:
        stream.write("$ " + shlex.join(args) + "\n")
        stream.flush()
        result = subprocess.run(args, stdout=stream, stderr=subprocess.STDOUT, env=env)
    if result.returncode:
        print("\n".join(log.read_text().splitlines()[-60:]), file=sys.stderr)
        raise RuntimeError(f"Command failed; full log: {log}")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_tools(selected, allow_mismatch):
    if platform.system() != "Darwin":
        raise RuntimeError("Apple XCFrameworks require macOS and full Xcode.")
    for executable in ("cmake", "ninja", "xcodebuild", "xcrun", "curl"):
        if not shutil.which(executable):
            raise RuntimeError(f"Missing {executable}; see README.md for pinned tools.")
    xcode = run(["xcodebuild", "-version"]).splitlines()
    actual = {
        "xcode": xcode[0].removeprefix("Xcode "),
        "xcode_build": xcode[1].removeprefix("Build version "),
        "cmake": run(["cmake", "--version"]).splitlines()[0].split()[-1],
        "ninja": run(["ninja", "--version"]),
        "python": platform.python_version(),
        "clang": run(["xcrun", "clang", "--version"]),
        "swift": run(["xcrun", "swift", "--version"]),
        "sdks": {},
    }
    # Python only orchestrates: pin it in CI, allow >=3.10 for local builds.
    mismatches = [f"{k}: expected {LOCK['tools'][k]}, found {actual[k]}"
                  for k in ("xcode", "xcode_build", "cmake", "ninja")
                  if actual[k] != LOCK["tools"][k]]
    for sdk in sorted({SLICES[name]["sdk"] for name in selected}):
        version = run(["xcrun", "--sdk", sdk, "--show-sdk-version"])
        actual["sdks"][sdk] = version
        if version != LOCK["tools"]["sdk"]:
            mismatches.append(f"{sdk}: expected {LOCK['tools']['sdk']}, found {version}")
    if mismatches:
        message = "Toolchain mismatch:\n" + "\n".join(mismatches)
        if not allow_mismatch:
            raise RuntimeError(message + "\nUse --allow-toolchain-mismatch for local validation only.")
        print(message, file=sys.stderr)
    actual["mismatches"] = mismatches
    return actual


def fetch_source():
    source = LOCK["libwebp"]
    downloads = BUILD / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = downloads / f"libwebp-{source['version']}.tar.gz"
    if not archive.exists():
        temporary = archive.with_suffix(".download")
        run(["curl", "--fail", "--location", "--retry", "3", "--proto", "=https",
             "--tlsv1.2", source["url"], "--output", temporary])
        if sha256(temporary) != source["sha256"]:
            temporary.unlink()
            raise RuntimeError("Downloaded source checksum does not match toolchain.json.")
        temporary.replace(archive)
    if sha256(archive) != source["sha256"]:
        raise RuntimeError(f"Source checksum mismatch: {archive}; remove it and retry.")
    destination = BUILD / "source"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir()
    with tarfile.open(archive) as bundle:
        for member in bundle.getmembers():
            path = Path(member.name)
            if path.is_absolute() or ".." in path.parts or not (member.isfile() or member.isdir()):
                raise RuntimeError(f"Unsafe source archive entry: {member.name}")
        bundle.extractall(destination)
    return destination / f"libwebp-{source['version']}"


def cmake_options(slice_name, arch, sdk):
    info = SLICES[slice_name]
    flags = [
        "-DCMAKE_BUILD_TYPE=Release", "-DBUILD_SHARED_LIBS=OFF", "-DWEBP_LINK_STATIC=ON",
        f"-DCMAKE_SYSTEM_NAME={info['system']}", f"-DCMAKE_SYSTEM_PROCESSOR={arch}",
        f"-DCMAKE_OSX_ARCHITECTURES={arch}", f"-DCMAKE_OSX_SYSROOT={sdk}",
        f"-DCMAKE_C_COMPILER={run(['xcrun', '--sdk', info['sdk'], '--find', 'clang'])}",
        f"-DCMAKE_C_COMPILER_TARGET={triple(slice_name, arch)}",
        "-DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY",
        f"-DCMAKE_MAKE_PROGRAM={shutil.which('ninja')}",
        "-DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=ONLY", "-DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=ONLY",
        "-DCMAKE_FIND_ROOT_PATH_MODE_PACKAGE=ONLY", "-DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER",
        "-DCMAKE_DISABLE_FIND_PACKAGE_OpenGL=ON", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "-DCMAKE_C_FLAGS_INIT=" + shlex.join([
            f"-ffile-prefix-map={ROOT}=.", f"-fdebug-prefix-map={ROOT}=."]),
        "-DWEBP_ENABLE_SIMD=ON", "-DWEBP_USE_THREAD=ON",
        # Preserve legacy packed 16-bit color output behavior.
        "-DWEBP_ENABLE_SWAP_16BIT_CSP=ON", "-DWEBP_BUILD_LIBWEBPMUX=ON",
    ]
    # Catalyst's ios*-macabi triple supplies its deployment target. Darwin's
    # deployment setting would incorrectly inject -mmacosx-version-min.
    flags.append("-DCMAKE_OSX_DEPLOYMENT_TARGET=" + ("" if slice_name == "catalyst" else deployment(slice_name, arch)))
    flags += [f"-DWEBP_BUILD_{option}=OFF" for option in (
        "ANIM_UTILS", "CWEBP", "DWEBP", "GIF2WEBP", "IMG2WEBP", "VWEBP",
        "WEBPINFO", "WEBPMUX", "EXTRAS", "WEBP_JS", "FUZZTEST")]
    return flags


def build_slice(source, slice_name, jobs):
    info = SLICES[slice_name]
    sdk = run(["xcrun", "--sdk", info["sdk"], "--show-sdk-path"])
    outputs = {name: [] for name in PRODUCTS}
    for arch in info["archs"]:
        print(f"Building {slice_name} / {arch}", flush=True)
        directory = BUILD / "cmake" / slice_name / arch
        # A fresh cache prevents stale platform/SIMD feature checks.
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True)
        log = BUILD / "logs" / f"{slice_name}-{arch}.log"
        log.write_text("")
        run(["cmake", "-S", source, "-B", directory, "-G", "Ninja",
             *cmake_options(slice_name, arch, sdk)], log=log)
        # Decoder/demux are unconditional upstream targets, not options.
        run(["cmake", "--build", directory, "--parallel", jobs, "--target",
             "webpdecoder", "webpdemux", "webp", "libwebpmux"], log=log)
        for name, product in PRODUCTS.items():
            archive = directory / f"lib{product['library']}.a"
            if name == "WebP":
                combined = directory / "libwebp-complete.a"
                run(["xcrun", "libtool", "-static", "-o", combined, archive,
                     directory / "libsharpyuv.a"], log=log)
                archive = combined
            if not archive.is_file():
                raise RuntimeError(f"Missing upstream output: {archive}")
            outputs[name].append(archive)
    for name, archives in outputs.items():
        directory = BUILD / "slices" / slice_name / name
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"lib{PRODUCTS[name]['library']}.a"
        if len(archives) == 1:
            shutil.copyfile(archives[0], target)
        else:
            run(["xcrun", "lipo", "-create", *archives, "-output", target])
        if set(run(["xcrun", "lipo", "-archs", target]).split()) != set(info["archs"]):
            raise RuntimeError(f"Unexpected architectures: {target}")


def stage_headers(source, name, product):
    headers = BUILD / "headers" / name
    if headers.exists():
        shutil.rmtree(headers)
    (headers / "webp").mkdir(parents=True)
    for header in product["headers"]:
        shutil.copyfile(source / "src" / "webp" / header, headers / header)
        (headers / "webp" / header).write_text(f'#include "../{header}"\n')
    if name == "WebP":
        module = ('module WebP [system] {\n  header "encode.h"\n  header "types.h"\n'
                  '  export *\n  module Decoder {\n    header "decode.h"\n    export *\n  }\n}\n')
    else:
        module = f"module {name} [system] {{\n"
        module += "".join(f'  header "{header}"\n' for header in product["headers"])
        module += "  export *\n}\n"
    (headers / "module.modulemap").write_text(module)
    return headers


def create_xcframeworks(source, selected):
    DIST.mkdir(exist_ok=True)
    for name, product in PRODUCTS.items():
        output = DIST / f"{name}.xcframework"
        if output.exists():
            shutil.rmtree(output)
        headers = stage_headers(source, name, product)
        args = ["xcodebuild", "-create-xcframework"]
        for slice_name in selected:
            archive = BUILD / "slices" / slice_name / name / f"lib{product['library']}.a"
            args += ["-library", archive, "-headers", headers]
        run([*args, "-output", output], log=BUILD / "logs" / f"{name}-xcframework.log")
        licenses = output / "Licenses"
        licenses.mkdir()
        shutil.copyfile(ROOT / "LICENSE", licenses / "WebP-Cocoa-LICENSE")
        for filename in ("COPYING", "PATENTS", "AUTHORS"):
            shutil.copyfile(source / filename, licenses / filename)
        print(f"Created {output}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("platform", nargs="?", default="all", choices=["all", "ios", "macos", "catalyst", "tvos", "watchos", "visionos"])
    parser.add_argument("--slices", help="Comma-separated slice names; overrides platform (development only)")
    parser.add_argument("--jobs", type=int, default=min(os.cpu_count() or 2, 8))
    parser.add_argument("--allow-toolchain-mismatch", action="store_true", help="Allow local compiler/tool differences; release packaging rejects them")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    if args.slices is not None:
        selected = args.slices.split(",")
    elif args.platform == "all":
        selected = list(SLICES)
    else:
        selected = [name for name in SLICES if name == args.platform or name.startswith(args.platform + "-")]
        if args.platform == "ios":
            selected.append("catalyst")
    if not selected or len(set(selected)) != len(selected) or any(name not in SLICES for name in selected):
        parser.error("--slices must contain unique names from: " + ", ".join(SLICES))
    tools = check_tools(selected, args.allow_toolchain_mismatch)
    (BUILD / "logs").mkdir(parents=True, exist_ok=True)
    # A failed rebuild must not leave publishable provenance from an older run.
    (DIST / "build-info.json").unlink(missing_ok=True)
    source = fetch_source()
    for name in selected:
        build_slice(source, name, args.jobs)
    create_xcframeworks(source, selected)
    info = {"schema": 1, "libwebp": LOCK["libwebp"], "tools": tools,
            "toolchain_override": args.allow_toolchain_mismatch, "slices": selected,
            "deployment": LOCK["deployment"], "architecture_deployment": LOCK["architecture_deployment"],
            "products": list(PRODUCTS),
            "cmake": {"generator": "Ninja", "build_type": "Release", "shared": False,
                      "swap_16bit_csp": True, "simd": True, "threading": True}}
    (DIST / "build-info.json").write_text(json.dumps(info, indent=2) + "\n")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, OSError) as error:
        sys.exit(str(error))

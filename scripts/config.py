"""Shared build/distribution contract. No third-party Python dependencies."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = json.loads((ROOT / "toolchain.json").read_text())
BUILD = ROOT / "build"
DIST = ROOT / "dist"
PRODUCTS = {
    "WebP": {"library": "webp", "headers": ["decode.h", "encode.h", "types.h"]},
    "WebPDecoder": {"library": "webpdecoder", "headers": ["decode.h", "types.h"]},
    "WebPDemux": {"library": "webpdemux", "headers": ["decode.h", "demux.h", "mux_types.h", "types.h"]},
    "WebPMux": {"library": "webpmux", "headers": ["encode.h", "mux.h", "mux_types.h", "types.h"]},
}
# A slice is one Apple platform/variant. Only architectures within that slice
# are combined with lipo; device/simulator/Catalyst archives never are.
SLICES = {
    "macos": {"sdk": "macosx", "system": "Darwin", "platform": "macos", "archs": ["arm64", "x86_64"], "target": "{arch}-apple-macos{min}"},
    "ios": {"sdk": "iphoneos", "system": "iOS", "platform": "ios", "archs": ["arm64"], "target": "{arch}-apple-ios{min}"},
    "ios-simulator": {"sdk": "iphonesimulator", "system": "iOS", "platform": "ios", "variant": "simulator", "archs": ["arm64", "x86_64"], "target": "{arch}-apple-ios{min}-simulator"},
    "catalyst": {"sdk": "macosx", "system": "Darwin", "platform": "ios", "variant": "maccatalyst", "archs": ["arm64", "x86_64"], "target": "{arch}-apple-ios{min}-macabi"},
    "tvos": {"sdk": "appletvos", "system": "tvOS", "platform": "tvos", "archs": ["arm64"], "target": "{arch}-apple-tvos{min}"},
    "tvos-simulator": {"sdk": "appletvsimulator", "system": "tvOS", "platform": "tvos", "variant": "simulator", "archs": ["arm64", "x86_64"], "target": "{arch}-apple-tvos{min}-simulator"},
    "watchos": {"sdk": "watchos", "system": "watchOS", "platform": "watchos", "archs": ["arm64", "arm64_32"], "target": "{arch}-apple-watchos{min}"},
    "watchos-simulator": {"sdk": "watchsimulator", "system": "watchOS", "platform": "watchos", "variant": "simulator", "archs": ["arm64", "x86_64"], "target": "{arch}-apple-watchos{min}-simulator"},
    "visionos": {"sdk": "xros", "system": "visionOS", "platform": "xros", "archs": ["arm64"], "target": "{arch}-apple-xros{min}"},
    "visionos-simulator": {"sdk": "xrsimulator", "system": "visionOS", "platform": "xros", "variant": "simulator", "archs": ["arm64"], "target": "{arch}-apple-xros{min}-simulator"},
}


def deployment(slice_name, arch=None):
    overrides = LOCK["architecture_deployment"].get(slice_name, {})
    return overrides.get(arch, LOCK["deployment"][slice_name.split("-")[0]])


def triple(slice_name, arch):
    return SLICES[slice_name]["target"].format(arch=arch, min=deployment(slice_name, arch))

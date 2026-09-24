#!/usr/bin/env python3
"""Rebuild repository-owned fixture pixels using libwebp 1.6.0 CLI tools."""
from pathlib import Path
import re
import subprocess
import tempfile

TESTS = Path(__file__).resolve().parent
for tool in ("cwebp", "webpmux"):
    version = subprocess.check_output([tool, "-version"], text=True).splitlines()[0].strip()
    if version != "1.6.0":
        raise SystemExit(f"{tool} 1.6.0 required, found {version}")
with tempfile.TemporaryDirectory() as temporary:
    source = Path(temporary)
    output = TESTS / "Fixtures"
    rgba = bytes([255, 0, 0, 255, 0, 255, 0, 128, 0, 0, 255, 255, 255, 255, 255, 0])
    (source / "rgba.pam").write_bytes(
        b"P7\nWIDTH 2\nHEIGHT 2\nDEPTH 4\nMAXVAL 255\nTUPLTYPE RGB_ALPHA\nENDHDR\n" + rgba)
    (source / "black.ppm").write_bytes(b"P6\n4 4\n255\n" + bytes(48))
    subprocess.run(["cwebp", "-quiet", "-lossless", "-exact", str(source / "rgba.pam"),
                    "-o", str(output / "lossless.webp")], check=True)
    subprocess.run(["cwebp", "-quiet", "-q", "90", str(source / "black.ppm"),
                    "-o", str(output / "lossy.webp")], check=True)
    for name, pixel in [("red", bytes([255, 0, 0])), ("green", bytes([0, 255, 0]))]:
        (source / f"{name}.ppm").write_bytes(b"P6\n2 2\n255\n" + pixel * 4)
        subprocess.run(["cwebp", "-quiet", "-lossless", str(source / f"{name}.ppm"),
                        "-o", str(source / f"{name}.webp")], check=True)
    subprocess.run(["webpmux", "-frame", str(source / "red.webp"), "+40+0+0+0-b",
                    "-frame", str(source / "green.webp"), "+60+0+0+0-b", "-loop", "3",
                    "-o", str(source / "animation.webp")], check=True)
    (source / "exif.bin").write_bytes(b"Exif\0\0II\x2a\0\x08\0\0\0\0\0\0\0\0\0")
    subprocess.run(["webpmux", "-set", "exif", str(source / "exif.bin"),
                    str(source / "animation.webp"), "-o", str(output / "animation.webp")], check=True)
    swift = TESTS / "ImportDecoder.swift"
    array = ", ".join(str(byte) for byte in (output / "lossless.webp").read_bytes())
    swift.write_text(re.sub(r"let webp: \[UInt8\] = \[[^\]]*\]",
                           f"let webp: [UInt8] = [{array}]", swift.read_text()))

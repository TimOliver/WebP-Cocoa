"""Portable release roundtrips with structural XCFramework fixtures, not Mach-O binaries."""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import plistlib
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import distribution
from config import LOCK, PRODUCTS, SLICES


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.dist = self.root / "dist"
        self.dist.mkdir()
        self.lock = copy.deepcopy(LOCK)
        self.tag = self.lock["libwebp"]["version"]
        self.repository = "FixtureOwner/WebP-Cocoa"
        for name, value in (("ROOT", self.root), ("DIST", self.dist), ("LOCK", self.lock)):
            patcher = mock.patch.object(distribution, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        (self.root / "LICENSE").write_text("repository BSD notice\n")
        for name, product in PRODUCTS.items():
            framework = self.dist / f"{name}.xcframework"
            framework.mkdir()
            libraries = []
            for slice_name, spec in SLICES.items():
                directory = framework / slice_name
                headers = directory / "Headers"
                (headers / "webp").mkdir(parents=True)
                library_name = f"lib{product['library']}.a"
                # Archive signature only: real object/platform checks are compiler tests.
                (directory / library_name).write_bytes(b"!<arch>\n")
                for header in product["headers"]:
                    (headers / header).write_text(f"/* {header} */\n")
                    (headers / "webp" / header).write_text(f'#include "../{header}"\n')
                (headers / "module.modulemap").write_text(f'module {name} {{ header "{product["headers"][0]}" export * }}\n')
                entry = {
                    "LibraryIdentifier": slice_name, "LibraryPath": library_name,
                    "HeadersPath": "Headers", "SupportedArchitectures": spec["archs"],
                    "SupportedPlatform": spec["platform"],
                }
                if "variant" in spec:
                    entry["SupportedPlatformVariant"] = spec["variant"]
                libraries.append(entry)
            (framework / "Info.plist").write_bytes(plistlib.dumps({
                "CFBundlePackageType": "XFWK", "XCFrameworkFormatVersion": "1.0",
                "AvailableLibraries": libraries,
            }))
            (framework / "Licenses").mkdir()
            for license_name in ("COPYING", "PATENTS", "AUTHORS", "WebP-Cocoa-LICENSE"):
                (framework / "Licenses" / license_name).write_text(f"license {license_name}\n")
        self.provenance = {
            "schema": 1, "libwebp": self.lock["libwebp"], "toolchain_override": False,
            "slices": list(SLICES), "deployment": self.lock["deployment"], "products": list(PRODUCTS),
            "architecture_deployment": self.lock["architecture_deployment"],
            "tools": {key: value for key, value in self.lock["tools"].items() if key != "sdk"},
            "cmake": {"generator": "Ninja", "build_type": "Release", "shared": False,
                      "swap_16bit_csp": True, "simd": True, "threading": True},
        }
        self.provenance["tools"].update({
            "sdks": {spec["sdk"]: self.lock["tools"]["sdk"] for spec in SLICES.values()},
            "mismatches": [], "clang": "fixture compiler", "swift": "fixture compiler",
        })
        self.write_provenance()

    def write_provenance(self):
        (self.dist / "build-info.json").write_text(json.dumps(self.provenance))

    def package(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return distribution.package(self.tag, self.repository)

    def verify(self, directory, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return distribution.verify(directory, self.tag, self.repository, **kwargs)

    def update_sums(self, release, *, regenerate_manifest=False):
        if regenerate_manifest:
            checksums = {name: distribution.sha256(release / f"{name}.xcframework.zip") for name in PRODUCTS}
            (release / "Package.swift").write_text(distribution.manifest(
                tag=self.tag, checksums=checksums, repository=self.repository))
        files = sorted(path for path in release.iterdir() if path.name != "SHA256SUMS")
        (release / "SHA256SUMS").write_text("".join(f"{distribution.sha256(path)}  {path.name}\n" for path in files))

    def test_zip_checksum_manifest_and_extracted_consumer_roundtrip(self):
        release = self.package()
        manifest = (release / "Package.swift").read_text()
        sums = dict(line.split("  ", 1)[::-1] for line in (release / "SHA256SUMS").read_text().splitlines())
        expected = {f"{name}.xcframework.zip" for name in PRODUCTS} | {
            "Package.swift", "build-info.json", "LICENSE.WebP-Cocoa",
        }
        self.assertEqual(set(sums), expected)
        for filename, digest in sums.items():
            self.assertEqual(hashlib.sha256((release / filename).read_bytes()).hexdigest(), digest)
        for name in PRODUCTS:
            asset = f"{name}.xcframework.zip"
            self.assertIn(f"https://github.com/{self.repository}/releases/download/{self.tag}/{asset}", manifest)
            self.assertIn(f'checksum: "{sums[asset]}"', manifest)
            with zipfile.ZipFile(release / asset) as archive:
                self.assertTrue(all(member.startswith(f"{name}.xcframework/") for member in archive.namelist()))
                self.assertIn(f"{name}.xcframework/Licenses/PATENTS", archive.namelist())
        consumer = self.root / "consumer"
        self.verify(release, extract_to=consumer)
        self.assertEqual((consumer / "Package.swift").read_text(), distribution.manifest(local=True))
        self.assertEqual(json.loads((consumer / "dist" / "build-info.json").read_text()), self.provenance)
        for name in PRODUCTS:
            distribution.validate_xcframework(consumer / "dist" / f"{name}.xcframework")

    def test_archive_bytes_are_repeatable(self):
        framework = self.dist / "WebPDecoder.xcframework"
        first, second = self.root / "first.zip", self.root / "second.zip"
        distribution.zip_framework(framework, first)
        distribution.zip_framework(framework, second)
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_rejects_invalid_or_unpinned_tags_before_packaging(self):
        for tag in (f"v{self.tag}", "0.0.0", f"{self.tag}-rc1", "../1.6.0", ""):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                distribution.package(tag, self.repository)
        self.assertFalse((self.dist / "release").exists())

    def test_release_cannot_replace_existing_archive_bytes(self):
        release = self.package()
        original = (release / "SHA256SUMS").read_bytes()
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.package()
        self.assertEqual((release / "SHA256SUMS").read_bytes(), original)

    def test_rejects_override_and_mismatched_toolchain(self):
        original = copy.deepcopy(self.provenance)
        for change in ("override", "python", "sdk", "missing-sdk", "missing-slice", "architecture-deployment"):
            with self.subTest(change=change):
                self.provenance = copy.deepcopy(original)
                if change == "override":
                    self.provenance["toolchain_override"] = True
                elif change == "python":
                    self.provenance["tools"]["python"] = "0.0.0"
                elif change == "sdk":
                    self.provenance["tools"]["sdks"]["iphoneos"] = "0.0"
                elif change == "missing-sdk":
                    self.provenance["tools"]["sdks"].pop("iphoneos")
                elif change == "missing-slice":
                    self.provenance["slices"].pop()
                else:
                    self.provenance["architecture_deployment"] = {}
                self.write_provenance()
                with self.assertRaises(ValueError):
                    self.package()
                self.assertFalse((self.dist / "release").exists())

    def test_rejects_incomplete_xcframework_slice_matrix(self):
        info = self.dist / "WebPDemux.xcframework" / "Info.plist"
        data = plistlib.loads(info.read_bytes())
        data["AvailableLibraries"].pop()
        info.write_bytes(plistlib.dumps(data))
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.package()
        self.assertFalse((self.dist / "release").exists())

    def test_rejects_missing_licenses_or_import_headers(self):
        framework = self.dist / "WebPDecoder.xcframework"
        required = [framework / "Licenses" / name for name in (
            "COPYING", "PATENTS", "AUTHORS", "WebP-Cocoa-LICENSE")]
        required += [framework / "ios" / "Headers" / name for name in (
            "module.modulemap", "decode.h", "webp/decode.h")]
        for file in required:
            with self.subTest(file=file.relative_to(framework)):
                original = file.read_bytes()
                file.unlink()
                try:
                    with self.assertRaises(ValueError):
                        self.package()
                    self.assertFalse((self.dist / "release").exists())
                finally:
                    file.write_bytes(original)

    def test_rejects_archive_tampering(self):
        release = self.package()
        asset = release / "WebPDecoder.xcframework.zip"
        asset.write_bytes(asset.read_bytes() + b"tampered")
        with self.assertRaisesRegex(ValueError, "Checksum mismatch"):
            self.verify(release)

    def test_rejects_manifest_substitution_even_with_updated_checksums(self):
        release = self.package()
        manifest = release / "Package.swift"
        manifest.write_text(manifest.read_text().replace(self.repository, "Different/Repository"))
        self.update_sums(release)
        with self.assertRaisesRegex(ValueError, "Package.swift does not match"):
            self.verify(release)

    def test_rejects_unsafe_zip_paths_and_symlinks_before_extraction(self):
        release = self.package()
        asset = release / "WebP.xcframework.zip"
        for index, name in enumerate(("WebP.xcframework/../../escaped", "WebP.xcframework/link")):
            with self.subTest(name=name):
                entry = zipfile.ZipInfo(name)
                if index:
                    entry.create_system = 3
                    entry.external_attr = 0o120777 << 16
                with zipfile.ZipFile(asset, "w") as archive:
                    archive.writestr(entry, "../../escaped")
                self.update_sums(release, regenerate_manifest=True)
                with self.assertRaisesRegex(ValueError, "Unsafe archive member|symlinks"):
                    self.verify(release, extract_to=self.root / f"unsafe-consumer-{index}")
                self.assertFalse((self.root / "escaped").exists())


if __name__ == "__main__":
    unittest.main()

"""Portable release roundtrips with structural XCFramework fixtures, not Mach-O binaries."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import distribution
from config import LOCK, PRODUCTS, SLICES


class ReleaseWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.repository = Path(__file__).resolve().parents[1]
        self.workflow = (self.repository / ".github/workflows/package.yml").read_text()

    def test_workflow_validates_and_exports_prefixed_tag(self):
        script = textwrap.dedent(self.workflow.split("python3 - <<'PY'\n", 1)[1]
                                 .split("\n          PY", 1)[0])
        tag = f"v{LOCK['package_version']}"
        cases = [("push", "", True), ("pull_request", "", True),
                 ("workflow_dispatch", tag, True),
                 ("workflow_dispatch", tag[1:], False),
                 ("workflow_dispatch", "v0.0.0", False),
                 ("workflow_dispatch", f"v{tag}", False)]
        for event, requested, valid in cases:
            with self.subTest(event=event, requested=requested), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "output"
                result = subprocess.run(
                    [sys.executable, "-c", script], cwd=self.repository,
                    env={**os.environ, "GITHUB_EVENT_NAME": event, "REQUESTED_VERSION": requested,
                         "GITHUB_OUTPUT": str(output), "PYTHONDONTWRITEBYTECODE": "1"},
                    capture_output=True, text=True)
                if valid:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(output.read_text(), f"tag={tag}\n")
                else:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(output.exists())

    def test_draft_and_published_release_titles_match_tag(self):
        self.assertIn('--verify-tag --draft --title "$RELEASE_TAG"', self.workflow)
        self.assertIn('--tag "$RELEASE_TAG" --target "$RELEASE_COMMIT" --title "$RELEASE_TAG"',
                      self.workflow)

    def test_xcode_consumer_gates_packaging_and_draft_publication(self):
        build_test = self.workflow.index("run: python3 scripts/test-xcode-consumer.py\n")
        package = self.workflow.index("python3 scripts/distribution.py package")
        downloaded_test = self.workflow.index('python3 scripts/test-xcode-consumer.py --package "$RUNNER_TEMP/release-consumer"')
        publish = self.workflow.index('gh release edit "$CANDIDATE_TAG"')
        public_test = self.workflow.index('python3 scripts/test-xcode-consumer.py --package "$GITHUB_WORKSPACE"')
        self.assertLess(build_test, package)
        self.assertLess(package, downloaded_test)
        self.assertLess(downloaded_test, publish)
        self.assertLess(publish, public_test)

    def test_publishing_refuses_existing_tags_and_never_replaces_assets(self):
        self.assertIn('git show-ref --verify --quiet "refs/tags/$RELEASE_TAG"', self.workflow)
        self.assertIn('git ls-remote --tags origin "refs/tags/$RELEASE_TAG"', self.workflow)
        self.assertNotIn("--clobber", self.workflow)
        self.assertNotIn("--force", self.workflow)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.dist = self.root / "dist"
        self.dist.mkdir()
        self.lock = copy.deepcopy(LOCK)
        self.tag = f"v{self.lock['package_version']}"
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
                bundle = directory / f"{name}.framework"
                headers = bundle / "Headers"
                (headers / "webp").mkdir(parents=True)
                # Archive signature only: real object/platform checks are compiler tests.
                (bundle / name).write_bytes(b"!<arch>\n")
                for header in product["headers"]:
                    (headers / header).write_text(f"/* {header} */\n")
                    (headers / "webp" / header).write_text(f'#include "../{header}"\n')
                (bundle / "Modules").mkdir()
                (bundle / "Modules/module.modulemap").write_text(
                    f'framework module {name} [system] {{ header "{product["headers"][0]}" export * }}\n')
                (bundle / "Info.plist").write_bytes(plistlib.dumps({
                    "CFBundlePackageType": "FMWK", "CFBundleExecutable": name,
                }))
                entry = {
                    "LibraryIdentifier": slice_name, "LibraryPath": f"{name}.framework",
                    "SupportedArchitectures": spec["archs"],
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
            "schema": 2, "libwebp": self.lock["libwebp"], "toolchain_override": False,
            "package_version": self.lock["package_version"], "packaging": "static-framework-v1",
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

    def test_accepts_v_prefixed_pinned_tag(self):
        self.assertEqual(distribution.validate_tag(self.tag), self.tag)
        self.assertEqual(self.lock["package_version"], self.tag[1:])

    def test_package_version_can_advance_without_changing_upstream_source(self):
        upstream = copy.deepcopy(self.lock["libwebp"])
        self.lock["package_version"] = "9.8.7"
        self.assertEqual(distribution.validate_tag("v9.8.7"), "v9.8.7")
        with self.assertRaisesRegex(ValueError, "package version"):
            distribution.validate_tag(f"v{upstream['version']}")
        self.provenance["package_version"] = "9.8.7"
        distribution.validate_provenance(self.provenance)
        self.assertEqual(self.provenance["libwebp"], upstream)
        checksums = {name: "a" * 64 for name in PRODUCTS}
        manifest = distribution.manifest(tag="v9.8.7", checksums=checksums)
        self.assertIn("/releases/download/v9.8.7/", manifest)

    def test_rejects_invalid_or_unpinned_tags_before_packaging(self):
        for tag in (self.tag[1:], f"v{self.tag}", self.tag.upper(), "v0.0.0",
                    f"{self.tag}-rc1", "../v1.6.0", ""):
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
        for change in ("override", "python", "sdk", "missing-sdk", "missing-slice",
                       "architecture-deployment", "schema", "packaging", "package-version"):
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
                elif change == "architecture-deployment":
                    self.provenance["architecture_deployment"] = {}
                elif change == "schema":
                    self.provenance["schema"] = 1
                elif change == "packaging":
                    self.provenance["packaging"] = "raw-static-library"
                else:
                    self.provenance["package_version"] = "0.0.0"
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
        bundle = framework / "ios/WebPDecoder.framework"
        required = [framework / "Licenses" / name for name in (
            "COPYING", "PATENTS", "AUTHORS", "WebP-Cocoa-LICENSE")]
        required += [bundle / "Headers" / name for name in ("decode.h", "webp/decode.h")]
        required += [bundle / "Modules/module.modulemap", bundle / "WebPDecoder"]
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

    def test_rejects_raw_library_headers_that_collide_when_xcode_stages_targets(self):
        framework = self.dist / "WebPDecoder.xcframework"
        plist = framework / "Info.plist"
        info = plistlib.loads(plist.read_bytes())
        entry = info["AvailableLibraries"][0]
        entry.update({"LibraryPath": "libwebpdecoder.a", "HeadersPath": "Headers"})
        plist.write_bytes(plistlib.dumps(info))
        with self.assertRaisesRegex(ValueError, "named framework bundles without HeadersPath"):
            self.package()

    def test_rejects_shared_framework_names_and_external_headers(self):
        plist = self.dist / "WebPDemux.xcframework/Info.plist"
        original = plist.read_bytes()
        for change in ("shared-name", "external-headers"):
            with self.subTest(change=change):
                info = plistlib.loads(original)
                entry = info["AvailableLibraries"][0]
                if change == "shared-name":
                    entry["LibraryPath"] = "WebPDecoder.framework"
                else:
                    entry["HeadersPath"] = "Headers"
                plist.write_bytes(plistlib.dumps(info))
                with self.assertRaisesRegex(ValueError, "named framework bundles without HeadersPath"):
                    self.package()

    def test_rejects_mismatched_framework_executable_and_module(self):
        bundle = self.dist / "WebPDemux.xcframework/ios/WebPDemux.framework"
        plist = bundle / "Info.plist"
        original = plist.read_bytes()
        info = plistlib.loads(original)
        info["CFBundleExecutable"] = "WebPDecoder"
        plist.write_bytes(plistlib.dumps(info))
        with self.assertRaisesRegex(ValueError, "Invalid named framework"):
            self.package()
        plist.write_bytes(original)
        module_map = bundle / "Modules/module.modulemap"
        module_map.write_text('module WebPDemux { header "demux.h" export * }\n')
        with self.assertRaisesRegex(ValueError, "named framework module map"):
            self.package()

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

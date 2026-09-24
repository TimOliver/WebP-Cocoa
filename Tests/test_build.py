"""Portable build-contract tests; compiler/link/decode checks live in smoke.py."""
import contextlib
import copy
import hashlib
import io
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build
from config import PRODUCTS, SLICES, deployment, triple


class BuildContractTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        for name, path in (("ROOT", Path(temporary.name)),
                           ("BUILD", Path(temporary.name) / "build"),
                           ("DIST", Path(temporary.name) / "dist")):
            patcher = mock.patch.object(build, name, path)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_platforms_keep_variants_separate_and_current_architectures(self):
        expected = {
            "macos": {"arm64", "x86_64"}, "ios": {"arm64"},
            "ios-simulator": {"arm64", "x86_64"}, "catalyst": {"arm64", "x86_64"},
            "tvos": {"arm64"}, "tvos-simulator": {"arm64", "x86_64"},
            "watchos": {"arm64", "arm64_32"}, "watchos-simulator": {"arm64", "x86_64"},
            "visionos": {"arm64"}, "visionos-simulator": {"arm64"},
        }
        self.assertEqual(set(SLICES), set(expected))
        platform_variants = set()
        for name, arches in expected.items():
            with self.subTest(slice=name):
                info = SLICES[name]
                self.assertEqual(set(info["archs"]), arches)
                variant = (info["platform"], info.get("variant"))
                self.assertNotIn(variant, platform_variants)
                platform_variants.add(variant)
                for arch in arches:
                    self.assertIn(f"{arch}-apple-", triple(name, arch))
                    self.assertIn(deployment(name, arch), triple(name, arch))
                if name.endswith("simulator"):
                    self.assertTrue(triple(name, "arm64").endswith("-simulator"))
        self.assertTrue(triple("catalyst", "arm64").endswith("-macabi"))

    def test_flags_preserve_pixel_layout_without_host_catalyst_deployment(self):
        with mock.patch.object(build, "run", return_value="/Xcode/clang"), \
             mock.patch.object(build.shutil, "which", return_value="/tools/ninja"):
            catalyst = build.cmake_options("catalyst", "arm64", "/SDKs/MacOSX.sdk")
            ios = build.cmake_options("ios", "arm64", "/SDKs/iPhoneOS.sdk")
        self.assertIn("-DCMAKE_OSX_DEPLOYMENT_TARGET=", catalyst)
        self.assertIn(f"-DCMAKE_C_COMPILER_TARGET={triple('catalyst', 'arm64')}", catalyst)
        self.assertFalse(any("mmacosx-version-min" in flag for flag in catalyst))
        self.assertIn(f"-DCMAKE_OSX_DEPLOYMENT_TARGET={deployment('ios')}", ios)
        for flags in (catalyst, ios):
            self.assertIn("-DBUILD_SHARED_LIBS=OFF", flags)
            self.assertIn("-DWEBP_ENABLE_SWAP_16BIT_CSP=ON", flags)
            self.assertIn("-DWEBP_BUILD_LIBWEBPMUX=ON", flags)
            self.assertIn("-DWEBP_BUILD_CWEBP=OFF", flags)
            self.assertIn("-DWEBP_BUILD_DWEBP=OFF", flags)
            self.assertIn("-DWEBP_BUILD_WEBPMUX=OFF", flags)
            self.assertFalse(any("bitcode" in flag for flag in flags))

    def test_watchos_arm64_uses_new_abi_minimum_without_raising_other_watch_slices(self):
        self.assertEqual(triple("watchos", "arm64"), "arm64-apple-watchos26.0")
        self.assertEqual(triple("watchos", "arm64_32"), "arm64_32-apple-watchos8.0")
        self.assertEqual(triple("watchos-simulator", "arm64"), "arm64-apple-watchos8.0-simulator")
        with mock.patch.object(build, "run", return_value="/Xcode/clang"), \
             mock.patch.object(build.shutil, "which", return_value="/tools/ninja"):
            flags = build.cmake_options("watchos", "arm64", "/SDKs/WatchOS.sdk")
        self.assertIn("-DCMAKE_OSX_DEPLOYMENT_TARGET=26.0", flags)

    def test_subprocess_environment_cannot_override_platform_flags(self):
        inherited = {
            "CFLAGS": "-arch i386", "LDFLAGS": "-L/host/lib", "SDKROOT": "/wrong-sdk",
            "MACOSX_DEPLOYMENT_TARGET": "99.0", "IPHONEOS_DEPLOYMENT_TARGET": "99.0",
            "TVOS_DEPLOYMENT_TARGET": "99.0", "WATCHOS_DEPLOYMENT_TARGET": "99.0",
            "XROS_DEPLOYMENT_TARGET": "99.0", "ZERO_AR_DATE": "0",
        }
        with mock.patch.dict(os.environ, inherited), \
             mock.patch.object(build.subprocess, "check_output", return_value="ok\n") as command:
            self.assertEqual(build.run(["test-tool"]), "ok")
        environment = command.call_args.kwargs["env"]
        for key in inherited.keys() - {"ZERO_AR_DATE"}:
            self.assertNotIn(key, environment)
        self.assertEqual(environment["ZERO_AR_DATE"], "1")

    def test_invalid_selections_fail_before_tools_or_network(self):
        arguments = [
            ["--slices", ""], ["--slices", "ios,ios"],
            ["--slices", "ios,,macos"], ["--slices", "iphoneos"],
            ["--jobs", "0"], ["--jobs", "-2"],
        ]
        for args in arguments:
            with self.subTest(args=args), \
                 mock.patch.object(sys, "argv", ["build.py", *args]), \
                 mock.patch.object(build, "check_tools", side_effect=AssertionError("invalid CLI reached tool probing")) as check_tools, \
                 mock.patch.object(build, "fetch_source") as fetch_source, \
                 contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    build.main()
                self.assertEqual(error.exception.code, 2)
                check_tools.assert_not_called()
                fetch_source.assert_not_called()


class SourceArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.lock = copy.deepcopy(build.LOCK)
        self.lock["libwebp"]["version"] = "test"
        self.archive = self.directory / "downloads" / "libwebp-test.tar.gz"
        self.archive.parent.mkdir()
        self.addCleanup(mock.patch.stopall)
        mock.patch.object(build, "ROOT", self.directory).start()
        mock.patch.object(build, "BUILD", self.directory).start()
        mock.patch.object(build, "DIST", self.directory / "dist").start()
        mock.patch.object(build, "LOCK", self.lock).start()

    def write_archive(self, extra_member=None):
        with tarfile.open(self.archive, "w:gz") as bundle:
            content = b"upstream source\n"
            member = tarfile.TarInfo("libwebp-test/CMakeLists.txt")
            member.size = len(content)
            bundle.addfile(member, io.BytesIO(content))
            if extra_member is not None:
                bundle.addfile(extra_member)
        self.lock["libwebp"]["sha256"] = hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def test_verified_source_extracts_to_expected_root(self):
        self.write_archive()
        with mock.patch.object(build, "run") as run:
            source = build.fetch_source()
        run.assert_not_called()
        self.assertEqual(source, self.directory / "source" / "libwebp-test")
        self.assertEqual((source / "CMakeLists.txt").read_bytes(), b"upstream source\n")

    def test_cached_hash_mismatch_does_not_extract(self):
        self.write_archive()
        self.archive.write_bytes(self.archive.read_bytes() + b"tampered")
        with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
            build.fetch_source()
        self.assertFalse((self.directory / "source").exists())

    def test_download_hash_mismatch_is_not_cached(self):
        self.lock["libwebp"]["sha256"] = "0" * 64
        def download(args):
            Path(args[-1]).write_bytes(b"wrong download")
        with mock.patch.object(build, "run", side_effect=download), \
             self.assertRaisesRegex(RuntimeError, "checksum does not match"):
            build.fetch_source()
        self.assertFalse(self.archive.exists())
        self.assertFalse(self.archive.with_suffix(".download").exists())
        self.assertFalse((self.directory / "source").exists())

    def test_rejects_traversal_absolute_paths_and_links_before_extraction(self):
        traversal = tarfile.TarInfo("../outside")
        absolute = tarfile.TarInfo("/outside")
        symlink = tarfile.TarInfo("libwebp-test/link")
        symlink.type, symlink.linkname = tarfile.SYMTYPE, "../outside"
        hardlink = tarfile.TarInfo("libwebp-test/hardlink")
        hardlink.type, hardlink.linkname = tarfile.LNKTYPE, "libwebp-test/CMakeLists.txt"
        for member in (traversal, absolute, symlink, hardlink):
            with self.subTest(member=member.name, type=member.type):
                self.write_archive(member)
                with self.assertRaisesRegex(RuntimeError, "Unsafe source archive entry"):
                    build.fetch_source()
                # The valid member before the unsafe entry must not have been extracted.
                self.assertEqual(list((self.directory / "source").iterdir()), [])


class DistributionInputsTests(unittest.TestCase):
    def test_products_keep_legacy_imports_c_headers_and_license_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "upstream"
            (source / "src" / "webp").mkdir(parents=True)
            for header in {header for product in PRODUCTS.values() for header in product["headers"]}:
                (source / "src" / "webp" / header).write_text(f"/* upstream {header} */\n")
            for name in ("COPYING", "PATENTS", "AUTHORS"):
                (source / name).write_text(f"upstream {name}\n")
            (root / "LICENSE").write_text("repository license\n")
            commands = []
            def create_framework(args, *, log=None):
                commands.append(args)
                Path(args[args.index("-output") + 1]).mkdir(parents=True)
            selected = ["ios", "ios-simulator", "catalyst"]
            with mock.patch.object(build, "BUILD", root / "build"), \
                 mock.patch.object(build, "DIST", root / "dist"), \
                 mock.patch.object(build, "ROOT", root), \
                 mock.patch.object(build, "run", side_effect=create_framework), \
                 contextlib.redirect_stdout(io.StringIO()):
                build.create_xcframeworks(source, selected)
            self.assertEqual(set(PRODUCTS), {"WebP", "WebPDecoder", "WebPDemux", "WebPMux"})
            self.assertEqual(len(commands), 4)
            for name, product in PRODUCTS.items():
                headers = root / "build" / "headers" / name
                module = (headers / "module.modulemap").read_text()
                self.assertIn(f"module {name} [system]", module)
                if name == "WebP":
                    self.assertIn("module Decoder", module)
                for header in product["headers"]:
                    self.assertEqual((headers / header).read_bytes(), (source / "src" / "webp" / header).read_bytes())
                    self.assertEqual((headers / "webp" / header).read_text(), f'#include "../{header}"\n')
                    self.assertIn(f'header "{header}"', module)
                licenses = root / "dist" / f"{name}.xcframework" / "Licenses"
                for license_name in ("COPYING", "PATENTS", "AUTHORS"):
                    self.assertEqual((licenses / license_name).read_bytes(), (source / license_name).read_bytes())
                self.assertEqual((licenses / "WebP-Cocoa-LICENSE").read_bytes(), (root / "LICENSE").read_bytes())
            for command in commands:
                libraries = [Path(command[index + 1]) for index, arg in enumerate(command) if arg == "-library"]
                self.assertEqual([path.parent.parent.name for path in libraries], selected)
                self.assertEqual(command.count("-headers"), len(selected))


if __name__ == "__main__":
    unittest.main()

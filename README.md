<p align="center">
    <img src="https://github.com/TimOliver/WebP-Cocoa/raw/main/banner.png" width="731" alt="WebP-Cocoa Banner" />
</p>

[WebP](https://developers.google.com/speed/webp) is a modern image file format that provides amazing lossy and lossless compression fidelity. WebP is developed by Google and is freely distributed as open source software.

Google provides pre-built binaries of WebP for both iOS and macOS, however the build script has not been updated recently and as such, the binaries do not support either Swift modules, or Mac Catalyst.

Taking the official build script by Google and modifying it, this repository serves pre-built binaries for all of Apple's platforms, adding in tvOS and watchOS, as well as supporting Mac Catalyst via the new `xcframework` format.

There are 4 separate frameworks available for each platform:

* **WebP**: Both encoding and decoding capabilities for the WebP format.
* **WebPDecoder**: Just the decoding capabilities for the WebP format.
* **WebPMux**: Enables manipulation of WebP container image features like color profile, metadata, animation.
* **WebPDemux**: Enables extraction of image and extended format data from WebP files.

# Instructions

1. Download and extract the package for your platform and capabilities of choice.
2. Drag the `framework` folder into your Xcode project.
3. When prompted, make sure *Copy items if needed* is checked before proceeding.

# Packages

For ultimate convenience, the pre-built frameworks have been packaged up into every combination of ZIP archives. Simply click one of the links below to begin downloading.

<table>
    <tr>
        <td colspan="4" align="center">
            <h3><a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework.zip">Download All Frameworks for All Platforms (ZIP)</a></h3>
        </td>
    </tr>
    <tr>
        <th>Platform</th>
        <th>Versions</th>
        <th>Slices</th>
        <th>Download Packages</th>
    </tr>
    <tr>
        <td><b>iOS</b><br />(Mac Catalyst)</td>
        <td>iOS 11.0 and up.<br/>macOS 10.15 and up.</td>
        <td>
            <ul>
                <li><code>arm64</code></li>
                <li><code>x86_64</code> (Mac Catalyst)</li>
                <li><code>x86_64</code> (Simulator)</li>
            </ul>
        </td>
        <td>
            <ul>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-catalyst.zip">
                        <strong>Download All (ZIP)</strong>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-catalyst-webp.zip">
                        <code>WebP.xcframework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-catalyst-webpdecoder.zip">
                        <code>WebPDecoder.xcframework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-catalyst-webpdemux.zip">
                        <code>WebPDemux.xcframework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-catalyst-webpmux.zip">
                        <code>WebPMux.xcframework</code>
                    </a>
                </li>
            </ul>
        </td>
    </tr>
    <tr>
        <td><strong>iOS</strong></td>
        <td>iOS 9.0 and up.</td>
        <td>
            <ul>
                <li><code>arm64</code></li>
                <li><code>armv7</code></li>
                <li><code>armv7s</code></li>
                <li><code>x86_64</code></li>
                <li><code>i386</code></li>
            </ul>
        </td>
        <td>
            <ul>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios.zip">
                        <strong>Download All (ZIP)</strong>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-webp.zip">
                        <code>WebP.xcframework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-webpdecoder.zip">
                        <code>WebPDecoder.xcframework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-webpdemux.zip">
                        <code>WebPDemux.xcframework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-webpmux.zip">
                        <code>WebPMux.xcframework</code>
                    </a>
                </li>
            </ul>
        </td>
    </tr>
    <tr>
        <td><strong>macOS</strong></td>
        <td>OS X 10.9 and up.</td>
        <td>
            <ul>
                <li><code>x86_64</code></li>
            </ul>
        </td>
        <td>
            <ul>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-macos.zip">
                    <strong>Download All (ZIP)</strong>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-macos-webp.zip">
                    <code>WebP.xcframework</code>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-macos-webpdecoder.zip">
                    <code>WebPDecoder.xcframework</code>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-macos-webpdemux.zip">
                    <code>WebPDemux.xcframework</code>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-macos-webpmux.zip">
                    <code>WebPMux.xcframework</code>
                </a>
            </li>
            </ul>
        </td>
    </tr>
    <tr>
        <td><strong>tvOS</strong></td>
        <td>tvOS 9.0 and up.</td>
        <td>
            <ul>
                <li><code>arm64</code></li>
                <li><code>x86_64</code></li>
            </ul>
        </td>
        <td>
            <ul>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-tvos.zip">
                    <strong>Download All (ZIP)</strong>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-tvos-webp.zip">
                    <code>WebP.xcframework</code>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-tvos-webpdecoder.zip">
                    <code>WebPDecoder.xcframework</code>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-tvos-webpdemux.zip">
                    <code>WebPDemux.xcframework</code>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-tvos-webpmux.zip">
                    <code>WebPMux.xcframework</code>
                </a>
            </li>
            </ul>
        </td>
    </tr>
    <tr>
        <td><strong>watchOS</strong></td>
        <td>watchOS 2.0 and up.</td>
        <td>
            <ul>
                <li><code>arm64_32</code></li>
                <li><code>armv7k</code></li>
                <li><code>i386</code></li>
                <li><code>x86_64</code></li>
            </ul>
        </td>
        <td>
            <ul>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-watchos.zip">
                        <strong>Download All (ZIP)</strong>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-watchos-webp.zip">
                        <code>WebP.xcframework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-watchos-webpdecoder.zip">
                        <code>WebPDecoder.xcframework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-watchos-webpdemux.zip">
                        <code>WebPDemux.xcframework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-watchos-webpmux.zip">
                        <code>WebPMux.xcframework</code>
                    </a>
                </li>
            </ul>
        </td>
    </tr>
</table>

# Credits

Repository created and maintained by [Tim Oliver](http://twitter.com/TimOliverAU). WebP icon artwork by [Simo99](https://commons.wikimedia.org/wiki/User:Simo99) used under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). WebP is developed by [Google](http://about.google).

# License

All code in this repository is under the BSD-3-Clause License. Please see the [LICENSE](LICENSE) file for more information.

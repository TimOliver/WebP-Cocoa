<p align="center">
    <img src="https://github.com/TimOliver/WebP-Cocoa/raw/main/banner.png" width="731" alt="WebP-Cocoa Banner" />
</p>

[WebP](https://developers.google.com/speed/webp) is a modern image file format that provides amazing lossy and lossless compression fidelity. WebP is developed by Google who very kindly publishes the underlying library, [`libwepb` as open source software](https://chromium.googlesource.com/webm/libwebp/).

Google provides precompiled binaries of WebP for both iOS and macOS on [WebP's download page](https://developers.google.com/speed/webp/download). However, at the time of writing, their build pipeline has not yet been updated to support the more modern features of Apple's platforms, such as Swift module support, or architectural slices for Mac Catalyst.

Using Google's original iOS build script as a base, this repository uses GitHub Actions to automatically build and release precompiled WebP binaries for all of Apple's platforms. This includes support for watchOS and tvOS as well as support for Mac Catalyst via Apple's new `xcframework` format.

There are 4 separate frameworks available for each platform:

* **WebP**: Enables both encoding and decoding of WebP image files.
* **WebPDecoder**: Enables just the decoding of WebP image files.
* **WebPMux**: Enables manipulation of WebP container image features like color profile, metadata, animation.
* **WebPDemux**: Enables extraction of image and extended format data from WebP files.

# Installation Instructions

1. Download and extract the package for your platform and capabilities of choice.
2. Drag the `framework` folder into your Xcode project.
3. When prompted, make sure *Copy items if needed* is checked before proceeding.

# Download Frameworks

For fast access, the binaries are bundled up and provided in a variety of different ZIP archive combinations. Simply click any of the links below to begin downloading.

<table>
    <tr>
        <td colspan="4" align="center">
            <strong><a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework.zip">Download All Frameworks for All Platforms (ZIP)</a></strong>
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
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-ios-catalyst.zip">
                        <strong>Download All (ZIP)</strong>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-ios-catalyst-webp.zip">
                        <code>WebP.xcframework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-ios-catalyst-webpdecoder.zip">
                        <code>WebPDecoder.xcframework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-ios-catalyst-webpdemux.zip">
                        <code>WebPDemux.xcframework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-ios-catalyst-webpmux.zip">
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
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-ios.zip">
                        <strong>Download All (ZIP)</strong>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-ios-webp.zip">
                        <code>WebP.framework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-ios-webpdecoder.zip">
                        <code>WebPDecoder.framework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-ios-webpdemux.zip">
                        <code>WebPDemux.framework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-ios-webpmux.zip">
                        <code>WebPMux.framework</code>
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
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-macos.zip">
                    <strong>Download All (ZIP)</strong>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-macos-webp.zip">
                    <code>WebP.framework</code>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-macos-webpdecoder.zip">
                    <code>WebPDecoder.framework</code>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-macos-webpdemux.zip">
                    <code>WebPDemux.framework</code>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-macos-webpmux.zip">
                    <code>WebPMux.framework</code>
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
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-tvos.zip">
                    <strong>Download All (ZIP)</strong>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-tvos-webp.zip">
                    <code>WebP.framework</code>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-tvos-webpdecoder.zip">
                    <code>WebPDecoder.framework</code>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-tvos-webpdemux.zip">
                    <code>WebPDemux.framework</code>
                </a>
            </li>
            <li>
                <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-tvos-webpmux.zip">
                    <code>WebPMux.framework</code>
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
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-watchos.zip">
                        <strong>Download All (ZIP)</strong>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-watchos-webp.zip">
                        <code>WebP.framework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-watchos-webpdecoder.zip">
                        <code>WebPDecoder.framework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-watchos-webpdemux.zip">
                        <code>WebPDemux.framework</code>
                    </a>
                </li>
                <li>
                    <a href="https://github.com/TimOliver/WebP-Cocoa/releases/download/{tag_version}/libwebp-{tag_version}-framework-watchos-webpmux.zip">
                        <code>WebPMux.framework</code>
                    </a>
                </li>
            </ul>
        </td>
    </tr>
</table>

# Dependency Managers

If you would prefer to integrate `libwebp` via a dependency manager, the [`libwebp-Xcode`](https://github.com/SDWebImage/libwebp-Xcode) project managed by [SDWebImage](https://github.com/SDWebImage) already provides amazing support for all of the major dependency managers.

For convenience, the configuration settings for using `libwebp-Xcode`'s packages are as follows:

### CocoaPods
```ruby
pod 'libwebp'
```

### Carthage
```
github "SDWebImage/libwebp-Xcode"
```

### Swift Package Manager (SPM)
```swift
let package = Package(
    dependencies: [
        .package(url: "https://github.com/SDWebImage/libwebp-Xcode", from: "1.1.0")
    ],
    // ...
)
```

# Credits

Repository created and maintained by [Tim Oliver](http://twitter.com/TimOliverAU). WebP logo artwork by [Simo99](https://commons.wikimedia.org/wiki/User:Simo99) used under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). WebP is developed by [Google](http://about.google).

# License

All code in this repository is under the BSD-3-Clause License. Please see the [LICENSE](LICENSE) file for more information.

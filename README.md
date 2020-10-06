<p align="center">
  <img src="https://github.com/TimOliver/WebP-Cocoa/raw/main/banner.png" width="731" alt="WebP-Cocoa Banner" />
</p>

[WebP](https://developers.google.com/speed/webp) is a modern image file format that provides both amazing lossy and lossless compression fidelity. WebP is developed by Google and is freely distributed as open source software.

Google provides pre-built binaries of WebP for both iOS and macOS, however the build script has not been updated recently and as such, the binaries do not support either Swift modules, or Mac Catalyst.

Taking the official build script by Google and modifying it, this repository serves pre-built binaries for all of Apple's platforms, adding in tvOS and watchOS, as well as supporting Mac Catalyst via the new `xcframework` format.

There are 4 separate frameworks available for each platform:

* **WebP**: Both encoding and decoding capabilities of the WebP format.
* **WebPDecoder**: Just the decoding capabilities of the WebP format.
* **WebPMux**: Enables manipulation of WebP container images containing features like color profile, metadata, animation.
* **WebPDemux**: Enables extraction of image and extended format data from WebP files.

# Instructions

1. Download and extract the package for your platform and capabilities of choice.
2. Drag the `framework` folder into your Xcode project.
3. When prompted, make sure *Copy items if needed* is checked before proceeding.

# Packages
 
 For ultimate convenience, the pre-built frameworks have been packaged up into every combination of ZIP archives. Simply click one of the links below to begin downloading.
 
 [Download All Frameworks](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework.zip)
 
## iOS (Including Mac Catalyst)

**Architectures:** arm64, x86_64 (Mac Catalyst), x86_64 (iOS Simulator)<br/>
**Supported Versions:** iOS 11.0, macOS 10.15<br/>
**Technical Requirements:** Xcode 11 and up

* [All iOS Frameworks](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-catalyst.zip)
* [WebP.xcframework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-catalyst-webp.zip)
* [WebPDecoder.xcframework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-catalyst-webpdecoder.zip)
* [WebPDemux.xcframework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-catalyst-webpdemux.zip)
* [WebPMux.xcframework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-catalyst-webpmux.zip)

## iOS

**Architectures:** arm64, armv7, armv7s, i386, x86_64<br/>
**Supported Versions:** iOS 9.0 and up<br/>
**Technical Requirements:** Xcode 7 and up

* [All iOS Frameworks](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios.zip)
* [WebP.framework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-webp.zip)
* [WebPDecoder.framework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-webpdecoder.zip)
* [WebPDemux.framework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-webpdemux.zip)
* [WebPMux.framework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-ios-webpmux.zip)

## tvOS

**Architectures:** arm64, x86_64<br/>
**Supported Versions:** tvOS 9.0 and up<br/>
**Technical Requirements:** Xcode 7 and up

* [All tvOS Frameworks](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-tvos.zip)
* [WebP.framework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-tvos-webp.zip)
* [WebPDecoder.framework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-tvos-webpdecoder.zip)
* [WebPDemux.framework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-tvos-webpdemux.zip)
* [WebPMux.framework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-tvos-webpmux.zip)

## watchOS

**Architectures:** arm64_32, armv7k, i386, x86_64<br/>
**Supported Versions:** watchOS 2.0 and up<br/>
**Technical Requirements:** Xcode 7 and up

* [All watchOS Frameworks](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-watchos.zip)
* [WebP.framework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-watchos-webp.zip)
* [WebPDecoder.framework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-watchos-webpdecoder.zip)
* [WebPDemux.framework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-watchos-webpdemux.zip)
* [WebPMux.framework](https://github.com/TimOliver/WebP-Cocoa/releases/download/v1.1.0/libwebp-v1.1.0-framework-watchos-webpmux.zip)

# Credits

Repository created and maintained by [Tim Oliver](http://twitter.com/TimOliverAU). WebP icon artwork by [Simo99](https://commons.wikimedia.org/wiki/User:Simo99) used under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). WebP is developed by [Google](http://about.google).

# License

All code in this repository is under the BSD-3-Clause License. Please see the [LICENSE](LICENSE) file for more information.
import UIKit

#if WEBP_FULL
import WebP
import WebP.Decoder
import WebPMux
#else
import WebPDecoder
#endif
import WebPDemux

// These calls must compile and link in an actual iOS application. The CI build
// does not boot a simulator; the macOS artifact tests execute equivalent checks.
private func verifyWebP() {
    // Synthetic RGBA 2x2 fixture; see ../Fixtures/README.md.
    let webp: [UInt8] = [82, 73, 70, 70, 48, 0, 0, 0, 87, 69, 66, 80, 86, 80, 56, 76, 35, 0, 0, 0, 47, 1, 64, 0, 16, 31, 48, 255, 2, 130, 34, 255, 71, 219, 127, 129, 0, 193, 185, 115, 193, 141, 42, 65, 77, 219, 6, 44, 126, 147, 142, 136, 254, 199, 1, 0]
    let expected: [UInt8] = [255, 0, 0, 255, 0, 255, 0, 128,
                             0, 0, 255, 255, 255, 255, 255, 0]
    precondition(WebPGetDecoderVersion() > 0 && WebPGetDemuxVersion() > 0)
    webp.withUnsafeBufferPointer { bytes in
        var width: Int32 = 0
        var height: Int32 = 0
        guard let decoded = WebPDecodeRGBA(bytes.baseAddress, bytes.count, &width, &height) else {
            fatalError("iOS decoder returned nil")
        }
        defer { WebPFree(decoded) }
        precondition(width == 2 && height == 2)
        precondition(Array(UnsafeBufferPointer(start: decoded, count: 16)) == expected)
        var data = WebPData(bytes: bytes.baseAddress, size: bytes.count)
        guard let demux = WebPDemux(&data) else { fatalError("iOS demux returned nil") }
        defer { WebPDemuxDelete(demux) }
        precondition(WebPDemuxGetI(demux, WEBP_FF_FRAME_COUNT) == 1)
        precondition(WebPDemuxGetI(demux, WEBP_FF_CANVAS_WIDTH) == 2)
    }
#if WEBP_FULL
    precondition(WebPGetEncoderVersion() > 0 && WebPGetMuxVersion() > 0)
    let pixel: [UInt8] = [255, 0, 0, 255]
    pixel.withUnsafeBufferPointer { input in
        var encoded: UnsafeMutablePointer<UInt8>?
        let size = WebPEncodeLosslessRGBA(input.baseAddress, 1, 1, 4, &encoded)
        guard let encoded, size > 0 else { fatalError("iOS encoder returned nil") }
        WebPFree(encoded)
    }
    guard let mux = WebPMuxNew() else { fatalError("iOS mux returned nil") }
    WebPMuxDelete(mux)
#endif
}

@main
final class SmokeApp: UIResponder, UIApplicationDelegate {
    var window: UIWindow?

    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        verifyWebP()
        let window = UIWindow(frame: UIScreen.main.bounds)
        window.rootViewController = UIViewController()
        window.makeKeyAndVisible()
        self.window = window
        return true
    }
}

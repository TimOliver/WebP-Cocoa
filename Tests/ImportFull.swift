import WebP
import WebP.Decoder
import WebPDemux
import WebPMux

precondition(WebPGetEncoderVersion() > 0 && WebPGetDecoderVersion() > 0)
precondition(WebPGetMuxVersion() > 0 && WebPGetDemuxVersion() > 0)
let pixel: [UInt8] = [255, 0, 0, 255]
pixel.withUnsafeBufferPointer { input in
    var encoded: UnsafeMutablePointer<UInt8>?
    let size = WebPEncodeLosslessRGBA(input.baseAddress, 1, 1, 4, &encoded)
    guard let encoded, size > 0 else { fatalError("Swift encoder returned nil") }
    defer { WebPFree(encoded) }
    var width: Int32 = 0
    var height: Int32 = 0
    guard let decoded = WebPDecodeRGBA(encoded, size, &width, &height) else {
        fatalError("Swift full decoder returned nil")
    }
    defer { WebPFree(decoded) }
    precondition(width == 1 && height == 1)
    precondition(Array(UnsafeBufferPointer(start: decoded, count: 4)) == pixel)
}
guard let mux = WebPMuxNew() else { fatalError("Swift mux returned nil") }
WebPMuxDelete(mux)
print("Swift WebPFull: legacy Decoder import, link, encode and decode passed")

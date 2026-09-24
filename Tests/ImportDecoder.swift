import WebPDecoder
import WebPDemux

// Synthetic RGBA 2x2 fixture; see Fixtures/README.md.
let webp: [UInt8] = [82, 73, 70, 70, 48, 0, 0, 0, 87, 69, 66, 80, 86, 80, 56, 76, 35, 0, 0, 0, 47, 1, 64, 0, 16, 31, 48, 255, 2, 130, 34, 255, 71, 219, 127, 129, 0, 193, 185, 115, 193, 141, 42, 65, 77, 219, 6, 44, 126, 147, 142, 136, 254, 199, 1, 0]
let expected: [UInt8] = [255, 0, 0, 255, 0, 255, 0, 128,
                         0, 0, 255, 255, 255, 255, 255, 0]
precondition(WebPGetDecoderVersion() > 0 && WebPGetDemuxVersion() > 0)
webp.withUnsafeBufferPointer { bytes in
    var width: Int32 = 0
    var height: Int32 = 0
    guard let decoded = WebPDecodeRGBA(bytes.baseAddress, bytes.count, &width, &height) else {
        fatalError("Swift decoder returned nil")
    }
    defer { WebPFree(decoded) }
    precondition(width == 2 && height == 2)
    precondition(Array(UnsafeBufferPointer(start: decoded, count: 16)) == expected)
    var data = WebPData(bytes: bytes.baseAddress, size: bytes.count)
    guard let demux = WebPDemux(&data) else { fatalError("Swift demux returned nil") }
    defer { WebPDemuxDelete(demux) }
    precondition(WebPDemuxGetI(demux, WEBP_FF_FRAME_COUNT) == 1)
    precondition(WebPDemuxGetI(demux, WEBP_FF_CANVAS_WIDTH) == 2)
}
print("Swift WebPDecoding: import, link, decode and demux passed")

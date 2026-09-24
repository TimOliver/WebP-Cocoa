#if WEBP_DECODER_ONLY
import WebPDecoder
#else
import WebP
import WebP.Decoder
#endif

precondition(WebPGetDecoderVersion() > 0)
#if !WEBP_DECODER_ONLY
precondition(WebPGetEncoderVersion() > 0)
#endif
// Pull in the real decoder as well as the version function, without any other
// WebP module's headers or libraries being present on the search/link paths.
let malformed: [UInt8] = [0, 1, 2, 3]
malformed.withUnsafeBufferPointer { bytes in
    var width: Int32 = 0
    var height: Int32 = 0
    precondition(WebPDecodeRGBA(bytes.baseAddress, bytes.count, &width, &height) == nil)
}
print("Standalone Swift module import/link passed")

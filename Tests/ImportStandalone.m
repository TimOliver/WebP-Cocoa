#if WEBP_DECODER_ONLY
@import WebPDecoder;
#else
@import WebP;
@import WebP.Decoder;
#endif
int main(void) {
    const unsigned char malformed[] = {0, 1, 2, 3};
    int width, height;
    if (WebPDecodeRGBA(malformed, sizeof(malformed), &width, &height) != 0) return 1;
#if !WEBP_DECODER_ONLY
    if (WebPGetEncoderVersion() == 0) return 1;
#endif
    return WebPGetDecoderVersion() == 0;
}

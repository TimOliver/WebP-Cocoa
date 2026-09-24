#include <webp/decode.h>
#include <webp/demux.h>
#include <webp/encode.h>
#include <webp/mux.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #condition); \
        exit(1); \
    } \
} while (0)

int main(void) {
    CHECK(WebPGetEncoderVersion() == EXPECTED_WEBP_VERSION);
    CHECK(WebPGetMuxVersion() == EXPECTED_WEBP_VERSION);
    uint8_t pixels[4 * 4 * 4];
    for (int p = 0; p < 16; ++p) {
        pixels[4 * p] = (uint8_t)(p * 16);
        pixels[4 * p + 1] = (uint8_t)(255 - p * 16);
        pixels[4 * p + 2] = (uint8_t)(p % 2 ? 0 : 255);
        pixels[4 * p + 3] = 255;
    }
    uint8_t *encoded;
    size_t size = WebPEncodeLosslessRGBA(pixels, 4, 4, 16, &encoded);
    CHECK(size > 0 && encoded != NULL);
    int width, height;
    uint8_t *decoded = WebPDecodeRGBA(encoded, size, &width, &height);
    CHECK(decoded != NULL && width == 4 && height == 4);
    CHECK(memcmp(pixels, decoded, sizeof(pixels)) == 0);
    WebPFree(decoded);

    WebPMux *mux = WebPMuxNew();
    CHECK(mux != NULL);
    WebPData image = {encoded, size};
    CHECK(WebPMuxSetImage(mux, &image, 1) == WEBP_MUX_OK);
    const uint8_t xmp[] = "<x:xmpmeta xmlns:x='adobe:ns:meta/'>webp-cocoa</x:xmpmeta>";
    WebPData metadata = {xmp, sizeof(xmp) - 1};
    CHECK(WebPMuxSetChunk(mux, "XMP ", &metadata, 1) == WEBP_MUX_OK);
    WebPData assembled = {0};
    CHECK(WebPMuxAssemble(mux, &assembled) == WEBP_MUX_OK);
    WebPDemuxer *demux = WebPDemux(&assembled);
    CHECK(demux != NULL);
    WebPChunkIterator chunk;
    CHECK(WebPDemuxGetChunk(demux, "XMP ", 1, &chunk));
    CHECK(chunk.chunk.size == metadata.size);
    CHECK(memcmp(chunk.chunk.bytes, metadata.bytes, metadata.size) == 0);
    WebPDemuxReleaseChunkIterator(&chunk);
    WebPDemuxDelete(demux);
    WebPMuxDelete(mux);
    WebPDataClear(&assembled);
    WebPFree(encoded);

    /* This path needs the merged libsharpyuv objects even with static linking. */
    WebPConfig config;
    CHECK(WebPConfigInit(&config));
    config.quality = 90;
    config.use_sharp_yuv = 1;
    CHECK(WebPValidateConfig(&config));
    WebPPicture picture;
    CHECK(WebPPictureInit(&picture));
    picture.width = 4;
    picture.height = 4;
    picture.use_argb = 1;
    CHECK(WebPPictureImportRGBA(&picture, pixels, 16));
    WebPMemoryWriter writer;
    WebPMemoryWriterInit(&writer);
    picture.writer = WebPMemoryWrite;
    picture.custom_ptr = &writer;
    CHECK(WebPEncode(&config, &picture));
    CHECK(writer.size > 0);
    decoded = WebPDecodeRGBA(writer.mem, writer.size, &width, &height);
    CHECK(decoded != NULL && width == 4 && height == 4);
    WebPFree(decoded);
    WebPPictureFree(&picture);
    WebPMemoryWriterClear(&writer);
    puts("Full encoder/mux: lossless round trip, XMP mux/demux and SharpYUV encode passed");
    return 0;
}

#include <webp/decode.h>
#include <webp/demux.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CHECK(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #condition); \
        exit(1); \
    } \
} while (0)

static const uint8_t expected_rgba[] = {
    255, 0, 0, 255, 0, 255, 0, 128,
    0, 0, 255, 255, 255, 255, 255, 0
};
static const uint8_t expected_exif[] = {
    'E', 'x', 'i', 'f', 0, 0, 'I', 'I', 42, 0, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0
};

static WebPData read_fixture(const char *directory, const char *name) {
    char path[4096];
    CHECK(snprintf(path, sizeof(path), "%s/%s", directory, name) < (int)sizeof(path));
    FILE *file = fopen(path, "rb");
    CHECK(file != NULL);
    CHECK(fseek(file, 0, SEEK_END) == 0);
    long length = ftell(file);
    CHECK(length > 0);
    rewind(file);
    uint8_t *bytes = malloc((size_t)length);
    CHECK(bytes != NULL);
    CHECK(fread(bytes, 1, (size_t)length, file) == (size_t)length);
    CHECK(fclose(file) == 0);
    WebPData data = {bytes, (size_t)length};
    return data;
}

static void check_lossless(const char *directory) {
    WebPData data = read_fixture(directory, "lossless.webp");
    int width = 0, height = 0;
    CHECK(WebPGetInfo(data.bytes, data.size, &width, &height));
    CHECK(width == 2 && height == 2);
    WebPBitstreamFeatures features;
    CHECK(WebPGetFeatures(data.bytes, data.size, &features) == VP8_STATUS_OK);
    CHECK(features.format == 2 && features.has_alpha == 1);
    uint8_t *pixels = WebPDecodeRGBA(data.bytes, data.size, &width, &height);
    CHECK(pixels != NULL);
    CHECK(memcmp(pixels, expected_rgba, sizeof(expected_rgba)) == 0);
    WebPFree(pixels);
    uint8_t into[16];
    CHECK(WebPDecodeRGBAInto(data.bytes, data.size, into, sizeof(into), 8) == into);
    CHECK(memcmp(into, expected_rgba, sizeof(into)) == 0);
    CHECK(WebPDecodeRGBAInto(data.bytes, data.size, into, sizeof(into) - 1, 8) == NULL);
    /* Exercise the streaming entry points commonly used by image loaders. */
    WebPIDecoder *incremental = WebPINewRGB(MODE_RGBA, into, sizeof(into), 8);
    CHECK(incremental != NULL);
    CHECK(WebPIAppend(incremental, data.bytes, 8) == VP8_STATUS_SUSPENDED);
    CHECK(WebPIAppend(incremental, data.bytes + 8, data.size - 8) == VP8_STATUS_OK);
    CHECK(memcmp(into, expected_rgba, sizeof(into)) == 0);
    WebPIDelete(incremental);
    for (size_t length = 0; length < 20; ++length) {
        CHECK(WebPDecodeRGBA(data.bytes, length, &width, &height) == NULL);
    }
    uint8_t invalid[] = {'R', 'I', 'F', 'F', 4, 0, 0, 0, 'N', 'O', 'P', 'E'};
    CHECK(WebPGetInfo(invalid, sizeof(invalid), &width, &height) == 0);
    CHECK(WebPDecodeRGBA(invalid, sizeof(invalid), &width, &height) == NULL);
    WebPData malformed = {invalid, sizeof(invalid)};
    CHECK(WebPDemux(&malformed) == NULL);
    free((void *)data.bytes);
}

static void check_lossy(const char *directory) {
    WebPData data = read_fixture(directory, "lossy.webp");
    WebPBitstreamFeatures features;
    CHECK(WebPGetFeatures(data.bytes, data.size, &features) == VP8_STATUS_OK);
    CHECK(features.format == 1 && features.has_alpha == 0);
    int width = 0, height = 0;
    uint8_t *pixels = WebPDecodeRGBA(data.bytes, data.size, &width, &height);
    CHECK(pixels != NULL && width == 4 && height == 4);
    for (int pixel = 0; pixel < 16; ++pixel) {
        for (int channel = 0; channel < 3; ++channel) CHECK(pixels[4 * pixel + channel] <= 3);
        CHECK(pixels[4 * pixel + 3] == 255);
    }
    WebPFree(pixels);
    free((void *)data.bytes);
}

static void check_animation(const char *directory) {
    WebPData data = read_fixture(directory, "animation.webp");
    WebPDemuxer *demux = WebPDemux(&data);
    CHECK(demux != NULL);
    CHECK(WebPDemuxGetI(demux, WEBP_FF_CANVAS_WIDTH) == 2);
    CHECK(WebPDemuxGetI(demux, WEBP_FF_CANVAS_HEIGHT) == 2);
    CHECK(WebPDemuxGetI(demux, WEBP_FF_FRAME_COUNT) == 2);
    CHECK(WebPDemuxGetI(demux, WEBP_FF_LOOP_COUNT) == 3);
    CHECK((WebPDemuxGetI(demux, WEBP_FF_FORMAT_FLAGS) & (ANIMATION_FLAG | EXIF_FLAG)) ==
          (ANIMATION_FLAG | EXIF_FLAG));
    WebPIterator frame;
    CHECK(WebPDemuxGetFrame(demux, 1, &frame));
    int count = 0;
    do {
        CHECK(frame.complete && frame.width == 2 && frame.height == 2);
        CHECK(frame.duration == (count == 0 ? 40 : 60));
        int width, height;
        uint8_t *pixels = WebPDecodeRGBA(frame.fragment.bytes, frame.fragment.size, &width, &height);
        CHECK(pixels != NULL && width == 2 && height == 2);
        for (int p = 0; p < 4; ++p) {
            CHECK(pixels[p * 4] == (count == 0 ? 255 : 0));
            CHECK(pixels[p * 4 + 1] == (count == 0 ? 0 : 255));
            CHECK(pixels[p * 4 + 2] == 0 && pixels[p * 4 + 3] == 255);
        }
        WebPFree(pixels);
        ++count;
    } while (WebPDemuxNextFrame(&frame));
    CHECK(count == 2);
    CHECK(WebPDemuxPrevFrame(&frame) && frame.frame_num == 1);
    WebPDemuxReleaseIterator(&frame);
    WebPChunkIterator chunk;
    CHECK(WebPDemuxGetChunk(demux, "EXIF", 1, &chunk));
    CHECK(chunk.chunk.size == sizeof(expected_exif));
    CHECK(memcmp(chunk.chunk.bytes, expected_exif, sizeof(expected_exif)) == 0);
    CHECK(!WebPDemuxNextChunk(&chunk));
    WebPDemuxReleaseChunkIterator(&chunk);
    WebPDemuxDelete(demux);

    WebPAnimDecoderOptions options;
    CHECK(WebPAnimDecoderOptionsInit(&options));
    options.color_mode = MODE_RGBA;
    options.use_threads = 1;
    WebPAnimDecoder *animation = WebPAnimDecoderNew(&data, &options);
    CHECK(animation != NULL);
    WebPAnimInfo info;
    CHECK(WebPAnimDecoderGetInfo(animation, &info));
    CHECK(info.canvas_width == 2 && info.canvas_height == 2 && info.frame_count == 2 && info.loop_count == 3);
    for (int index = 0; index < 2; ++index) {
        uint8_t *pixels;
        int timestamp;
        CHECK(WebPAnimDecoderHasMoreFrames(animation));
        CHECK(WebPAnimDecoderGetNext(animation, &pixels, &timestamp));
        CHECK(timestamp == (index == 0 ? 40 : 100));
        for (int p = 0; p < 4; ++p) {
            CHECK(pixels[p * 4] == (index == 0 ? 255 : 0));
            CHECK(pixels[p * 4 + 1] == (index == 0 ? 0 : 255));
            CHECK(pixels[p * 4 + 2] == 0 && pixels[p * 4 + 3] == 255);
        }
    }
    CHECK(!WebPAnimDecoderHasMoreFrames(animation));
    WebPAnimDecoderReset(animation);
    CHECK(WebPAnimDecoderHasMoreFrames(animation));
    WebPAnimDecoderDelete(animation);
    free((void *)data.bytes);
}

int main(int argc, char **argv) {
    CHECK(argc == 2);
    CHECK(WebPGetDecoderVersion() == EXPECTED_WEBP_VERSION);
    CHECK(WebPGetDemuxVersion() == EXPECTED_WEBP_VERSION);
    check_lossless(argv[1]);
    check_lossy(argv[1]);
    check_animation(argv[1]);
    puts("Decoder/demux: lossy, lossless, alpha, incremental, malformed, animation and metadata passed");
    return 0;
}

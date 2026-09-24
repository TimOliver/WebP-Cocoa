@import WebPDecoder;
@import WebPDemux;

int main(void) {
    WebPAnimDecoderOptions options;
    if (!WebPAnimDecoderOptionsInit(&options)) return 1;
    WebPData data = {0};
    WebPDemuxer *demux = WebPDemux(&data);
    WebPDemuxDelete(demux);
    WebPAnimDecoder *animation = WebPAnimDecoderNew(&data, &options);
    WebPAnimDecoderDelete(animation);
    return WebPGetDecoderVersion() == 0 || WebPGetDemuxVersion() == 0;
}

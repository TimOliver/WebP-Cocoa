@import WebP;
@import WebP.Decoder;  // Historical client spelling remains supported.
@import WebPDemux;
@import WebPMux;

int main(void) {
    WebPConfig config;
    if (!WebPConfigInit(&config)) return 1;
    WebPMux *mux = WebPMuxNew();
    WebPMuxDelete(mux);
    return WebPGetDecoderVersion() == 0 || WebPGetEncoderVersion() == 0 ||
           WebPGetDemuxVersion() == 0 || WebPGetMuxVersion() == 0;
}

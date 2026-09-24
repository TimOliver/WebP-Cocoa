/* Both upstream include styles are supported, without a custom search map. */
#include <decode.h>
#include <webp/decode.h>
#include <demux.h>
#include <webp/demux.h>
#if WEBP_FULL
#include <encode.h>
#include <webp/encode.h>
#include <mux.h>
#include <webp/mux.h>
#endif
int main(void) {
#if WEBP_FULL
    if (WebPGetEncoderVersion() == 0 || WebPGetMuxVersion() == 0) return 1;
#endif
    return WebPGetDecoderVersion() == 0 || WebPGetDemuxVersion() == 0;
}

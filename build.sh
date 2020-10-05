#!/bin/bash

# BSD 3-Clause License
# 
# Copyright (c) 2019-2020, Google, Tim Oliver
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

set -e

# Perform all operations in a sub-directory
mkdir -p build
cd build

# Global Valuess
readonly TAG_VERSION="v1.1.0"
readonly WEBP_GIT_URL="https://chromium.googlesource.com/webm/libwebp"
readonly WEBP_SRC_DIR="libwebp"
readonly TOPDIR=$(pwd)

# Extract Xcode version.
readonly XCODE=$(xcodebuild -version | grep Xcode | cut -d " " -f2)
if [[ -z "${XCODE}" ]]; then
  echo "Xcode not available"
  exit 1
fi

# Global Static 
readonly DEVELOPER=$(xcode-select --print-path)
readonly PLATFORMSROOT="${DEVELOPER}/Platforms"
readonly OLDPATH=${PATH}
readonly EXTRA_CFLAGS="-fembed-bitcode"
readonly LIPO=$(xcrun -sdk iphoneos${SDK} -find lipo)

usage() {
cat <<EOF
Usage: sh $0 command [argument]

command:
  build:            builds all frameworks
  ios:              builds iOS framework
  ios-catalyst:     builds iOS xcframework (With Mac Catalyst)
  tvos:             builds tvOS framework
  macos:            builds macOS framework
  watchos:          builds watchOS framework
  package-each:      packages all built frameworks each into a separate ZIP file per framework
  package-platform: packages all built frameworks into separate ZIP files per platform
  package-all:      packages all built frameworks into one single ZIP file
EOF
}

# Clone a fresh copy of the libwep source code
clone_repo() {
    # Clone a copy of the WebP source code
    if [[ ! -d ${WEBP_SRC_DIR} ]]; then
        git clone --depth 1 --branch ${TAG_VERSION} ${WEBP_GIT_URL}
    fi

    # Move to the directory
    cd ${WEBP_SRC_DIR}
}

build_ios() {
  # Query for the SDK version installed
  SDK=$(xcodebuild -showsdks \
    | grep iphoneos | sort | tail -n 1 | awk '{print substr($NF, 9)}'
  )

  # Check to make sure we found the SDK version
  if [[ -z "${SDK}" ]]; then
    echo "iOS SDK not available"
    exit 1
  else 
    echo "iOS SDK Version ${SDK}"
  fi

  BUILDDIR="$(pwd)/iosbuild"

  # Build all of the iOS native device slices
  build_common
  build_slice "armv7" "armv7-apple-ios" "arm-apple-darwin" "iphoneos" "-miphoneos-version-min=9.0"
  build_slice "armv7s" "armv7s-apple-ios" "arm-apple-darwin" "iphoneos" "-miphoneos-version-min=9.0"
  build_slice "arm64" "aarch64-apple-ios" "arm-apple-darwin" "iphoneos" "-miphoneos-version-min=9.0"
  build_slice "x86_64" "x86_64-apple-ios" "x86_64-apple-darwin" "iphonesimulator" "-miphoneos-version-min=9.0"
  build_slice "i386" "i386-apple-ios" "i386-apple-darwin" "iphonesimulator" "-miphoneos-version-min=9.0"
  make_frameworks "iOS"
}

build_ios_catalyst() {
  # Query for the SDK version installed
  SDK=$(xcodebuild -showsdks \
    | grep iphoneos | sort | tail -n 1 | awk '{print substr($NF, 9)}'
  )

  # Check to make sure we found the SDK version
  if [[ -z "${SDK}" ]]; then
    echo "iOS SDK not available"
    exit 1
  else 
    echo "iOS SDK Version ${SDK}"
  fi

  BUILDDIR="$(pwd)/iosbuild-catalyst"

  # Build all of the iOS native device slices
  build_common
  build_slice "x86_64" "x86_64-apple-ios13.0-macabi" "x86_64-apple-darwin" "macosx" "-miphoneos-version-min=11.0" 
  build_slice "arm64" "aarch64-apple-ios" "arm-apple-darwin" "iphoneos" "-miphoneos-version-min=11.0"
  build_slice "x86_64" "x86_64-apple-ios" "x86_64-apple-darwin" "iphonesimulator" "-miphoneos-version-min=11.0"
  make_xcframeworks "iOS-MacCatalyst"
}

build_tvos() {
  # Query for the SDK version installed
  SDK=$(xcodebuild -showsdks \
    | grep appletvos | sort | tail -n 1 | awk '{print substr($NF, 10)}'
  )

  # Check to make sure we found the SDK version
  if [[ -z "${SDK}" ]]; then
    echo "tvOS SDK not available"
    exit 1
  else 
    echo "tvOS SDK Version ${SDK}"
  fi

  BUILDDIR="$(pwd)/tvosbuild"

  build_common
  build_slice "arm64" "aarch64-apple-tvos" "arm-apple-darwin" "appletvos" "-mtvos-version-min=9.0"
  build_slice "x86_64" "x86_64-apple-tvos" "x86_64-apple-darwin" "appletvsimulator" "-mtvos-version-min=9.0"
  make_frameworks "tvOS"
}

build_macos() {
  # Query for the SDK version installed
  SDK=$(xcodebuild -showsdks \
    | grep macosx | sort | tail -n 1 | awk '{print substr($NF, 7)}'
  )

  # Check to make sure we found the SDK version
  if [[ -z "${SDK}" ]]; then
    echo "macOS SDK not available"
    exit 1
  else 
    echo "macOS SDK Version ${SDK}"
  fi

  BUILDDIR="$(pwd)/macosbuild"

  build_common
  # build_slice "arm64" "arm64-apple-macos11" "arm-apple-darwin" "MacOSX" ""
  build_slice "x86_64" "x86_64-apple-macos10.12" "x86_64-apple-darwin" "macosx" "-mmacosx-version-min=10.12"
  make_frameworks "macOS"
}

build_watchos() {
  # Query for the SDK version installed
  SDK=$(xcodebuild -showsdks \
    | grep watchos | sort | tail -n 1 | awk '{print substr($NF, 8)}'
  )

  # Check to make sure we found the SDK version
  if [[ -z "${SDK}" ]]; then
    echo "watchOS SDK not available"
    exit 1
  else 
    echo "watchOS SDK Version ${SDK}"
  fi

  BUILDDIR="$(pwd)/watchosbuild"

  build_common
  build_slice "arm64_32" "arm64_32-apple-watchos" "arm-apple-darwin" "watchos" "-mwatchos-version-min=2.0"
  build_slice "armv7k" "armv7k-apple-watchos" "arm-apple-darwin" "watchos" "-mwatchos-version-min=2.0"
  build_slice "x86_64" "x86_64-apple-watchos" "x86_64-apple-darwin" "watchsimulator" "-mwatchos-version-min=2.0"
  build_slice "i386" "i386-apple-watchos" "i386-apple-darwin" "watchsimulator" "-mwatchos-version-min=2.0"
  make_frameworks "watchOS"
}

# Perform common set-up/reset between builds
build_common() {
  SRCDIR=$(dirname $0)

  # Remove previous build folders
  rm -rf ${BUILDDIR}
  mkdir -p ${BUILDDIR}

  # Reset the lists of built binaries
  LIBLIST=''
  DECLIBLIST=''
  MUXLIBLIST=''
  DEMUXLIBLIST=''

  # Configure build settings
    if [[ ! -e ${SRCDIR}/configure ]]; then
      if ! (cd ${SRCDIR} && sh autogen.sh); then
        cat <<EOT
Error creating configure script!
This script requires the autoconf/automake and libtool to build. MacPorts can
be used to obtain these:
http://www.macports.org/install.php
EOT
        exit 1
      fi
    fi
}

build_slice() {
  ARCH=$1
  TARGET=$2
  HOST=$3
  PLATFORM=$4
  VERSION=$5
  
  ROOTDIR="${BUILDDIR}/${PLATFORM}-${ARCH}"
  mkdir -p "${ROOTDIR}"
  
  DEVROOT="${DEVELOPER}/Toolchains/XcodeDefault.xctoolchain"
  SDKROOT=`xcrun -sdk ${PLATFORM} --show-sdk-path`
  CFLAGS=" -arch ${ARCH} -pipe -isysroot ${SDKROOT} -O3 -DNDEBUG -target ${TARGET}"
  CFLAGS+=" ${VERSION} ${EXTRA_CFLAGS}"

  # Add --disable-libwebpdemux \ to disable demux
  set -x
  export PATH="${DEVROOT}/usr/bin:${OLDPATH}"
  ${SRCDIR}/configure --host=${HOST} --prefix=${ROOTDIR} \
    --build=$(${SRCDIR}/config.guess) \
    --disable-shared --enable-static \
    --enable-libwebpdecoder --enable-swap-16bit-csp \
    --enable-libwebpmux \
    CFLAGS="${CFLAGS}"
  set +x

  # Run make only in the src/ directory to create libwebp.a/libwebpdecoder.a
  cd src/
  make V=0
  make install

  # Capture the locations of all of the built binaries
  LIBLIST+=" ${ROOTDIR}/lib/libwebp.a"
  DECLIBLIST+=" ${ROOTDIR}/lib/libwebpdecoder.a"
  MUXLIBLIST+=" ${ROOTDIR}/lib/libwebpmux.a"
  DEMUXLIBLIST+=" ${ROOTDIR}/lib/libwebpdemux.a"

  make clean
  cd ..

  export PATH=${OLDPATH}
}

make_frameworks() {

  # Make WebP.xcframework
  echo "LIBLIST = ${LIBLIST}"
  TARGETDIR=${TOPDIR}/$1/WebP.framework
  rm -rf ${TARGETDIR}
  mkdir -p ${TARGETDIR}/Headers/
  mkdir -p ${TARGETDIR}/Modules/
  cp -a ${SRCDIR}/src/webp/{decode,encode,types}.h ${TARGETDIR}/Headers/
cat <<EOT >> ${TARGETDIR}/Modules/module.modulemap
framework module WebP [system] {
  header "decode.h"
  header "encode.h"
  header "types.h"
  export *
}
EOT
  ${LIPO} -create ${LIBLIST} -output ${TARGETDIR}/WebP

  # Make WebPDecoder.xcframework
  echo "DECLIBLIST = ${DECLIBLIST}"
  TARGETDIR=${TOPDIR}/$1/WebPDecoder.framework
  rm -rf ${TARGETDIR}
  mkdir -p ${TARGETDIR}/Headers/
  mkdir -p ${TARGETDIR}/Modules/
  cp -a ${SRCDIR}/src/webp/{decode,types}.h ${TARGETDIR}/Headers/
cat <<EOT >> ${TARGETDIR}/Modules/module.modulemap
framework module WebPDecoder [system] {
  header "decode.h"
  header "types.h"
  export *
}
EOT
  ${LIPO} -create ${LIBLIST} -output ${TARGETDIR}/WebPDecoder

  # Make WebPMux.xcframework
  echo "MUXLIBLIST = ${MUXLIBLIST}"
  TARGETDIR=${TOPDIR}/$1/WebPMux.framework
  mkdir -p ${TARGETDIR}/Headers/
  mkdir -p ${TARGETDIR}/Modules/
  cp -a ${SRCDIR}/src/webp/{types,mux,mux_types}.h ${TARGETDIR}/Headers/
cat <<EOT >> ${TARGETDIR}/Modules/module.modulemap
framework module WebPMux [system] {
  header "mux.h"
  header "mux_types.h"
  header "types.h"
  export *
}
EOT
  ${LIPO} -create ${MUXLIBLIST} -output ${TARGETDIR}/WebPMux

  # Make WebPDemux.xcframework
  echo "DEMUXLIBLIST = ${DEMUXLIBLIST}"
  TARGETDIR=${TOPDIR}/$1/WebPDemux.framework
  mkdir -p ${TARGETDIR}/Headers/
  mkdir -p ${TARGETDIR}/Modules/
  cp -a ${SRCDIR}/src/webp/{decode,types,mux_types,demux}.h ${TARGETDIR}/Headers/
cat <<EOT >> ${TARGETDIR}/Modules/module.modulemap
framework module WebPDemux [system] {
  header "decode.h"
  header "mux_types.h"
  header "types.h"
  header "demux.h"
  export *
}
EOT
  ${LIPO} -create ${DEMUXLIBLIST} -output ${TARGETDIR}/WebPDemux
}

make_xcframeworks() {
  TARGETDIR=${TOPDIR}/$1

  # Make WebP.xcframework
  echo "LIBLIST = ${LIBLIST}"
  rm -rf ${TARGETDIR}/WebP.xcframework
  mkdir -p ${TARGETDIR}/Headers/
cat <<EOT >> ${TARGETDIR}/Headers/module.modulemap
module WebP [system] {
  header "decode.h"
  header "encode.h"
  header "types.h"

  export *
}
EOT
  LIBRARIES=''
  for LIBRARY in ${LIBLIST}; do
    LIBRARIES+="-library ${LIBRARY} -headers ${TARGETDIR}/Headers "
  done
  echo ${LIBRARIES}
  cp -a ${SRCDIR}/src/webp/{decode,encode,types}.h ${TARGETDIR}/Headers/
  xcodebuild -create-xcframework ${LIBRARIES} \
              -output ${TARGETDIR}/WebP.xcframework
  rm -rf ${TARGETDIR}/Headers

  # Make WebPDecoder.xcframework
  echo "DECLIBLIST = ${DECLIBLIST}"
  rm -rf ${TARGETDIR}/WebPDecoder.xcframework
  mkdir -p ${TARGETDIR}/Headers/
cat <<EOT >> ${TARGETDIR}/Headers/module.modulemap
module WebPDecoder [system] {
  header "decode.h"
  header "types.h"

  export *
}
EOT
  LIBRARIES=''
  for LIBRARY in ${DECLIBLIST}; do
    LIBRARIES+="-library ${LIBRARY} -headers ${TARGETDIR}/Headers "
  done
  cp -a ${SRCDIR}/src/webp/{decode,types}.h ${TARGETDIR}/Headers/
  xcodebuild -create-xcframework ${LIBRARIES} \
              -output ${TARGETDIR}/WebPDecoder.xcframework
  rm -rf ${TARGETDIR}/Headers

  # Make WebPMux.xcframework
  echo "MUXLIBLIST = ${MUXLIBLIST}"
  rm -rf ${TARGETDIR}/WebPMux.xcframework
  mkdir -p ${TARGETDIR}/Headers/
cat <<EOT >> ${TARGETDIR}/Headers/module.modulemap
module WebPMux [system] {
  header "mux.h"
  header "mux_types.h"
  header "types.h"

  export *
}
EOT
  LIBRARIES=''
  for LIBRARY in ${MUXLIBLIST}; do
    LIBRARIES+="-library ${LIBRARY} -headers ${TARGETDIR}/Headers "
  done
  cp -a ${SRCDIR}/src/webp/{types,mux,mux_types}.h ${TARGETDIR}/Headers/
  xcodebuild -create-xcframework ${LIBRARIES} \
              -output ${TARGETDIR}/WebPMux.xcframework
  rm -rf ${TARGETDIR}/Headers

  # Make WebPDemux.xcframework
  echo "DEMUXLIBLIST = ${DEMUXLIBLIST}"
  rm -rf ${TARGETDIR}/WebPDemux.xcframework
  mkdir -p ${TARGETDIR}/Headers/
cat <<EOT >> ${TARGETDIR}/Headers/module.modulemap
module WebPDemux [system] {
  header "decode.h"
  header "mux_types.h"
  header "types.h"
  header "demux.h"

  export *
}
EOT
  LIBRARIES=''
  for LIBRARY in ${DEMUXLIBLIST}; do
    LIBRARIES+="-library ${LIBRARY} -headers ${TARGETDIR}/Headers "
  done
  cp -a ${SRCDIR}/src/webp/{decode,types,mux_types,demux}.h ${TARGETDIR}/Headers/
  xcodebuild -create-xcframework ${LIBRARIES} \
              -output ${TARGETDIR}/WebPDemux.xcframework
  rm -rf ${TARGETDIR}/Headers
}

package_framework_platform() {
  FRAMEWORK_NAME=$1
  DESTINATION_NAME=$2

  # Check there is a valid build folder
  if [[ ! -d ${FRAMEWORK_NAME} ]]; then
    return
  fi

  # Define the build folder name and delete if already there
  ZIP_FILENAME="libwebp-${TAG_VERSION}-framework-${DESTINATION_NAME}"
  if [[ -d ${ZIP_FILENAME} ]]; then
    rm -rf ${ZIP_FILENAME}
  fi

  # Make a directory with that name and copy the framework folder in there
  mkdir -p ${ZIP_FILENAME}
  rsync -av --exclude=".*" ${FRAMEWORK_NAME}/. ${ZIP_FILENAME}

  # Generate the ZIP file
  if [[ -d "${ZIP_FILENAME}.zip" ]]; then
    rm -rf "${ZIP_FILENAME}.zip"
  fi
  zip -r "${ZIP_FILENAME}.zip" ${ZIP_FILENAME}

  # Delete the folder copy
  rm -rf ${ZIP_FILENAME}
}

package_all_frameworks() {
  PLATFORMS="iOS iOS-MacCatalyst tvOS watchOS macOS"
  ZIP_FILENAME="libwebp-${TAG_VERSION}-framework"

  echo ${#PLATFORMS}

  # Make a directory to copy all of the frameworks into
  mkdir -p ${ZIP_FILENAME}

  # Copy all framework folders
  for PLATFORM in ${PLATFORMS}; do
    if [[ ! -d ${PLATFORM} ]]; then
      continue
    fi

    rsync -av --exclude=".*" ${PLATFORM} ${ZIP_FILENAME}
  done

  # Generate the ZIP file
  if [[ -d "${ZIP_FILENAME}.zip" ]]; then
    rm -rf "${ZIP_FILENAME}.zip"
  fi
  zip -r "${ZIP_FILENAME}.zip" ${ZIP_FILENAME}

  # Delete the folder copy
  rm -rf ${ZIP_FILENAME}
}

package_each_framework() {
  PLATFORM_NAME=$1
  ZIP_PLATFORM=$2
  FRAMEWORK_NAME=$3
  ZIP_FRAMEWORK=$4

  ZIP_FILENAME="libwebp-${TAG_VERSION}-framework-${ZIP_PLATFORM}-${ZIP_FRAMEWORK}"
  FRAMEWORK_PATH="${PLATFORM_NAME}/${FRAMEWORK_NAME}"

  # Exit out if there's no matching framework to ZIP
  if [[ ! -d ${FRAMEWORK_PATH} ]]; then
    return
  fi

  # Make a directory to copy all of the frameworks into
  mkdir -p ${ZIP_FILENAME}

  # Copy the framework to the folder
  rsync -av --exclude=".*" ${FRAMEWORK_PATH} ${ZIP_FILENAME}

  # Generate the ZIP file
  if [[ -d "${ZIP_FILENAME}.zip" ]]; then
    rm -rf "${ZIP_FILENAME}.zip"
  fi
  zip -r "${ZIP_FILENAME}.zip" ${ZIP_FILENAME}

  # Delete the folder copy
  rm -rf ${ZIP_FILENAME}
}

# Commands
COMMAND="$1"
case "$COMMAND" in

      "build")
        clone_repo
        build_ios
        build_ios_catalyst
        build_tvos
        build_macos
        build_watchos
        exit 0
        ;;

    "ios")
        clone_repo
        build_ios
        exit 0
        ;;

    "ios-catalyst")
        clone_repo
        build_ios_catalyst
        exit 0
        ;;
    
    "tvos")
        clone_repo
        build_tvos
        exit 0
        ;;

    "macos")
        clone_repo
        build_macos
        exit 0
        ;;

    "watchos")
        clone_repo
        build_watchos
        exit 0
        ;;

    "package-platform")
      package_framework_platform "iOS" "ios"
      package_framework_platform "tvOS" "tvos"
      package_framework_platform "watchOS" "watchos"
      package_framework_platform "macOS" "macos"
      package_framework_platform "iOS-MacCatalyst" "ios-catalyst"
      exit 0;;

    "package-each")
      package_each_framework "iOS" "ios" "WebP.framework" "webp"
      package_each_framework "iOS" "ios" "WebPDecoder.framework" "webpdecoder"
      package_each_framework "iOS" "ios" "WebPDemux.framework" "webpdemux"
      package_each_framework "iOS" "ios" "WebPMux.framework" "webpmux"
      package_each_framework "iOS-MacCatalyst" "ios-catalyst" "WebP.xcframework" "webp"
      package_each_framework "iOS-MacCatalyst" "ios-catalyst" "WebPDecoder.xcframework" "webpdecoder"
      package_each_framework "iOS-MacCatalyst" "ios-catalyst" "WebPDemux.xcframework" "webpdemux"
      package_each_framework "iOS-MacCatalyst" "ios-catalyst" "WebPMux.xcframework" "webpmux"
      package_each_framework "tvOS" "tvos" "WebP.framework" "webp"
      package_each_framework "tvOS" "tvos" "WebPDecoder.framework" "webpdecoder"
      package_each_framework "tvOS" "tvos" "WebPDemux.framework" "webpdemux"
      package_each_framework "tvOS" "tvos" "WebPMux.framework" "webpmux"
      package_each_framework "macOS" "macos" "WebP.framework" "webp"
      package_each_framework "macOS" "macos" "WebPDecoder.framework" "webpdecoder"
      package_each_framework "macOS" "macos" "WebPDemux.framework" "webpdemux"
      package_each_framework "macOS" "macos" "WebPMux.framework" "webpmux"
      package_each_framework "watchOS" "watchos" "WebP.framework" "webp"
      package_each_framework "watchOS" "watchos" "WebPDecoder.framework" "webpdecoder"
      package_each_framework "watchOS" "watchos" "WebPDemux.framework" "webpdemux"
      package_each_framework "watchOS" "watchos" "WebPMux.framework" "webpmux"
      exit 0;;

    "package-all")
      package_all_frameworks
      exit 0;
esac

# Print usage instructions if no arguments were set
if [ "$#" -eq 0 -o "$#" -gt 3 ]; then
    usage
    exit 1
fi
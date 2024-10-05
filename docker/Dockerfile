#
# Build libraries and tools
#

FROM python:3-slim-bookworm AS build

RUN apt-get update \
    && apt-get install -y \
        cmake \
        curl \
        g++ \
        libavcodec-dev \
        libavformat-dev \
        libavutil-dev \
        libswresample-dev \
        libeigen3-dev \
        libfftw3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN curl -SL https://github.com/andban/musly/archive/refs/heads/master.tar.gz \
        | tar -xzC /usr/src \
    && mkdir -p /usr/src/musly-master/build \
    && cd /usr/src/musly-master/build \
    && cmake .. \
    && make \
    && make install

RUN curl -SL https://github.com/mixxxdj/libkeyfinder/archive/refs/tags/2.2.8.tar.gz \
        | tar -xzC /usr/src \
    && cd /usr/src/libkeyfinder-2.2.8 \
    && cmake -S . -B build -DBUILD_TESTING=OFF \
    && cmake --build build \
    && cmake --install build \
    && ls -l /usr/local/lib

RUN curl -SL https://github.com/andban/keyfinder-cli/archive/heads/bugfix/endless-loop-on-linux-aarch64.tar.gz \
               | tar -xzC /usr/src \
    && ls -l /usr/src \
    && cd /usr/src/keyfinder-cli-heads-bugfix-endless-loop-on-linux-aarch64 \
    && make && make install

#
# Final image
#

FROM python:3-slim-bookworm

COPY --from=build /usr/local/lib/libmusly.so /usr/local/lib/libmusly_resample.so /usr/local/lib/
COPY --from=build /usr/local/lib/libkeyfinder.so /usr/local/lib/
COPY --from=build /usr/local/bin/keyfinder-cli /usr/local/bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libavcodec59 \
        libavformat59 \
        libavutil57 \
        libswresample4 \
        libfftw3-single3 \
        libfftw3-double3 \
        libfftw3-long3 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir librosa \
    && ldconfig \
    && groupadd -r -g 1001 beets \
    && useradd --no-log-init -rm -d /home/beets -s /bin/sh -u 1001 -g beets beets

COPY . /usr/src/beetmatch

RUN pip install --no-cache-dir /usr/src/beetmatch

USER beets
WORKDIR /var/lib/beets
ENV BEETSDIR "/var/lib/beets"


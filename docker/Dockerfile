FROM python:3.8.12-slim-bullseye

ARG SANDBOX_USER_UID
ARG SANDBOX_DIR

ENV CARGO_HTTP_MULTIPLEXING=false
ENV PATH="/root/.cargo/bin:${PATH}" \
    RUST_BACKTRACE=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends nano curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN curl --http1.1 -fsSL --retry 5 --retry-delay 2 \
         https://sh.rustup.rs -o /tmp/rustup-init.sh

RUN sh /tmp/rustup-init.sh -y --profile minimal \
        --default-toolchain none && \
    rm /tmp/rustup-init.sh

RUN . "$HOME/.cargo/env" && \
    rustup toolchain install 1.86.0 \
          --component rust-src \
          --profile minimal

RUN pip install --no-cache-dir --upgrade pip pipenv

RUN adduser \
    --system \
    --gecos \
    --disabled-login \
    --disabled-password \
    --home ${SANDBOX_DIR} \
    --uid ${SANDBOX_USER_UID} \
    sandbox && \
    chown root:root ${SANDBOX_DIR}

COPY ./src/Pipfile ./src/Pipfile.lock /tmp/
RUN cd /tmp && pipenv install --deploy --dev --system

ENV PATH="/root/.cargo/bin:${PATH}"
ENV RUST_BACKTRACE=1

WORKDIR ${SANDBOX_DIR}

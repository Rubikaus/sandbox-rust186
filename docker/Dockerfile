FROM python:3.8.12-buster

ARG SANDBOX_USER_UID
ARG SANDBOX_DIR

RUN apt-get update && \
    apt-get -y install nano curl && \
    curl -fsSL --retry 5 --retry-delay 2 --retry-connrefused \
         https://sh.rustup.rs -o /tmp/rustup-init.sh && \
    sh /tmp/rustup-init.sh -y --profile minimal --default-toolchain 1.86.0 && \
    rm /tmp/rustup-init.sh && \
    . "$HOME/.cargo/env" && \
    rustup component add rust-src --toolchain 1.86.0 && \
    pip install --upgrade pip && \
    pip install pipenv

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

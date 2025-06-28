FROM langchain/langgraph-api:3.12

# Install system dependencies for boss-bot

ENV UV_SYSTEM_PYTHON=1 \
    UV_PIP_DEFAULT_PYTHON=/usr/bin/python3 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR=/root/.cache/uv/ \
    UV_COMPILE_BYTECODE=1 \
    PYTHONASYNCIODEBUG=1 \
    DEBIAN_FRONTEND=noninteractive \
    TAPLO_VERSION=0.9.3 \
    UV_VERSION=0.7.15 \
    PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    PYTHONFAULTHANDLER=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install comprehensive system dependencies
RUN apt-get update && apt-get -qq install -y --no-install-recommends \
    python3-dev python3 ca-certificates python3-numpy python3-setuptools python3-wheel python3-pip \
    g++ gcc ninja-build cmake build-essential autoconf automake libtool \
    libmagic-dev poppler-utils libreoffice libomp-dev \
    tesseract-ocr tesseract-ocr-por libyaml-dev \
    ffmpeg libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev \
    wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev \
    python3-openssl git libpq5 libpq-dev \
    libxml2-dev libxslt1-dev libcairo2-dev libgirepository1.0-dev libgraphviz-dev \
    libjpeg-dev libopencv-dev libpango1.0-dev \
    libprotobuf-dev protobuf-compiler \
    rustc cargo \
    libwebp-dev libzbar0 libzbar-dev \
    imagemagick ghostscript pandoc aria2 \
    zsh bash-completion pkg-config openssl \
    unzip gzip vim tree less sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install taplo and just
COPY ./install_taplo.sh .
RUN chmod +x install_taplo.sh && bash ./install_taplo.sh && mv taplo /usr/local/bin/taplo && rm install_taplo.sh \
    && curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

# Install rust toolchain
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | env PATH='/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' bash -s -- -y
ENV PATH='/root/.cargo/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'

# Install UV package manager
ADD https://astral.sh/uv/${UV_VERSION}/install.sh /uv-installer.sh
RUN env PATH='/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' bash /uv-installer.sh && rm /uv-installer.sh

ENV PATH='/root/.local/bin:/root/.cargo/bin:/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'

# Set working directory for boss-bot
WORKDIR /deps/boss-bot

# Copy dependency files first for optimal layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies only (UV Docker best practice)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    pip install -U pip && \
    uv sync --frozen --no-install-project --no-dev --compile-bytecode

# Copy project source code
COPY . /deps/boss-bot

# Install project with compiled bytecode for performance
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen --compile-bytecode --no-editable

# -- Adding local package . --
ADD . /deps/boss-bot
# -- End of local package . --

# -- Installing all local dependencies --
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir -c /api/constraints.txt -e /deps/*
# -- End of local dependencies install --
ENV LANGSERVE_GRAPHS='{"download_workflow": "/deps/boss-bot/src/boss_bot/ai/workflows/download_workflow.py:graph"}'



# -- Ensure user deps didn't inadvertently overwrite langgraph-api
RUN mkdir -p /api/langgraph_api /api/langgraph_runtime /api/langgraph_license &&     touch /api/langgraph_api/__init__.py /api/langgraph_runtime/__init__.py /api/langgraph_license/__init__.py
RUN PYTHONDONTWRITEBYTECODE=1 uv pip install --system --no-cache-dir --no-deps -e /api
# -- End of ensuring user deps didn't inadvertently overwrite langgraph-api --
# -- Removing pip from the final image ~<:===~~~ --
RUN pip uninstall -y pip setuptools wheel &&     rm -rf /usr/local/lib/python*/site-packages/pip* /usr/local/lib/python*/site-packages/setuptools* /usr/local/lib/python*/site-packages/wheel* &&     find /usr/local/bin -name "pip*" -delete || true
# pip removal for wolfi
RUN rm -rf /usr/lib/python*/site-packages/pip* /usr/lib/python*/site-packages/setuptools* /usr/lib/python*/site-packages/wheel* &&     find /usr/bin -name "pip*" -delete || true
RUN uv pip uninstall --system pip setuptools wheel && rm /usr/bin/uv /usr/bin/uvx
# -- End of pip removal --

WORKDIR /deps/boss-bot

# glibc-based Python so pip can use manylinux wheels (no Rust toolchain needed)
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /usr/src/app

# System deps (runtime + minimal build tools if any wheel needs it)
# - libzbar0: runtime library for barcode/QR scanning libs
# - openssh-client/curl: keep parity with your original image
# If you know you don't need to compile anything, you can drop build-essential.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzbar0 \
    openssh-client \
    curl \
    ca-certificates \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
 && pip install -r requirements.txt

# App source
COPY . .

# Compile translations (uabel installs the `pybabel` console script)
RUN pybabel compile -d luka_bot/locales || true

# Non-root user
RUN useradd --create-home --home-dir /home/appuser --shell /bin/bash appuser \
 && chown -R appuser:appuser /usr/src/app
USER appuser

CMD ["python", "./luka_bot/__main__.py"]

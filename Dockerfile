# Dockerfile for assembling and linking toy compiler output
# Use x86-64 platform explicitly since the compiler generates x86-64 assembly
# hadolint ignore=DL3029
FROM --platform=linux/amd64 alpine:latest

# Install dependencies:
# - python3, py3-pip: For running the toy compiler
# - nasm: Assembler for x86-64
# - binutils: GNU linker (ld)
RUN apk add --no-cache python3 py3-pip nasm binutils

# Install Python dependencies for the compiler
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt --break-system-packages

# Set working directory
WORKDIR /workspace

# Default command: shell
CMD ["/bin/sh"]

#!/usr/bin/env bash
# Download the medium model for whisper.
mkdir -p ./models && wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin -O ./models/ggml-medium.bin
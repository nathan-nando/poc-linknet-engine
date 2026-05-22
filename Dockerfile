FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# Install Python 3.10 and system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-dev \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl

# Add required symlinks for PaddlePaddle (Runtime images don't have .so, only .so.8/.so.11)
RUN ln -sf /usr/lib/x86_64-linux-gnu/libcudnn.so.8 /usr/lib/x86_64-linux-gnu/libcudnn.so && \
    ln -sf /usr/local/cuda-11.8/targets/x86_64-linux/lib/libcublas.so.11 /usr/local/cuda-11.8/targets/x86_64-linux/lib/libcublas.so

# Ensure python and pip point to python3
RUN ln -sf /usr/bin/python3.10 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
# 1. Install PyTorch for CUDA 11.8 from official PyTorch index (avoids CUDA 12 nvidia packages from PyPI)
RUN pip install --default-timeout=300 --retries=3 torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu118
# 2. Install remaining dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt



# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Create paddleocr directory so Docker volume inherits correct ownership
RUN mkdir -p /home/appuser/.paddleocr

# Copy the rest of the application
COPY --chown=appuser:appuser . .

# Expose port
EXPOSE 8000

# Run FastAPI using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# Python 3.13.2 Bullseye as base image
FROM python:3.13.2-bullseye

# Environment Variables
ENV PIPER_VERSION=2023.11.14-2
ENV PIPER_URL_BASE=https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/

# Copy your requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies and upgrade them if needed
RUN pip install --upgrade pip && pip install -U -r requirements.txt

# Create user permissions
RUN useradd -m -u 1000 app

# Set working directory
WORKDIR /app

# Download and extract Piper binaries
RUN arch=$(uname -m) && \
    case "${arch}" in \
        x86_64) DOWNLOAD_URL="${PIPER_URL_BASE}piper_linux_x86_64.tar.gz" ;; \
        armv7l) DOWNLOAD_URL="${PIPER_URL_BASE}piper_linux_armv7l.tar.gz" ;; \
        aarch64) DOWNLOAD_URL="${PIPER_URL_BASE}piper_linux_aarch64.tar.gz" ;; \
        *) echo "Unsupported architecture: ${arch}"; exit 1 ;; \
    esac && \
    curl -SL "${DOWNLOAD_URL}" | tar -xzC ./

# Copy the app code
COPY --chown=app:app . .

# Set permission
RUN chown -R app:app .

# Exposing Port 5000
EXPOSE 5000

# Start Application as Root
USER root
CMD ["python3", "app.py"]

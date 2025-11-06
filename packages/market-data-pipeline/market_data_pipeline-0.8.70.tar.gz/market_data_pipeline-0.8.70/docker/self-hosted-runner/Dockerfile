# GitHub Actions Self-Hosted Runner Docker Image
FROM ubuntu:22.04

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    openssl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create runner user
RUN useradd -m -s /bin/bash runner

# Set working directory
WORKDIR /home/runner

# Copy runner setup script
COPY setup-runner.sh /home/runner/
RUN chmod +x /home/runner/setup-runner.sh

# Switch to runner user
USER runner

# Expose port for health checks (optional)
EXPOSE 8080

# Default command
CMD ["/home/runner/setup-runner.sh"]

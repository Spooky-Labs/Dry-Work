# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY . .

# Create non-root user
RUN useradd -m trader && \
    mkdir -p /var/lib/trading-agent && \
    chown -R trader:trader /var/lib/trading-agent

USER trader

# Volume for persistence
VOLUME ["/var/lib/trading-agent"]

# Run the agent
CMD ["python", "run_agent.py"]
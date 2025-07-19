#!/bin/bash

# Multi-Agent MCP System Installation Script
# For Ubuntu 24.04 with Cloudflare Tunnel
# Version: 1.0

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Please run as a user with sudo privileges."
fi

# Check if sudo is available
if ! command -v sudo &> /dev/null; then
    error "sudo is required but not installed."
fi

# Check Ubuntu version
if ! grep -q "Ubuntu 24.04" /etc/os-release; then
    warn "This script is optimized for Ubuntu 24.04. Your version may work but is not tested."
fi

log "Starting Multi-Agent MCP System installation..."

# Update system
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
log "Installing required packages..."
sudo apt install -y \
    curl \
    wget \
    git \
    unzip \
    htop \
    nano \
    jq \
    tree \
    net-tools \
    ufw \
    fail2ban \
    logrotate \
    python3 \
    python3-pip \
    python3-venv

# Install Python packages
log "Installing Python packages..."
pip3 install --upgrade pip
pip3 install -U openai

# Test Qwen API connection
log "Creating Qwen API test script..."
cat > /tmp/hello_qwen.py <<'EOF'
import os
from openai import OpenAI

try:
    client = OpenAI(
        # If the environment variable is not configured, replace the following line with your API key: api_key="sk-xxx",
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    )

    completion = client.chat.completions.create(
        model="qwen-plus",  # Model list: https://www.alibabacloud.com/help/en/model-studio/getting-started/models
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Who are you?'}
            ]
    )
    print("✅ Qwen API Test Successful!")
    print(f"Response: {completion.choices[0].message.content}")
except Exception as e:
    print(f"❌ Qwen API Test Failed: {e}")
    print("For more information, see: https://www.alibabacloud.com/help/en/model-studio/developer-reference/error-code")
EOF

log "Qwen API test script created at /tmp/hello_qwen.py"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
else
    log "Docker is already installed"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    log "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    log "Docker Compose is already installed"
fi

# Create project directory
PROJECT_DIR="/opt/multi-agent-mcp"
log "Creating project directory at $PROJECT_DIR..."
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# Clone or copy project files
if [ -d "multi_agent_mcp" ]; then
    log "Copying project files..."
    cp -r multi_agent_mcp/* $PROJECT_DIR/
else
    error "Project files not found. Please ensure the multi_agent_mcp directory exists."
fi

# Set up environment file
log "Setting up environment configuration..."
cd $PROJECT_DIR/deployment
if [ ! -f .env ]; then
    if [ -f .alwazw.env ]; then
        log "Using custom alwazw environment configuration..."
        cp .alwazw.env .env
    else
        log "Using example environment configuration..."
        cp .env.example .env
        warn "Please edit $PROJECT_DIR/deployment/.env with your settings."
    fi
fi

# Test Qwen API with actual credentials
log "Testing Qwen API connection..."
export DASHSCOPE_API_KEY='sk-991e406e28cf4e71a3a36b805e76d193'
python3 /tmp/hello_qwen.py

log "Qwen API test completed. Check output above for results."

# Create necessary directories
log "Creating data directories..."
sudo mkdir -p /opt/multi-agent-mcp/data/{postgres,redis,uploads,backups,logs}
sudo chown -R $USER:$USER /opt/multi-agent-mcp/data

# Set up UFW firewall rules
log "Configuring firewall..."
sudo ufw --force enable
sudo ufw allow 22/tcp comment "SSH"
sudo ufw allow 80/tcp comment "HTTP"
sudo ufw allow 443/tcp comment "HTTPS"

# Create systemd service for easy management
log "Creating systemd service..."
sudo tee /etc/systemd/system/multi-agent-mcp.service > /dev/null <<EOF
[Unit]
Description=Multi-Agent MCP System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR/deployment
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0
User=$USER
Group=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable multi-agent-mcp.service

# Create management scripts
log "Creating management scripts..."
sudo tee /usr/local/bin/mcp-start > /dev/null <<'EOF'
#!/bin/bash
cd /opt/multi-agent-mcp/deployment
docker-compose up -d
echo "Multi-Agent MCP System started"
EOF

sudo tee /usr/local/bin/mcp-stop > /dev/null <<'EOF'
#!/bin/bash
cd /opt/multi-agent-mcp/deployment
docker-compose down
echo "Multi-Agent MCP System stopped"
EOF

sudo tee /usr/local/bin/mcp-restart > /dev/null <<'EOF'
#!/bin/bash
cd /opt/multi-agent-mcp/deployment
docker-compose down
docker-compose up -d
echo "Multi-Agent MCP System restarted"
EOF

sudo tee /usr/local/bin/mcp-logs > /dev/null <<'EOF'
#!/bin/bash
cd /opt/multi-agent-mcp/deployment
if [ -z "$1" ]; then
    docker-compose logs -f
else
    docker-compose logs -f "$1"
fi
EOF

sudo tee /usr/local/bin/mcp-status > /dev/null <<'EOF'
#!/bin/bash
cd /opt/multi-agent-mcp/deployment
echo "=== Multi-Agent MCP System Status ==="
docker-compose ps
echo ""
echo "=== System Resources ==="
docker stats --no-stream
EOF

sudo tee /usr/local/bin/mcp-backup > /dev/null <<'EOF'
#!/bin/bash
BACKUP_DIR="/opt/multi-agent-mcp/data/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/mcp_backup_$DATE.tar.gz"

echo "Creating backup: $BACKUP_FILE"
cd /opt/multi-agent-mcp/deployment
docker-compose exec -T postgres pg_dump -U mcp_user mcp_system > "$BACKUP_DIR/db_$DATE.sql"
tar -czf "$BACKUP_FILE" -C /opt/multi-agent-mcp data/
echo "Backup completed: $BACKUP_FILE"
EOF

sudo tee /usr/local/bin/mcp-update > /dev/null <<'EOF'
#!/bin/bash
cd /opt/multi-agent-mcp/deployment
echo "Updating Multi-Agent MCP System..."
docker-compose pull
docker-compose down
docker-compose up -d --build
echo "Update completed"
EOF

# Make scripts executable
sudo chmod +x /usr/local/bin/mcp-*

# Set up log rotation
log "Setting up log rotation..."
sudo tee /etc/logrotate.d/multi-agent-mcp > /dev/null <<EOF
/opt/multi-agent-mcp/data/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
}
EOF

# Set up automatic backups
log "Setting up automatic backups..."
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/mcp-backup") | crontab -

# Create Dockerfiles for each agent
log "Creating Dockerfiles..."

# Agent 1 Dockerfile
mkdir -p $PROJECT_DIR/agents/agent1_scraper/agent1_scraper
cat > $PROJECT_DIR/agents/agent1_scraper/agent1_scraper/Dockerfile <<'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data /app/uploads

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/scraper/health || exit 1

# Run application
CMD ["python", "src/main.py"]
EOF

# Similar Dockerfiles for other agents
for agent in agent2_knowledge agent3_database agent4_transformer; do
    agent_dir="$PROJECT_DIR/agents/$agent/$agent"
    mkdir -p "$agent_dir"
    cp "$PROJECT_DIR/agents/agent1_scraper/agent1_scraper/Dockerfile" "$agent_dir/Dockerfile"
done

# Orchestrator Dockerfile
mkdir -p $PROJECT_DIR/n8n_integration/n8n_orchestrator
cat > $PROJECT_DIR/n8n_integration/n8n_orchestrator/Dockerfile <<'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data

EXPOSE 5004

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5004/api/orchestrator/health || exit 1

CMD ["python", "src/main.py"]
EOF

# GUI Dockerfile
cat > $PROJECT_DIR/multi-agent-gui/Dockerfile <<'EOF'
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

CMD ["nginx", "-g", "daemon off;"]
EOF

log "Installation completed successfully!"
echo ""
echo -e "${BLUE}=== Next Steps ===${NC}"
echo "1. Edit the environment file: nano $PROJECT_DIR/deployment/.env"
echo "2. Set your OpenAI API key and other configurations"
echo "3. Start the system: mcp-start"
echo "4. Check status: mcp-status"
echo "5. View logs: mcp-logs"
echo ""
echo -e "${BLUE}=== Access URLs ===${NC}"
echo "Main GUI: https://mcp.visionvation.com"
echo "Monitoring: https://mcp.visionvation.com/grafana"
echo "Prometheus: https://mcp.visionvation.com/prometheus"
echo ""
echo -e "${BLUE}=== Management Commands ===${NC}"
echo "mcp-start    - Start the system"
echo "mcp-stop     - Stop the system"
echo "mcp-restart  - Restart the system"
echo "mcp-status   - Show system status"
echo "mcp-logs     - View logs (add service name for specific logs)"
echo "mcp-backup   - Create backup"
echo "mcp-update   - Update system"
echo ""
echo -e "${GREEN}Installation completed! The system is ready to start.${NC}"


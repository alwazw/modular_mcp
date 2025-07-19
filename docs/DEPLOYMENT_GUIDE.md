# Multi-Agent MCP System Deployment Guide

**Version**: 1.0.0  
**Date**: July 18, 2025  
**Author**: Manus AI  

## Table of Contents

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Quick Deployment](#quick-deployment)
4. [Production Deployment](#production-deployment)
5. [n8n Integration Setup](#n8n-integration-setup)
6. [Security Configuration](#security-configuration)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)
8. [Disaster Recovery](#disaster-recovery)
9. [Troubleshooting](#troubleshooting)

## Overview

This deployment guide provides comprehensive instructions for deploying the Multi-Agent MCP System in various environments, from development testing to production-ready installations. The system is designed to be highly scalable and can be deployed on single servers or distributed across multiple machines.

The Multi-Agent MCP System consists of five main components that can be deployed independently or together:
- **Orchestrator Service** (Port 5004) - Central coordination and workflow management
- **Agent 1: Web Scraper** (Port 5000) - Data collection and web scraping
- **Agent 2: Knowledge Base** (Port 5001) - Document processing and knowledge management
- **Agent 3: Database Manager** (Port 5002) - Database operations and analytics
- **Agent 4: Data Transformer** (Port 5003) - Intelligent data transformation

## System Requirements

### Minimum Requirements (Development/Testing)
- **Operating System**: Ubuntu 20.04+ or compatible Linux distribution
- **CPU**: 2 cores, 2.4 GHz
- **Memory**: 4 GB RAM
- **Storage**: 20 GB available disk space
- **Network**: Internet connectivity for package installation and API access

### Recommended Requirements (Production)
- **Operating System**: Ubuntu 22.04 LTS
- **CPU**: 8 cores, 3.0 GHz
- **Memory**: 16 GB RAM
- **Storage**: 100 GB SSD storage
- **Network**: High-speed internet connection with static IP
- **Database**: PostgreSQL 14+ or MySQL 8.0+

### Software Dependencies
- **Python**: 3.11.0 or higher
- **Node.js**: 20.18.0 or higher (for n8n integration)
- **Redis**: 6.0+ (for caching and message queuing)
- **Nginx**: 1.18+ (for reverse proxy and load balancing)
- **SSL Certificate**: For HTTPS in production

## Quick Deployment

### Automated Installation Script

For rapid deployment on a fresh Ubuntu server, use the automated installation script:

```bash
#!/bin/bash
# Multi-Agent MCP System Quick Deploy Script
# Run as: curl -sSL https://your-domain.com/install.sh | bash

set -e

echo "🚀 Starting Multi-Agent MCP System Deployment..."

# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm redis-server nginx git curl

# Create system user
sudo useradd -m -s /bin/bash mcp-system
sudo usermod -aG sudo mcp-system

# Clone repository
cd /opt
sudo git clone https://github.com/your-org/multi-agent-mcp.git
sudo chown -R mcp-system:mcp-system multi-agent-mcp
cd multi-agent-mcp

# Install Python dependencies
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Node.js dependencies for n8n integration
npm install -g n8n

# Create configuration files
sudo mkdir -p /etc/mcp-system
sudo cp config/production.conf /etc/mcp-system/

# Create systemd services
sudo cp scripts/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Start services
sudo systemctl enable mcp-orchestrator mcp-agent1 mcp-agent2 mcp-agent3 mcp-agent4
sudo systemctl start mcp-orchestrator mcp-agent1 mcp-agent2 mcp-agent3 mcp-agent4

# Configure Nginx
sudo cp config/nginx/mcp-system.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/mcp-system.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Multi-Agent MCP System deployed successfully!"
echo "🌐 Access the system at: http://your-server-ip:5004"
echo "📚 Documentation: /opt/multi-agent-mcp/docs/"
```

### Manual Quick Setup

If you prefer manual installation:

```bash
# 1. Create project directory
mkdir -p /opt/multi-agent-mcp
cd /opt/multi-agent-mcp

# 2. Copy your project files
# (Upload your project files to this directory)

# 3. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start services (development mode)
cd agents/agent1_scraper/agent1_scraper && python src/main.py &
cd agents/agent2_knowledge/agent2_knowledge && python src/main.py &
cd agents/agent3_database/agent3_database && python src/main.py &
cd agents/agent4_transformer/agent4_transformer && python src/main.py &
cd n8n_integration/n8n_orchestrator && python src/main.py &

# 6. Verify deployment
curl http://localhost:5004/api/orchestrator/health
```

## Production Deployment

### Environment Preparation

#### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Add Python 3.11 repository
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Redis
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Install Nginx
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
```

#### 2. Database Setup
```bash
# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE mcp_system;
CREATE USER mcp_user WITH ENCRYPTED PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE mcp_system TO mcp_user;
ALTER USER mcp_user CREATEDB;
\q
EOF

# Configure PostgreSQL for production
sudo nano /etc/postgresql/14/main/postgresql.conf
# Set: shared_buffers = 256MB, effective_cache_size = 1GB

sudo nano /etc/postgresql/14/main/pg_hba.conf
# Add: host mcp_system mcp_user 127.0.0.1/32 md5

sudo systemctl restart postgresql
```

#### 3. Application Deployment
```bash
# Create application user
sudo useradd -m -s /bin/bash mcp-system
sudo usermod -aG sudo mcp-system

# Create application directory
sudo mkdir -p /opt/mcp-system
sudo chown mcp-system:mcp-system /opt/mcp-system

# Switch to application user
sudo -u mcp-system bash

# Deploy application
cd /opt/mcp-system
git clone https://github.com/your-org/multi-agent-mcp.git .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Create configuration
mkdir -p config
cat > config/production.py << EOF
import os

# Database Configuration
DATABASE_URL = "postgresql://mcp_user:secure_password_here@localhost/mcp_system"

# Redis Configuration
REDIS_URL = "redis://localhost:6379/0"

# Security Configuration
SECRET_KEY = "your-secret-key-here"
API_KEY_REQUIRED = True
CORS_ORIGINS = ["https://your-domain.com"]

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FILE = "/var/log/mcp-system/app.log"

# Performance Configuration
WORKERS = 4
WORKER_CONNECTIONS = 1000
EOF
```

### Service Configuration

#### 1. Systemd Services

Create systemd service files for each component:

**Orchestrator Service** (`/etc/systemd/system/mcp-orchestrator.service`):
```ini
[Unit]
Description=MCP System Orchestrator
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=exec
User=mcp-system
Group=mcp-system
WorkingDirectory=/opt/mcp-system/n8n_integration/n8n_orchestrator
Environment=PATH=/opt/mcp-system/venv/bin
Environment=FLASK_ENV=production
Environment=CONFIG_FILE=/opt/mcp-system/config/production.py
ExecStart=/opt/mcp-system/venv/bin/gunicorn --bind 127.0.0.1:5004 --workers 4 src.main:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**Agent 1 Service** (`/etc/systemd/system/mcp-agent1.service`):
```ini
[Unit]
Description=MCP Agent 1 - Web Scraper
After=network.target
Requires=mcp-orchestrator.service

[Service]
Type=exec
User=mcp-system
Group=mcp-system
WorkingDirectory=/opt/mcp-system/agents/agent1_scraper/agent1_scraper
Environment=PATH=/opt/mcp-system/venv/bin
Environment=FLASK_ENV=production
ExecStart=/opt/mcp-system/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 src.main:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Create similar service files for agents 2, 3, and 4, adjusting ports and working directories accordingly.

#### 2. Nginx Configuration

**Main Configuration** (`/etc/nginx/sites-available/mcp-system`):
```nginx
upstream mcp_orchestrator {
    server 127.0.0.1:5004;
}

upstream mcp_agent1 {
    server 127.0.0.1:5000;
}

upstream mcp_agent2 {
    server 127.0.0.1:5001;
}

upstream mcp_agent3 {
    server 127.0.0.1:5002;
}

upstream mcp_agent4 {
    server 127.0.0.1:5003;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.com.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Main orchestrator
    location / {
        proxy_pass http://mcp_orchestrator;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Agent endpoints
    location /agent1/ {
        proxy_pass http://mcp_agent1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /agent2/ {
        proxy_pass http://mcp_agent2/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /agent3/ {
        proxy_pass http://mcp_agent3/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /agent4/ {
        proxy_pass http://mcp_agent4/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /opt/mcp-system/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

#### 3. SSL Certificate Setup

Using Let's Encrypt:
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Service Management

#### Start Services
```bash
# Enable and start all services
sudo systemctl enable mcp-orchestrator mcp-agent1 mcp-agent2 mcp-agent3 mcp-agent4
sudo systemctl start mcp-orchestrator mcp-agent1 mcp-agent2 mcp-agent3 mcp-agent4

# Enable and reload Nginx
sudo ln -s /etc/nginx/sites-available/mcp-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Check service status
sudo systemctl status mcp-orchestrator
sudo systemctl status mcp-agent1
sudo systemctl status mcp-agent2
sudo systemctl status mcp-agent3
sudo systemctl status mcp-agent4
```

#### Service Management Commands
```bash
# Check all service status
sudo systemctl status mcp-*

# Restart all services
sudo systemctl restart mcp-*

# View logs
sudo journalctl -u mcp-orchestrator -f
sudo journalctl -u mcp-agent1 -f

# Stop services
sudo systemctl stop mcp-*
```

## n8n Integration Setup

### n8n Installation

#### 1. Install n8n
```bash
# Install n8n globally
sudo npm install -g n8n

# Create n8n user
sudo useradd -m -s /bin/bash n8n

# Create n8n directory
sudo mkdir -p /opt/n8n
sudo chown n8n:n8n /opt/n8n

# Switch to n8n user
sudo -u n8n bash
cd /opt/n8n

# Create n8n configuration
cat > .env << EOF
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secure_password_here
N8N_HOST=0.0.0.0
N8N_PORT=5678
N8N_PROTOCOL=https
N8N_EDITOR_BASE_URL=https://n8n.your-domain.com
WEBHOOK_URL=https://n8n.your-domain.com
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=localhost
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=n8n
DB_POSTGRESDB_USER=n8n_user
DB_POSTGRESDB_PASSWORD=n8n_password
EOF
```

#### 2. n8n Database Setup
```bash
# Create n8n database
sudo -u postgres psql << EOF
CREATE DATABASE n8n;
CREATE USER n8n_user WITH ENCRYPTED PASSWORD 'n8n_password';
GRANT ALL PRIVILEGES ON DATABASE n8n TO n8n_user;
\q
EOF
```

#### 3. n8n Systemd Service
Create `/etc/systemd/system/n8n.service`:
```ini
[Unit]
Description=n8n Workflow Automation
After=network.target postgresql.service

[Service]
Type=exec
User=n8n
Group=n8n
WorkingDirectory=/opt/n8n
Environment=NODE_ENV=production
EnvironmentFile=/opt/n8n/.env
ExecStart=/usr/bin/n8n start
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### 4. n8n Nginx Configuration
Add to your Nginx configuration:
```nginx
server {
    listen 443 ssl http2;
    server_name n8n.your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.com.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.com.key;

    location / {
        proxy_pass http://127.0.0.1:5678;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### n8n Workflow Configuration

#### 1. Create HTTP Request Node
In n8n, create an HTTP Request node with these settings:
- **Method**: POST
- **URL**: `https://your-domain.com/api/webhooks/trigger/your-endpoint`
- **Headers**: 
  - `Content-Type`: `application/json`
  - `X-API-Key`: `your-api-key` (if authentication enabled)

#### 2. Sample Workflow
```json
{
  "name": "MCP Data Processing",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "mcp-trigger",
        "responseMode": "responseNode"
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [240, 300]
    },
    {
      "parameters": {
        "url": "https://your-domain.com/api/webhooks/trigger/process-data",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "data",
              "value": "={{$json}}"
            }
          ]
        },
        "options": {}
      },
      "name": "Send to MCP",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 1,
      "position": [460, 300]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{$json}}"
      },
      "name": "Respond to Webhook",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1,
      "position": [680, 300]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [
        [
          {
            "node": "Send to MCP",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Send to MCP": {
      "main": [
        [
          {
            "node": "Respond to Webhook",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

## Security Configuration

### 1. API Key Authentication
```python
# Add to production configuration
API_KEYS = {
    'sk_prod_12345': {
        'name': 'Production API Key',
        'permissions': ['read', 'write', 'admin'],
        'rate_limit': 1000
    },
    'sk_n8n_67890': {
        'name': 'n8n Integration Key',
        'permissions': ['read', 'write'],
        'rate_limit': 500
    }
}

# Enable API key validation
REQUIRE_API_KEY = True
```

### 2. Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow specific services (if needed)
sudo ufw allow from 10.0.0.0/8 to any port 5432  # PostgreSQL
sudo ufw allow from 127.0.0.1 to any port 6379   # Redis

# Check status
sudo ufw status verbose
```

### 3. Database Security
```bash
# Secure PostgreSQL
sudo -u postgres psql << EOF
-- Remove default postgres user password
ALTER USER postgres PASSWORD 'secure_postgres_password';

-- Create read-only user for monitoring
CREATE USER monitoring WITH PASSWORD 'monitoring_password';
GRANT CONNECT ON DATABASE mcp_system TO monitoring;
GRANT USAGE ON SCHEMA public TO monitoring;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO monitoring;

-- Enable SSL
ALTER SYSTEM SET ssl = on;
SELECT pg_reload_conf();
\q
EOF
```

### 4. Application Security
```python
# Security middleware configuration
SECURITY_HEADERS = {
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'"
}

# Rate limiting
RATE_LIMITS = {
    'default': '1000 per hour',
    'webhook': '100 per hour',
    'upload': '50 per hour'
}

# Input validation
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'csv', 'xlsx'}
```

## Monitoring and Maintenance

### 1. Health Monitoring
```bash
# Create health check script
cat > /opt/mcp-system/scripts/health_check.sh << 'EOF'
#!/bin/bash

SERVICES=("mcp-orchestrator" "mcp-agent1" "mcp-agent2" "mcp-agent3" "mcp-agent4")
ENDPOINTS=(
    "http://localhost:5004/api/orchestrator/health"
    "http://localhost:5000/api/scraper/health"
    "http://localhost:5001/api/knowledge/health"
    "http://localhost:5002/api/database/health"
    "http://localhost:5003/api/transformer/health"
)

for i in "${!SERVICES[@]}"; do
    service="${SERVICES[$i]}"
    endpoint="${ENDPOINTS[$i]}"
    
    # Check service status
    if ! systemctl is-active --quiet "$service"; then
        echo "CRITICAL: $service is not running"
        systemctl restart "$service"
    fi
    
    # Check endpoint health
    if ! curl -f -s "$endpoint" > /dev/null; then
        echo "WARNING: $service endpoint not responding"
    else
        echo "OK: $service is healthy"
    fi
done
EOF

chmod +x /opt/mcp-system/scripts/health_check.sh

# Add to crontab
echo "*/5 * * * * /opt/mcp-system/scripts/health_check.sh >> /var/log/mcp-health.log 2>&1" | sudo crontab -
```

### 2. Log Management
```bash
# Configure logrotate
sudo cat > /etc/logrotate.d/mcp-system << EOF
/var/log/mcp-system/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 mcp-system mcp-system
    postrotate
        systemctl reload mcp-*
    endscript
}
EOF

# Create log directory
sudo mkdir -p /var/log/mcp-system
sudo chown mcp-system:mcp-system /var/log/mcp-system
```

### 3. Performance Monitoring
```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Create performance monitoring script
cat > /opt/mcp-system/scripts/performance_monitor.sh << 'EOF'
#!/bin/bash

LOG_FILE="/var/log/mcp-system/performance.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# System metrics
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
MEM_USAGE=$(free | grep Mem | awk '{printf "%.2f", $3/$2 * 100.0}')
DISK_USAGE=$(df -h / | awk 'NR==2{printf "%s", $5}')

# Service metrics
for service in mcp-orchestrator mcp-agent1 mcp-agent2 mcp-agent3 mcp-agent4; do
    if systemctl is-active --quiet "$service"; then
        PID=$(systemctl show --property MainPID --value "$service")
        if [ "$PID" != "0" ]; then
            CPU_SERVICE=$(ps -p "$PID" -o %cpu --no-headers)
            MEM_SERVICE=$(ps -p "$PID" -o %mem --no-headers)
            echo "$DATE,$service,$CPU_SERVICE,$MEM_SERVICE" >> "$LOG_FILE"
        fi
    fi
done

echo "$DATE,system,$CPU_USAGE,$MEM_USAGE,$DISK_USAGE" >> "$LOG_FILE"
EOF

chmod +x /opt/mcp-system/scripts/performance_monitor.sh

# Add to crontab (every 5 minutes)
echo "*/5 * * * * /opt/mcp-system/scripts/performance_monitor.sh" | sudo crontab -
```

### 4. Backup Strategy
```bash
# Create backup script
cat > /opt/mcp-system/scripts/backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/backups/mcp-system"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="mcp_backup_$DATE.tar.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Database backup
pg_dump -h localhost -U mcp_user mcp_system > "$BACKUP_DIR/database_$DATE.sql"

# Application backup
tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='logs' \
    /opt/mcp-system

# Configuration backup
cp -r /etc/mcp-system "$BACKUP_DIR/config_$DATE"

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "mcp_backup_*.tar.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "database_*.sql" -mtime +30 -delete
find "$BACKUP_DIR" -name "config_*" -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_FILE"
EOF

chmod +x /opt/mcp-system/scripts/backup.sh

# Schedule daily backups at 2 AM
echo "0 2 * * * /opt/mcp-system/scripts/backup.sh >> /var/log/mcp-backup.log 2>&1" | sudo crontab -
```

## Disaster Recovery

### 1. Automated Recovery Script
```bash
# Create disaster recovery script
cat > /opt/mcp-system/scripts/disaster_recovery.sh << 'EOF'
#!/bin/bash

set -e

BACKUP_DIR="/opt/backups/mcp-system"
RECOVERY_LOG="/var/log/mcp-recovery.log"

echo "$(date): Starting disaster recovery process" >> "$RECOVERY_LOG"

# Stop all services
systemctl stop mcp-* nginx

# Find latest backup
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/mcp_backup_*.tar.gz | head -1)
LATEST_DB_BACKUP=$(ls -t "$BACKUP_DIR"/database_*.sql | head -1)

if [ -z "$LATEST_BACKUP" ] || [ -z "$LATEST_DB_BACKUP" ]; then
    echo "$(date): ERROR - No backup files found" >> "$RECOVERY_LOG"
    exit 1
fi

echo "$(date): Restoring from $LATEST_BACKUP" >> "$RECOVERY_LOG"

# Restore application
cd /
tar -xzf "$LATEST_BACKUP"

# Restore database
dropdb -U postgres mcp_system
createdb -U postgres mcp_system
psql -U postgres mcp_system < "$LATEST_DB_BACKUP"

# Restore permissions
chown -R mcp-system:mcp-system /opt/mcp-system

# Start services
systemctl start mcp-* nginx

# Verify recovery
sleep 30
if curl -f -s http://localhost:5004/api/orchestrator/health > /dev/null; then
    echo "$(date): Recovery successful" >> "$RECOVERY_LOG"
else
    echo "$(date): Recovery failed - service not responding" >> "$RECOVERY_LOG"
    exit 1
fi
EOF

chmod +x /opt/mcp-system/scripts/disaster_recovery.sh
```

### 2. Fresh Installation Recovery
```bash
# Create fresh installation script for disaster recovery
cat > /opt/mcp-system/scripts/fresh_install_recovery.sh << 'EOF'
#!/bin/bash

# Multi-Agent MCP System Fresh Installation Recovery Script
# This script can be run on a fresh Ubuntu server to restore from backup

set -e

BACKUP_URL="$1"  # URL or path to backup file
DB_BACKUP_URL="$2"  # URL or path to database backup

if [ -z "$BACKUP_URL" ] || [ -z "$DB_BACKUP_URL" ]; then
    echo "Usage: $0 <backup_url> <db_backup_url>"
    exit 1
fi

echo "Starting fresh installation recovery..."

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3.11 python3.11-venv python3-pip nodejs npm redis-server postgresql postgresql-contrib nginx git curl

# Create user
useradd -m -s /bin/bash mcp-system

# Download and restore backup
mkdir -p /opt/mcp-system
cd /opt/mcp-system

if [[ "$BACKUP_URL" == http* ]]; then
    curl -L "$BACKUP_URL" | tar -xz
else
    tar -xzf "$BACKUP_URL"
fi

# Set permissions
chown -R mcp-system:mcp-system /opt/mcp-system

# Setup database
sudo -u postgres createdb mcp_system
sudo -u postgres createuser mcp_user

if [[ "$DB_BACKUP_URL" == http* ]]; then
    curl -L "$DB_BACKUP_URL" | sudo -u postgres psql mcp_system
else
    sudo -u postgres psql mcp_system < "$DB_BACKUP_URL"
fi

# Install Python dependencies
cd /opt/mcp-system
sudo -u mcp-system python3.11 -m venv venv
sudo -u mcp-system bash -c "source venv/bin/activate && pip install -r requirements.txt"

# Install systemd services
cp scripts/systemd/*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable mcp-*

# Configure Nginx
cp config/nginx/mcp-system.conf /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/mcp-system.conf /etc/nginx/sites-enabled/
nginx -t

# Start services
systemctl start mcp-* nginx

echo "Fresh installation recovery completed!"
echo "System should be accessible at http://$(hostname -I | awk '{print $1}'):5004"
EOF

chmod +x /opt/mcp-system/scripts/fresh_install_recovery.sh
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Service Won't Start
```bash
# Check service status
sudo systemctl status mcp-orchestrator

# Check logs
sudo journalctl -u mcp-orchestrator -n 50

# Common fixes:
# - Check port conflicts: sudo netstat -tlnp | grep :5004
# - Check permissions: sudo chown -R mcp-system:mcp-system /opt/mcp-system
# - Check Python path: which python3.11
# - Check virtual environment: source /opt/mcp-system/venv/bin/activate
```

#### 2. Database Connection Issues
```bash
# Test database connection
sudo -u postgres psql -c "\l"

# Check PostgreSQL status
sudo systemctl status postgresql

# Test application database connection
sudo -u mcp-system psql -h localhost -U mcp_user -d mcp_system -c "SELECT 1;"

# Common fixes:
# - Check pg_hba.conf authentication
# - Verify user permissions
# - Check network connectivity
# - Restart PostgreSQL: sudo systemctl restart postgresql
```

#### 3. High Memory Usage
```bash
# Check memory usage by service
ps aux | grep python | sort -k4 -nr

# Check system memory
free -h

# Solutions:
# - Reduce worker processes in gunicorn
# - Implement memory limits in systemd services
# - Add swap space if needed
# - Optimize database queries
```

#### 4. SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in /etc/ssl/certs/your-domain.com.crt -text -noout

# Test SSL configuration
nginx -t

# Renew Let's Encrypt certificate
sudo certbot renew --dry-run

# Check certificate expiration
echo | openssl s_client -servername your-domain.com -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

#### 5. Performance Issues
```bash
# Check system load
uptime
htop

# Check disk I/O
iotop

# Check network usage
nethogs

# Database performance
sudo -u postgres psql mcp_system -c "SELECT * FROM pg_stat_activity;"

# Solutions:
# - Scale horizontally (add more servers)
# - Optimize database indexes
# - Implement caching with Redis
# - Use CDN for static content
```

### Emergency Procedures

#### 1. Emergency Shutdown
```bash
# Stop all services immediately
sudo systemctl stop mcp-* nginx

# Kill any remaining processes
sudo pkill -f "python.*mcp"

# Check for remaining processes
ps aux | grep mcp
```

#### 2. Emergency Recovery
```bash
# Quick recovery from backup
sudo /opt/mcp-system/scripts/disaster_recovery.sh

# Manual recovery steps:
# 1. Stop services
# 2. Restore from latest backup
# 3. Check database integrity
# 4. Start services
# 5. Verify functionality
```

#### 3. Rollback Deployment
```bash
# If new deployment fails, rollback to previous version
cd /opt/mcp-system
git log --oneline -10  # Find previous commit
git checkout <previous-commit-hash>

# Restart services
sudo systemctl restart mcp-*

# Verify rollback
curl http://localhost:5004/api/orchestrator/health
```

This comprehensive deployment guide provides everything needed to deploy the Multi-Agent MCP System in production environments with proper security, monitoring, and disaster recovery capabilities. Follow the appropriate sections based on your deployment requirements and environment constraints.


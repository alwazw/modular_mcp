# Multi-Agent MCP System - Ubuntu Server Deployment

## 🚀 Quick Start

### Prerequisites
- Ubuntu 24.04 server with sudo access
- 21GB RAM, 16 cores, 256GB disk (your specs are perfect!)
- Docker installed
- UFW firewall enabled with ports 80, 443, 22 open
- Cloudflare Tunnel configured for `mcp.visionvation.com`

### One-Command Installation

```bash
# Download and run the installation script
curl -sSL https://raw.githubusercontent.com/your-repo/multi-agent-mcp/main/deployment/scripts/install.sh | bash
```

Or manually:

```bash
# Clone the repository
git clone https://github.com/your-repo/multi-agent-mcp.git
cd multi-agent-mcp/deployment

# Run installation script
chmod +x scripts/install.sh
./scripts/install.sh
```

## 🔧 Configuration

### 1. Environment Setup

Edit the environment file:
```bash
nano /opt/multi-agent-mcp/deployment/.env
```

**Required Settings:**
```env
# Database (change the password!)
DB_PASSWORD=your_secure_password_here

# OpenAI API (for AI features)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Monitoring (change the password!)
GRAFANA_PASSWORD=your_grafana_password_here

# Security
SECRET_KEY=your_secret_key_here
```

### 2. Start the System

```bash
# Start all services
mcp-start

# Check status
mcp-status

# View logs
mcp-logs
```

## 🌐 Access URLs

- **Main GUI**: https://mcp.visionvation.com
- **System Monitoring**: https://mcp.visionvation.com/grafana
- **Metrics**: https://mcp.visionvation.com/prometheus

### Direct Agent Access (for debugging)
- **Agent 1 (Scraper)**: https://mcp.visionvation.com/agent1
- **Agent 2 (Knowledge)**: https://mcp.visionvation.com/agent2
- **Agent 3 (Database)**: https://mcp.visionvation.com/agent3
- **Agent 4 (Transformer)**: https://mcp.visionvation.com/agent4
- **Orchestrator**: https://mcp.visionvation.com/orchestrator

## 🛠️ Management Commands

```bash
# System Control
mcp-start          # Start the system
mcp-stop           # Stop the system
mcp-restart        # Restart the system
mcp-status         # Show system status

# Monitoring
mcp-logs           # View all logs
mcp-logs agent1    # View specific agent logs
mcp-logs nginx     # View web server logs

# Maintenance
mcp-backup         # Create backup
mcp-update         # Update system
```

## 📊 System Architecture

```
Internet → Cloudflare Tunnel → Nginx → Services
                                ├── React GUI (Port 3000)
                                ├── Agent 1: Scraper (Port 5000)
                                ├── Agent 2: Knowledge (Port 5001)
                                ├── Agent 3: Database (Port 5002)
                                ├── Agent 4: Transformer (Port 5003)
                                ├── Orchestrator (Port 5004)
                                ├── PostgreSQL (Port 5432)
                                ├── Redis (Port 6379)
                                ├── Prometheus (Port 9090)
                                └── Grafana (Port 3001)
```

## 🔒 Security Features

- **Cloudflare Tunnel**: Secure connection without exposing ports
- **UFW Firewall**: Only essential ports open (22, 80, 443)
- **Rate Limiting**: API and GUI rate limiting via Nginx
- **Container Isolation**: All services run in isolated containers
- **Encrypted Database**: PostgreSQL with encrypted connections
- **Security Headers**: HSTS, XSS protection, content type sniffing protection

## 📈 Resource Allocation

**Optimized for your 21GB RAM / 16 CPU server:**

| Service | Memory Limit | CPU Limit | Purpose |
|---------|-------------|-----------|---------|
| PostgreSQL | 2GB | 2 cores | Database |
| Redis | 512MB | 0.5 cores | Caching |
| Agent 1 | 2GB | 2 cores | Web scraping |
| Agent 2 | 3GB | 3 cores | Knowledge processing |
| Agent 3 | 2GB | 2 cores | Database management |
| Agent 4 | 3GB | 3 cores | Data transformation |
| Orchestrator | 2GB | 2 cores | Workflow management |
| GUI | 1GB | 1 core | React frontend |
| Nginx | 512MB | 1 core | Reverse proxy |
| Monitoring | 3GB | 3 cores | Prometheus + Grafana |
| **Total** | **~18GB** | **~16 cores** | **Perfect fit!** |

## 🔄 Backup & Recovery

### Automatic Backups
- **Schedule**: Daily at 2 AM
- **Retention**: 30 days
- **Location**: `/opt/multi-agent-mcp/data/backups/`

### Manual Backup
```bash
mcp-backup
```

### Restore from Backup
```bash
cd /opt/multi-agent-mcp/deployment
docker-compose exec postgres psql -U mcp_user -d mcp_system < /path/to/backup.sql
```

## 📝 Logs

### Log Locations
- **Application Logs**: `/opt/multi-agent-mcp/data/logs/`
- **Nginx Logs**: Docker volume `nginx_logs`
- **Container Logs**: `docker-compose logs [service]`

### Log Rotation
- **Retention**: 7 days
- **Compression**: Automatic
- **Rotation**: Daily

## 🚨 Troubleshooting

### Common Issues

**1. Services won't start**
```bash
# Check Docker status
sudo systemctl status docker

# Check logs
mcp-logs

# Restart system
mcp-restart
```

**2. Can't access via domain**
```bash
# Check Cloudflare tunnel
docker-compose logs cloudflared

# Check Nginx
docker-compose logs nginx

# Test local access
curl http://localhost
```

**3. Database connection issues**
```bash
# Check PostgreSQL
docker-compose logs postgres

# Test database connection
docker-compose exec postgres psql -U mcp_user -d mcp_system -c "SELECT 1;"
```

**4. High memory usage**
```bash
# Check resource usage
mcp-status

# Restart specific service
docker-compose restart agent2
```

### Health Checks

All services include health checks:
```bash
# Check all service health
docker-compose ps

# Manual health check
curl https://mcp.visionvation.com/health
```

## 🔧 Customization

### Adding Custom Agents
1. Create agent directory in `/opt/multi-agent-mcp/agents/`
2. Add service to `docker-compose.yml`
3. Update Nginx configuration
4. Restart system

### Scaling Services
Edit resource limits in `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      memory: 4G  # Increase memory
      cpus: '4'   # Increase CPU
```

## 📞 Support

### System Information
```bash
# Get system info for support
echo "=== System Info ==="
uname -a
docker --version
docker-compose --version
mcp-status
```

### Useful Commands
```bash
# Real-time resource monitoring
htop

# Disk usage
df -h

# Network connections
netstat -tulpn

# Docker system info
docker system df
docker system prune  # Clean up unused resources
```

## 🎯 Next Steps

1. **Configure OpenAI API**: Add your API key to `.env`
2. **Set up monitoring alerts**: Configure Grafana notifications
3. **Create workflows**: Use the GUI to create automation workflows
4. **Upload documents**: Start building your knowledge base
5. **Test transformations**: Try BestBuy → Walmart data conversion

## 📚 Additional Resources

- **User Guide**: `/opt/multi-agent-mcp/docs/USER_GUIDE.md`
- **API Documentation**: `/opt/multi-agent-mcp/docs/API_DOCUMENTATION.md`
- **Architecture Details**: `/opt/multi-agent-mcp/docs/architecture_specification.md`

---

**Your Multi-Agent MCP System is ready for production use!** 🚀


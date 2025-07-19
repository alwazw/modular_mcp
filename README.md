# Modular Multi-Agent MCP System

A comprehensive, modular multi-agent system built for data collection, knowledge management, database operations, and intelligent data transformation. Features a ChatGPT-style web interface with automatic agent routing and n8n integration.

![Multi-Agent MCP System](https://img.shields.io/badge/Status-Production%20Ready-green)
![Docker](https://img.shields.io/badge/Docker-Supported-blue)
![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04-orange)

## 🚀 Quick Start

### One-Command Installation

```bash
# Clone and install on your Ubuntu server
git clone https://github.com/alwazw/modular_mcp.git
cd modular_mcp/deployment
chmod +x scripts/install.sh
./scripts/install.sh
```

### Access Your System
- **Main GUI**: https://mcp.visionvation.com
- **n8n Workflows**: https://mcp.visionvation.com/n8n
- **Monitoring**: https://mcp.visionvation.com/grafana
- **API Docs**: https://mcp.visionvation.com/docs

## 🤖 Agent Architecture

### **Agent 1: Web Scraper & Data Collector**
- Persistent browser sessions with login support
- Multi-format file processing (PDF, Word, Excel, CSV, images)
- Automated data collection and scraping
- **Port**: 5000 | **URL**: `/agent1/`

### **Agent 2: Knowledge Base Creator**
- Document processing and chunking
- Vector embeddings with OpenAI integration
- Semantic search capabilities
- Knowledge base management
- **Port**: 5001 | **URL**: `/agent2/`

### **Agent 3: Database Manager**
- Multi-database support (PostgreSQL, MySQL, MongoDB)
- Automated backup scheduling
- Analytics and reporting
- Connection management with encryption
- **Port**: 5002 | **URL**: `/agent3/`

### **Agent 4: Intelligent Data Transformer**
- AI-powered field mapping (BestBuy ↔ Walmart templates)
- Pattern recognition and learning
- Business rules validation
- Batch processing capabilities
- **Port**: 5003 | **URL**: `/agent4/`

### **System Orchestrator**
- Workflow management and execution
- Agent coordination and health monitoring
- n8n integration with webhook support
- Real-time system metrics
- **Port**: 5004 | **URL**: `/orchestrator/`

### **n8n Workflow Automation**
- Visual workflow builder
- Multi-agent task orchestration
- Webhook triggers and API integrations
- Scheduled and event-driven automation
- **Port**: 5678 | **URL**: `/n8n/`

## 🎨 Features

### **ChatGPT-Style Interface**
- Intelligent request routing to appropriate agents
- Real-time chat with visual agent indicators
- File upload with drag & drop support
- Mobile-responsive design

### **Smart Agent Routing**
- **"Upload this file to knowledge base"** → Agent 1
- **"What were the last 3 documents?"** → Agent 2  
- **"How many laptops were sold last week?"** → Agent 3
- **"Transform BestBuy data to Walmart format"** → Agent 4

### **Production Features**
- **Cloudflare Tunnel Integration**
- **Docker Compose orchestration**
- **Automated SSL with Let's Encrypt**
- **Comprehensive monitoring (Prometheus + Grafana)**
- **Automated backups and log rotation**
- **Rate limiting and security headers**

## 📊 System Requirements

### **Minimum Requirements**
- Ubuntu 20.04+ (optimized for 24.04)
- 8GB RAM, 4 CPU cores
- 100GB disk space
- Docker & Docker Compose

### **Recommended (Production)**
- Ubuntu 24.04 LTS
- 16GB+ RAM, 8+ CPU cores  
- 256GB+ SSD storage
- Cloudflare Tunnel or reverse proxy

### **Tested Configuration**
- ✅ Ubuntu 24.04, 21GB RAM, 16 cores, 256GB disk
- ✅ Cloudflare Tunnel with custom domain
- ✅ Production workloads with high availability

## 🛠️ Installation Options

### **Option 1: Automated Installation (Recommended)**
```bash
git clone https://github.com/your-username/modular_mcp.git
cd modular_mcp/deployment
./scripts/install.sh
```

### **Option 2: Docker Compose**
```bash
git clone https://github.com/your-username/modular_mcp.git
cd modular_mcp/deployment
cp .env.example .env
# Edit .env with your settings
docker-compose up -d
```

### **Option 3: Manual Setup**
See [deployment/README.md](deployment/README.md) for detailed instructions.

## ⚙️ Configuration

### **Environment Variables**
```env
# Database
DB_PASSWORD=your_secure_password

# OpenAI API (for AI features)
OPENAI_API_KEY=sk-your-api-key

# Domain & SSL
DOMAIN_NAME=mcp.yourdomain.com
SSL_EMAIL=admin@yourdomain.com

# Monitoring
GRAFANA_PASSWORD=your_grafana_password
```

### **Cloudflare Tunnel Setup**
```yaml
# Already configured for mcp.visionvation.com
cloudflared:
  image: cloudflare/cloudflared:latest
  command: tunnel --no-autoupdate run --token YOUR_TUNNEL_TOKEN
```

## 🔧 Management

### **System Control**
```bash
mcp-start          # Start all services
mcp-stop           # Stop all services  
mcp-restart        # Restart system
mcp-status         # Show system status
```

### **Monitoring & Logs**
```bash
mcp-logs           # View all logs
mcp-logs agent1    # View specific agent
mcp-status         # Resource usage
```

### **Backup & Maintenance**
```bash
mcp-backup         # Create full backup
mcp-update         # Update system
```

## 🌐 API Endpoints

### **Core APIs**
- **GET** `/api/orchestrator/status` - System health
- **POST** `/api/orchestrator/workflows` - Create workflow
- **GET** `/api/orchestrator/agents` - List agents

### **Agent-Specific APIs**
- **POST** `/api/agent1/scrape` - Web scraping
- **POST** `/api/agent1/upload` - File upload
- **GET** `/api/agent2/search` - Knowledge search
- **POST** `/api/agent2/documents` - Add document
- **GET** `/api/agent3/analytics` - Database analytics
- **POST** `/api/agent4/transform` - Data transformation

## 🔒 Security

### **Built-in Security**
- Container isolation with resource limits
- Rate limiting (10 req/s API, 30 req/s GUI)
- Security headers (HSTS, XSS protection, etc.)
- Encrypted database connections
- UFW firewall configuration

### **Cloudflare Integration**
- Zero-trust network access
- DDoS protection
- SSL/TLS termination
- Geographic restrictions

## 📈 Monitoring

### **Grafana Dashboards**
- System resource utilization
- Agent performance metrics
- Database query performance
- Error rates and response times

### **Prometheus Metrics**
- Custom application metrics
- Container resource usage
- Network and disk I/O
- Health check status

## 🔄 Workflows & n8n Integration

### **Pre-built Workflows**
1. **Web Scraping Pipeline** - URL → Data → Knowledge Base
2. **Document Processing** - Upload → Extract → Index → Search
3. **Data Transformation** - BestBuy → Walmart format conversion
4. **Analytics Pipeline** - Query → Process → Report → Alert

### **n8n Integration**
- Webhook endpoints for workflow triggers
- Agent task routing and execution
- Real-time status monitoring
- Error handling and retry logic

## 🚀 Use Cases

### **E-commerce Data Management**
- Product catalog synchronization
- Multi-platform listing management
- Inventory tracking and analytics
- Price monitoring and optimization

### **Knowledge Management**
- Document processing and indexing
- Semantic search across content
- Automated content categorization
- FAQ and support automation

### **Data Integration**
- Multi-source data collection
- Format standardization
- Quality validation and cleansing
- Automated reporting and dashboards

## 📚 Documentation

- **[Deployment Guide](deployment/README.md)** - Complete installation instructions
- **[User Guide](docs/USER_GUIDE.md)** - How to use the system
- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete API reference
- **[Architecture Overview](docs/architecture_specification.md)** - System design details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### **Getting Help**
- 📖 Check the [documentation](docs/)
- 🐛 Report issues on [GitHub Issues](https://github.com/your-username/modular_mcp/issues)
- 💬 Join our [Discord community](https://discord.gg/your-invite)

### **System Status**
- 🟢 **Production Ready** - Tested on Ubuntu 24.04
- 🟢 **Docker Supported** - Full containerization
- 🟢 **Cloud Ready** - AWS, GCP, Azure compatible
- 🟢 **Monitoring Included** - Prometheus + Grafana

---

**Built with ❤️ for the Multi-Agent MCP Community**

[![Deploy to Server](https://img.shields.io/badge/Deploy-One%20Click-success)](deployment/scripts/install.sh)
[![Docker Hub](https://img.shields.io/badge/Docker-Hub-blue)](https://hub.docker.com/r/your-username/modular-mcp)
[![Documentation](https://img.shields.io/badge/Docs-Complete-green)](docs/)


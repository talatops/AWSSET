# 🚀 AWSSET - AI-Powered Cloud Management Platform

<div align="center">

<!-- AWSSET Logo -->
<img src="logo/awsset-logo-modern.svg" alt="AWSSET Logo" width="360" height="120">

<br>

![Version](https://img.shields.io/badge/version-2.1.0-blue?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)

**Revolutionize your AWS management with AI-powered cloud mastery**

[🚀 Quick Start](#-quick-start) • [📖 Features](#-features) • [🏗️ Architecture](#️-architecture) • [🔧 Configuration](#-configuration) • [📱 Usage](#-usage) • [🤝 Contributing](#-contributing)

</div>

---

## 📝 **Overview**

AWSSET is a comprehensive, AI-powered platform that transforms how you interact with Amazon Web Services. Say goodbye to complex console navigation and hello to natural language AWS management. With real-time WebSocket connections, intelligent cost optimization, and advanced security monitoring, AWSSET makes AWS accessible to everyone.

### 🎯 **Why AWSSET?**

- **🗣️ Natural Language Interface**: Manage AWS resources using plain English
- **⚡ Real-time Updates**: Live data streaming via WebSocket connections
- **🧠 AI-Powered Insights**: Smart recommendations for cost, security, and performance
- **🛡️ Enterprise Security**: JWT authentication with OAuth integration
- **📊 Intelligent Analytics**: CloudTrail analysis with AI-powered anomaly detection
- **💰 Cost Optimization**: Automated budget management and savings recommendations
- **🔔 Smart Notifications**: Multi-channel alerts with intelligent escalation

---

## ✨ **Features**

### 🤖 **AI-Powered Management**
- **Conversational Interface**: Natural language commands for all AWS operations
- **Groq AI Integration**: Advanced language model for intelligent responses
- **CloudTrail Analysis**: AI-powered security and cost anomaly detection
- **Smart Recommendations**: Automated optimization suggestions

### ⚡ **Real-time Operations**
- **WebSocket Streaming**: Live AWS statistics and status updates
- **Instant Notifications**: Real-time alerts for critical events
- **Live Dashboard**: Auto-updating metrics and charts
- **Performance Monitoring**: Real-time resource utilization tracking

### 🛡️ **Security & Compliance**
- **JWT Authentication**: Secure token-based authentication
- **OAuth Integration**: Google and Proton email OAuth support
- **Encrypted Storage**: AES-256 encryption for sensitive data
- **Audit Logging**: Comprehensive activity tracking
- **Role-based Access**: Granular permission management

### 💰 **Cost Management**
- **Budget Monitoring**: Intelligent budget alerts and forecasting
- **Usage Analytics**: Detailed cost breakdown and trend analysis
- **Optimization Recommendations**: AI-powered cost-saving suggestions
- **Unused Resource Detection**: Automatic identification of idle resources

### 🏗️ **Infrastructure Management**
- **EC2 Management**: Complete instance lifecycle management
- **S3 Operations**: Bucket management and file operations
- **Lambda Functions**: Serverless function deployment and monitoring
- **RDS Databases**: Database provisioning and management
- **IAM Security**: User, role, and policy management

### 🔮 **AI-Powered Predictive Operations** *(Coming Soon)*
- **Predictive Scaling**: AI predicts when you'll need more resources
- **Cost Forecasting**: Machine learning predicts future spending with 95% accuracy
- **Failure Prevention**: AI predicts potential system failures before they happen
- **Auto-optimization**: Intelligent resource optimization based on usage patterns
- **Performance Prediction**: Forecast resource bottlenecks and scaling needs

### 💬 **Natural Language Infrastructure as Code** *(Coming Soon)*
- **Chat-to-Infrastructure**: Generate complete Terraform/CloudFormation from chat
- **AI Code Review**: Automated security and best practice analysis
- **Template Translation**: Convert between CloudFormation, Terraform, and CDK
- **Smart Customization**: AI-assisted template modification and optimization

### 📊 **Advanced Analytics**
- **Custom Dashboards**: Personalized monitoring dashboards
- **Performance Metrics**: Detailed resource utilization analytics
- **Trend Analysis**: Historical data analysis and forecasting
- **Service Statistics**: Comprehensive multi-service monitoring

---

## 🏗️ **Architecture**

### **System Overview**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   AWS Services  │
│   (React)       │◄──►│   (FastAPI)      │◄──►│   (boto3)       │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │ Dashboard   │ │    │ │ AI Engine    │ │    │ │ EC2         │ │
│ │ Chat UI     │ │    │ │ WebSocket    │ │    │ │ S3          │ │
│ │ Real-time   │ │    │ │ Auth Service │ │    │ │ Lambda      │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ │ RDS         │ │
└─────────────────┘    └──────────────────┘    │ │ CloudTrail  │ │
                                               │ └─────────────┘ │
                                               └─────────────────┘
```

### **Technology Stack**

#### **Frontend**
- **Framework**: React 18 with modern hooks
- **UI Library**: Material-UI (MUI) v5
- **State Management**: Context API with custom hooks
- **Real-time**: Native WebSocket integration
- **Charts**: Recharts for data visualization
- **Animation**: Framer Motion for smooth UX

#### **Backend**
- **Framework**: FastAPI (Python 3.9+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT with OAuth integration
- **AI Engine**: Groq API for natural language processing
- **AWS SDK**: boto3 for AWS service integration
- **Real-time**: WebSocket for live data streaming

#### **Infrastructure**
- **Containerization**: Docker & Docker Compose
- **Database**: PostgreSQL 13+
- **Caching**: Redis for session management
- **Web Server**: Nginx for production deployment
- **Monitoring**: Structured logging with JSON output

---

## 🚀 **Quick Start**

### **Prerequisites**
- Docker and Docker Compose
- AWS Account with programmatic access
- Node.js 16+ (for development)
- Python 3.9+ (for development)

### **1. Clone Repository**
```bash
git clone <repository-url>
cd AWSSET
```

### **2. Environment Configuration**
```bash
# Copy environment template
cp .docker.env.example .docker.env

# Edit configuration (see Configuration section)
nano .docker.env
```

### **3. Launch Application**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### **4. Access Application**
- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

### **5. Initial Setup**
1. Create an account using OAuth (Google/Proton)
2. Configure AWS credentials in Settings
3. Start chatting with your AWS infrastructure!

---

## 🔧 **Configuration**

### **Environment Variables**

#### **Database Configuration**
```bash
# PostgreSQL Database
POSTGRES_DB=awschatbot
POSTGRES_USER=chatbot_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

#### **Authentication**
```bash
# JWT Configuration
SECRET_KEY=your_super_secret_jwt_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
PROTON_CLIENT_ID=your_proton_client_id
PROTON_CLIENT_SECRET=your_proton_client_secret
```

#### **AI Configuration**
```bash
# Groq AI Configuration
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama3-8b-8192
GROQ_TEMPERATURE=0.1
GROQ_MAX_TOKENS=4096

# Chatbot Personality
CHATBOT_NAME=CloudGenie
CHATBOT_PERSONALITY=expert_aws_solutions_architect
```

#### **Security & Monitoring**
```bash
# Security
IP_WHITELIST=127.0.0.1,localhost
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=100

# Logging
LOG_LEVEL=INFO
ENABLE_STRUCTURED_LOGGING=true
```

### **AWS Credentials Setup**

#### **Method 1: Through Web Interface (Recommended)**
1. Log in to the application
2. Navigate to Settings → AWS Configuration
3. Enter your AWS Access Key ID and Secret Access Key
4. Select your preferred region
5. Test connection

#### **Method 2: Environment Variables**
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
```

#### **Required AWS Permissions**
Your AWS credentials need the following permissions:
- `ec2:*` - EC2 management
- `s3:*` - S3 operations
- `lambda:*` - Lambda functions
- `rds:*` - RDS databases
- `iam:ListUsers`, `iam:ListRoles` - IAM read access
- `cloudtrail:LookupEvents` - CloudTrail analysis
- `ce:*` - Cost Explorer access

---

## 📱 **Usage**

### **Chat Commands**

#### **EC2 Management**
```
"List all my EC2 instances"
"Launch a t2.micro instance"
"Stop instance i-1234567890abcdef0"
"Show me running instances"
"Create an instance with 8GB RAM"
```

#### **S3 Operations**
```
"Show my S3 buckets"
"Create a bucket called my-app-data"
"List files in my-documents bucket"
"Delete the old-backup bucket"
```

#### **Cost Management**
```
"What's my current AWS bill?"
"Show me this month's costs"
"Find unused resources"
"Set a budget of $500 for this month"
"Why did my costs spike yesterday?"
```

#### **Security & Monitoring**
```
"Analyze my CloudTrail logs"
"Show security anomalies"
"Check for failed login attempts"
"List all IAM users"
"Show me recent AWS activity"
```

### **Dashboard Features**

#### **Overview Dashboard**
- Real-time AWS service statistics
- Cost trends and projections
- Recent activity feed
- Quick action buttons
- Service health indicators

#### **AWS Services Tab**
- EC2 instance management
- AMI and snapshot operations
- Security group configuration
- Key pair management
- Service-specific analytics

#### **CloudGenie Chat**
- Natural language interactions
- Voice input support (coming soon)
- File attachment support
- Command history
- Real-time responses

#### **Settings Panel**
- AWS credentials management
- Notification preferences
- Theme customization
- Profile management
- Security settings

---

## 🔄 **Development**

### **Local Development Setup**

#### **Backend Development**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### **Frontend Development**
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### **Database Migrations**
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### **Testing**
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### **Code Quality**
```bash
# Python linting
flake8 backend/
black backend/

# JavaScript linting
cd frontend
npm run lint
npm run format
```

---

## 📊 **Monitoring & Logging**

### **Application Logs**
```bash
# View all logs
docker-compose logs -f

# Backend logs only
docker-compose logs -f backend

# Frontend logs only
docker-compose logs -f frontend
```

### **Health Checks**
- **Backend Health**: `GET /api/health`
- **Database Health**: `GET /api/health/db`
- **AI Service Health**: `GET /api/chat/health`
- **AWS Connectivity**: `GET /api/aws/health`

### **Performance Monitoring**
- Real-time WebSocket connection monitoring
- API response time tracking
- Database query performance
- AWS API call rate limiting

---

## 🔐 **Security**

### **Security Features**
- **JWT Authentication**: Secure token-based auth with refresh tokens
- **OAuth Integration**: Google and Proton email OAuth support
- **Data Encryption**: AES-256 encryption for sensitive data
- **Rate Limiting**: Configurable API rate limiting
- **IP Whitelisting**: Restrict access by IP address
- **HTTPS Enforcement**: TLS encryption for all communications

### **Security Best Practices**
1. **Never commit secrets** to version control
2. **Use strong passwords** for all accounts
3. **Regularly rotate** AWS access keys
4. **Enable MFA** on AWS accounts
5. **Monitor logs** for suspicious activity
6. **Keep dependencies** up to date

### **Security Checklist**
- [ ] Environment variables configured
- [ ] AWS credentials properly secured
- [ ] JWT secret key is strong and unique
- [ ] OAuth applications configured correctly
- [ ] Rate limiting enabled
- [ ] HTTPS configured for production
- [ ] Database access restricted
- [ ] Logging enabled for audit trails

---

## 🚀 **Deployment**

### **Production Deployment**

#### **1. Server Requirements**
- **CPU**: 4+ cores
- **RAM**: 8GB+ 
- **Storage**: 50GB+ SSD
- **OS**: Ubuntu 20.04+ or similar
- **Docker**: 20.10+
- **Docker Compose**: 1.29+

#### **2. Environment Setup**
```bash
# Create production environment file
cp .docker.env.example .docker.env.production

# Configure production variables
nano .docker.env.production
```

#### **3. SSL Certificate**
```bash
# Using Let's Encrypt
certbot certonly --standalone -d yourdomain.com

# Copy certificates to ssl/ directory
cp /etc/letsencrypt/live/yourdomain.com/* ssl/
```

#### **4. Deploy Application**
```bash
# Pull latest images
docker-compose pull

# Start in production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify deployment
docker-compose ps
```

### **Scaling Considerations**
- **Database**: Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
- **Load Balancing**: Use nginx or cloud load balancers
- **Auto-scaling**: Implement container orchestration (Kubernetes, ECS)
- **Monitoring**: Use Prometheus, Grafana, or cloud monitoring
- **Backup**: Automated database backups

---

## 🔮 **Roadmap**

### **🔥 Next Release (v2.1.0)**
- **CloudTrail AI Analysis**: Advanced security and cost analysis
- **Budget Management**: Intelligent budget alerts and forecasting
- **Smart Notifications**: Multi-channel alerts with escalation
- **Infrastructure Templates**: Pre-built deployment templates

### **🎯 Future Features**
- **Voice Interface**: Voice commands and responses
- **Mobile App**: Native mobile applications
- **Multi-Cloud Support**: Azure and Google Cloud integration
- **Team Collaboration**: Multi-user workspaces
- **Advanced Analytics**: Predictive insights and recommendations

### **📅 Version History**
- **v2.0.0**: Real-time WebSocket implementation, enhanced AI
- **v1.5.0**: Groq AI integration, cost optimization
- **v1.0.0**: Initial release with EC2, S3, Lambda support

---

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### **How to Contribute**
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### **Development Guidelines**
- Follow existing code style and conventions
- Write comprehensive tests for new features
- Update documentation for any changes
- Ensure all tests pass before submitting PR

### **Bug Reports**
Please use GitHub Issues to report bugs. Include:
- Detailed description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, browser, etc.)
- Screenshots if applicable

---

## 📞 **Support**

### **Getting Help**
- **Documentation**: Check this README and inline docs
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Join community discussions
- **Email**: Contact maintainers for urgent issues

### **Troubleshooting**

#### **Common Issues**

**1. Docker containers won't start**
```bash
# Check logs
docker-compose logs

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**2. AWS connection fails**
- Verify AWS credentials are correct
- Check IAM permissions
- Ensure region is correctly set
- Test credentials with AWS CLI

**3. Database connection errors**
```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

**4. Frontend build failures**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### **Third-Party Licenses**
- React: MIT License
- FastAPI: MIT License
- Material-UI: MIT License
- PostgreSQL: PostgreSQL License
- Docker: Apache 2.0 License

---

## 🙏 **Acknowledgments**

- **AWS**: For providing comprehensive cloud services
- **Groq**: For advanced AI language model capabilities
- **React Team**: For the amazing frontend framework
- **FastAPI**: For the high-performance Python framework
- **Material-UI**: For beautiful React components
- **Open Source Community**: For countless contributions and inspiration

---

## 📊 **Project Stats**

![GitHub stars](https://img.shields.io/github/stars/talatops/AWSSET?style=social)
![GitHub forks](https://img.shields.io/github/forks/talatops/AWSSET?style=social)
![GitHub issues](https://img.shields.io/github/issues/talatops/AWSSET)
![GitHub pull requests](https://img.shields.io/github/issues-pr/talatops/AWSSET)
![GitHub last commit](https://img.shields.io/github/last-commit/talatops/AWSSET)

---

<div align="center">

[⭐ Star us on GitHub](https://github.com/talatops/AWSSET) • [🐛 Report Bug](https://github.com/talatops/AWSSET/issues) • [💡 Request Feature](https://github.com/talatops/AWSSET/issues/new)

</div>

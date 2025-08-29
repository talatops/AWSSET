# Contributing to AWS Chatbot

Thank you for your interest in contributing to AWS Chatbot! We welcome contributions from the community and are excited to see what you'll build.

## 🤝 **How to Contribute**

### **Types of Contributions**
We welcome the following types of contributions:
- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation improvements
- 🧪 Test coverage improvements
- 🔧 Performance optimizations
- 🎨 UI/UX improvements
- 🌐 Translations

## 🚀 **Getting Started**

### **1. Fork and Clone**
```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/aws-chatbot.git
cd aws-chatbot

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/aws-chatbot.git
```

### **2. Set Up Development Environment**
```bash
# Copy environment template
cp .docker.env.example .docker.env

# Edit configuration with your values
nano .docker.env

# Start development environment
docker-compose up -d

# Verify setup
curl http://localhost:8000/api/health
```

### **3. Create a Branch**
```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

## 📋 **Development Guidelines**

### **Code Style**

#### **Python (Backend)**
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write docstrings for all functions and classes
- Maximum line length: 88 characters (Black formatter)

```python
from typing import Dict, List, Optional

async def fetch_aws_resources(
    service_name: str, 
    region: Optional[str] = None
) -> Dict[str, List[str]]:
    """
    Fetch AWS resources for a specific service.
    
    Args:
        service_name: Name of the AWS service
        region: AWS region (optional, defaults to user's region)
        
    Returns:
        Dictionary containing resource lists
    """
    # Implementation here
    pass
```

#### **JavaScript/React (Frontend)**
- Use ES6+ features and modern React patterns
- Follow React hooks best practices
- Use meaningful component and variable names
- Use TypeScript for new components when possible

```jsx
import React, { useState, useEffect, useCallback } from 'react';

const AWSResourceManager = ({ serviceType, onResourceUpdate }) => {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchResources = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch logic here
    } catch (error) {
      console.error('Failed to fetch resources:', error);
    } finally {
      setLoading(false);
    }
  }, [serviceType]);

  useEffect(() => {
    fetchResources();
  }, [fetchResources]);

  return (
    // Component JSX
  );
};
```

### **Testing Requirements**

#### **Backend Tests**
```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_ec2_service.py
```

#### **Frontend Tests**
```bash
# Run all tests
cd frontend
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test -- ComponentName.test.js
```

#### **Test Coverage Requirements**
- New features must have **>90% test coverage**
- Bug fixes must include tests that prevent regression
- Critical paths must have integration tests

### **Documentation Standards**

#### **Code Documentation**
- All functions must have docstrings
- Complex algorithms need inline comments
- API endpoints must be documented with examples

#### **User Documentation**
- Update README.md for new features
- Add/update chat command examples
- Include configuration instructions

## 🔄 **Development Workflow**

### **1. Before Starting Work**
```bash
# Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main
git push origin main

# Create feature branch
git checkout -b feature/your-feature
```

### **2. During Development**
```bash
# Make small, focused commits
git add .
git commit -m "feat: add CloudTrail analysis endpoint"

# Push regularly
git push origin feature/your-feature
```

### **3. Before Submitting PR**
```bash
# Run all tests
cd backend && pytest
cd frontend && npm test

# Check code formatting
cd backend && black . && flake8 .
cd frontend && npm run lint

# Update documentation if needed
# Add entries to CHANGELOG.md
```

## 📝 **Pull Request Process**

### **PR Requirements**
- [ ] **Descriptive title** following conventional commit format
- [ ] **Detailed description** of changes made
- [ ] **Test coverage** for new functionality
- [ ] **Documentation updates** if applicable
- [ ] **No breaking changes** without major version bump
- [ ] **All tests passing** in CI/CD pipeline
- [ ] **Code review** from at least one maintainer

### **PR Template**
```markdown
## Description
Brief description of what this PR does.

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## How Has This Been Tested?
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Screenshots (if applicable)
Add screenshots to help explain your changes.

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code where necessary
- [ ] I have made corresponding changes to documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
```

## 🐛 **Bug Reports**

### **Before Reporting**
1. Search existing issues to avoid duplicates
2. Try to reproduce the bug with minimal steps
3. Test on the latest version

### **Bug Report Template**
```markdown
## Bug Description
A clear description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- OS: [e.g. Ubuntu 20.04]
- Browser: [e.g. Chrome 96]
- Version: [e.g. v2.0.0]
- Docker version: [e.g. 20.10.12]

## Additional Context
Add any other context about the problem here.

## Logs
```
Include relevant log output here
```
```

## ✨ **Feature Requests**

### **Feature Request Template**
```markdown
## Feature Description
A clear description of what the feature should do.

## Use Case
Describe the problem this feature would solve.

## Proposed Solution
Describe how you envision this feature working.

## Alternatives Considered
Other approaches you've considered.

## Additional Context
Any other context or screenshots about the feature request.
```

## 🚦 **Development Standards**

### **Commit Message Convention**
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```bash
feat(chat): add voice input support
fix(aws): resolve EC2 instance state sync issue
docs(readme): update installation instructions
test(backend): add CloudTrail service tests
```

### **Branch Naming Convention**
- `feature/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `docs/update-readme` - Documentation updates
- `refactor/service-restructure` - Code refactoring
- `test/add-integration-tests` - Test additions

### **Version Management**
We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## 🔒 **Security**

### **Security Guidelines**
- Never commit sensitive information (API keys, passwords, etc.)
- Use environment variables for configuration
- Follow secure coding practices
- Report security vulnerabilities privately

### **Reporting Security Issues**
If you discover a security vulnerability, please email us directly at `security@awschatbot.com` instead of creating a public issue.

## 📚 **Resources**

### **Useful Links**
- [AWS SDK Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs)
- [Material-UI Documentation](https://mui.com/)
- [Docker Documentation](https://docs.docker.com/)

### **Development Tools**
- **Code Formatting**: Black (Python), Prettier (JavaScript)
- **Linting**: Flake8 (Python), ESLint (JavaScript)
- **Testing**: pytest (Python), Jest (JavaScript)
- **Type Checking**: mypy (Python), TypeScript (JavaScript)

## 🎉 **Recognition**

Contributors will be recognized in the following ways:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes for significant contributions
- Special recognition for major features or improvements

## 📞 **Getting Help**

If you need help with development:
1. Check the documentation first
2. Search existing issues and discussions
3. Ask in GitHub Discussions
4. Join our community chat (link coming soon)

## 📄 **License**

By contributing to AWS Chatbot, you agree that your contributions will be licensed under the same MIT License that covers the project.

---

Thank you for contributing to AWS Chatbot! Your contributions help make AWS management more accessible to everyone. 🚀

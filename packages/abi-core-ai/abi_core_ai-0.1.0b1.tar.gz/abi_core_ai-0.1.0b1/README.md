# ABI-Core 🤖

**Agent-Based Infrastructure Core** - A comprehensive framework for building, deploying, and managing AI agent systems with semantic layers and security policies.

> ⚠️ **Beta Release**: This is a beta version. APIs may change and some features are experimental.

## 🚀 Quick Start

### Installation

```bash
pip install abi-core-ai
```

### Create Your First Project

```bash
# Create a new ABI project
abi-core create project my-ai-system

# Navigate to your project
cd my-ai-system

# Create an agent
abi-core create agent my-agent

# Run your project
docker-compose up
```

## 🎯 What is ABI-Core?

ABI-Core is a production-ready framework for building **Agent-Based Infrastructure** systems that combine:

- **🤖 AI Agents**: LangChain-powered agents with A2A (Agent-to-Agent) communication
- **🧠 Semantic Layer**: Vector embeddings and knowledge management
- **🔒 Security**: OPA-based policy enforcement and access control
- **🌐 Web Interfaces**: FastAPI-based REST APIs and real-time dashboards
- **📦 Containerization**: Docker-ready deployments with orchestration

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Agents     │◄──►│ Semantic Layer  │◄──►│   Guardian      │
│                 │    │                 │    │   Security      │
│ • LangChain     │    │ • Vector DB     │    │ • OPA Policies  │
│ • A2A Protocol  │    │ • Embeddings    │    │ • Access Control│
│ • Custom Logic  │    │ • Knowledge     │    │ • Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Web Interface  │
                    │                 │
                    │ • FastAPI       │
                    │ • Real-time UI  │
                    │ • Monitoring    │
                    └─────────────────┘
```

## 📋 Features

### 🤖 Agent System
- **Multi-Agent Architecture**: Create specialized agents for different tasks
- **A2A Communication**: Agents can communicate and collaborate
- **LangChain Integration**: Leverage the full LangChain ecosystem
- **Custom Tools**: Extend agents with domain-specific capabilities

### 🧠 Semantic Layer
- **Vector Storage**: Weaviate integration for semantic search
- **Embedding Management**: Automatic text-to-vector conversion
- **Knowledge Graphs**: NetworkX-based relationship modeling
- **Context Awareness**: Agents understand semantic relationships

### 🔒 Security & Governance
- **Policy Engine**: Open Policy Agent (OPA) integration
- **Access Control**: Fine-grained permissions and roles
- **Audit Logging**: Complete activity tracking
- **Compliance**: Built-in security best practices

### 🌐 Web & APIs
- **REST APIs**: FastAPI-based service endpoints
- **Real-time Updates**: WebSocket support for live data
- **Admin Dashboard**: Monitor and manage your agent system
- **Custom UIs**: Build domain-specific interfaces

## 🛠️ CLI Commands

### Project Management
```bash
# Create new project
abi-core create project <name>

# Project status
abi-core status

# Run project services
abi-core run
```

### Agent Development
```bash
# Create new agent
abi-core create agent <name>

# List agents
abi-core info agents

# Agent-specific operations
abi-core agent <name> status
```

### Services
```bash
# Create semantic layer service
abi-core create service semantic-layer

# Create security guardian
abi-core create service guardian
```

## 📁 Project Structure

When you create a new project, you get:

```
my-project/
├── agents/                 # Your AI agents
│   └── my-agent/
│       ├── agent.py       # Agent implementation
│       ├── main.py        # Entry point
│       └── models.py      # Data models
├── services/              # Supporting services
│   ├── semantic-layer/    # Vector DB & embeddings
│   └── guardian/          # Security & policies
├── config/                # Configuration
│   └── config.py
├── docker-compose.yml     # Container orchestration
└── README.md             # Project documentation
```

## 🔧 Configuration

ABI-Core uses environment variables and YAML configuration:

```yaml
# .abi/runtime.yaml
agents:
  my-agent:
    model: "llama3.2:3b"
    port: 8000
    
semantic_layer:
  provider: "weaviate"
  host: "localhost:8080"
  
security:
  opa_enabled: true
  policies_path: "./policies"
```

## 🚀 Deployment

### Docker (Recommended)
```bash
# Build and run all services
docker-compose up --build

# Scale specific services
docker-compose up --scale my-agent=3
```

### Kubernetes
```bash
# Generate K8s manifests
abi-core deploy kubernetes

# Apply to cluster
kubectl apply -f ./k8s/
```

## 🧪 Examples

### Simple Agent
```python
from abi_core.agent.agent import AbiAgent
from abi_core.common.utils import abi_logging

class MyAgent(AbiAgent):
    def __init__(self):
        super().__init__(
            agent_name='my-agent',
            description='A helpful AI assistant'
        )
    
    async def stream(self, query: str, context_id: str, task_id: str):
        abi_logging(f"Processing: {query}")
        
        # Your agent logic here
        response = await self.llm.ainvoke(query)
        
        yield {
            'content': response.content,
            'response_type': 'text',
            'is_task_completed': True
        }
```

### Agent Communication
```python
# Agent A sends message to Agent B
await self.send_message(
    target_agent="agent-b",
    message="Process this data",
    data={"items": [1, 2, 3]}
)
```

## 📚 Documentation

- **[Getting Started Guide](https://docs.abi-core.dev/getting-started)**
- **[Agent Development](https://docs.abi-core.dev/agents)**
- **[Semantic Layer](https://docs.abi-core.dev/semantic)**
- **[Security & Policies](https://docs.abi-core.dev/security)**
- **[API Reference](https://docs.abi-core.dev/api)**

## 🤝 Contributing

We welcome contributions! This is a beta release, so your feedback is especially valuable.

### Development Setup
```bash
git clone https://github.com/Joselo-zn/abi-core
cd abi-core
uv sync --dev
```

### Running Tests
```bash
uv run pytest
```

## 📄 License

Apache 2.0 License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/Joselo-zn/abi-core/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Joselo-zn/abi-core/discussions)
- **Email**: jl.mrtz@gmail.com

## 🗺️ Roadmap

- [ ] **v0.2.0**: Enhanced agent orchestration
- [ ] **v0.3.0**: Advanced semantic search
- [ ] **v0.4.0**: Multi-cloud deployment
- [ ] **v1.0.0**: Production-ready stable release

---

**Built with ❤️ by the ABI-Core Team**
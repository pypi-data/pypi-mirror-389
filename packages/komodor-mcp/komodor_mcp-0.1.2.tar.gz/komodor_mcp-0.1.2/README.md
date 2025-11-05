# Komodor MCP Server

A comprehensive MCP (Model Context Protocol) server for Komodor that provides AI assistants with intelligent access to Kubernetes infrastructure monitoring, health analysis, and cost optimization data.

## 🚀 Features

- **🔧 9 Powerful Tools**: Complete Kubernetes infrastructure analysis and monitoring
- **📊 Health Monitoring**: Real-time cluster health risks and violation analysis
- **💰 Cost Optimization**: Right-sizing recommendations for services and containers
- **🔍 Root Cause Analysis**: AI-powered Klaudia RCA for incident investigation
- **⚡ FastMCP Implementation**: Modern async architecture with Starlette
- **🛡️ Type-Safe**: Full type hints and Pydantic models
- **🌐 Dual Transport**: HTTP and stdio transport modes
- **📝 Smart Prompts**: Pre-built analysis templates for common scenarios

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- Komodor account and API key
- `uv` package manager (recommended) or `pip`

### Quick Install

```bash
# Clone the repository
git clone https://github.com/komodor/komodor-mcp.git
cd komodor-mcp

# Install dependencies
uv sync

# Or with pip
pip install -e .
```

### Environment Setup

Create a `.env` file in the project root:

```bash
# Required: Your Komodor API key
KOMODOR_API_KEY=your-api-key-here

# Optional: API base URL (defaults to production)
KOMODOR_API_BASE_URL=https://api.komodor.com

# Optional: Server configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8002
LOG_LEVEL=INFO
```

## 🚀 Quick Start

### HTTP Transport (Recommended)

```bash
# Start the server
uv run komodor-mcp

# Server will be available at http://localhost:8002
# Health check: http://localhost:8002/health
# MCP endpoint: http://localhost:8002/mcp
```

### Stdio Transport (Development)

```bash
# For direct MCP client integration
uv run komodor-mcp --transport stdio
```

## 🛠️ Available Tools

### Cluster Management
- **`get_clusters()`** - Retrieve all clusters in your Komodor workspace
- **`get_services_by(cluster, namespaces, service_kind, status)`** - Search and filter services by cluster, namespace, or type

### Health Analysis
- **`get_health_risks(cluster_name, namespace, status, check_category, page_size, offset)`** - Get health violations and risks across clusters
- **`get_health_risk_data(risk_id)`** - Detailed analysis of specific health violations
- **`get_service_yaml(cluster, namespace, kind, name)`** - Retrieve Kubernetes YAML configurations

### Root Cause Analysis
- **`trigger_klaudia_rca(cluster, namespace, resource_kind, resource_name, wait)`** - Initiate AI-powered root cause analysis
- **`get_klaudia_rca_results(session_id, wait)`** - Retrieve RCA results and recommendations

## 📊 Resources

- **`komodor://clusters`** - Live cluster information resource

## 🎯 Smart Prompts

### Komodor Health Overview
**Purpose**: Comprehensive health analysis of cluster violations and unhealthy services with actionable recommendations.

**What it does**:
- Analyzes health risks across clusters and namespaces
- Identifies unhealthy services and patterns
- Provides prioritized action plans
- Categorizes issues by severity (Critical, High, Medium, Low)
- Offers immediate and long-term recommendations

**Parameters**:
- `cluster_name` (required): Target cluster for analysis
- `namespace` (optional): Specific namespace to focus on

**Use when**: You need a complete health assessment of your Kubernetes infrastructure.

### Komodor Root Cause Analysis
**Purpose**: Perform deep-dive RCA on specific health issues using Klaudia AI analysis.

**What it does**:
- Initiates AI-powered root cause analysis using Klaudia
- Analyzes service configuration and health risks
- Provides technical analysis with confidence levels
- Offers step-by-step resolution plans
- Maps dependencies and resource constraints

**Parameters**:
- `cluster_name` (required): Target cluster
- `service_name` (required): Service experiencing issues
- `namespace` (required): Service namespace
- `issue_description` (optional): Description of the problem

**Use when**: You have a specific service issue that needs deep investigation and AI-powered insights.

## 🔧 MCP Client Configuration

### Cursor IDE

Add to your `.cursor/settings.json`:

```json
{
    "mcpServers": {
        "komodor-mcp": {
            "url": "http://localhost:8002/mcp",
            "headers": {
                "Authorization": "your-api-key-here"
            }
        }
    }
}
```

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
    "mcpServers": {
        "komodor-mcp": {
            "command": "uv",
            "args": ["run", "komodor-mcp", "--transport", "stdio"],
            "env": {
                "KOMODOR_API_KEY": "your-api-key-here"
            }
        }
    }
}
```

### Generic MCP Client

For HTTP transport:
```json
{
    "url": "http://localhost:8002/mcp",
    "headers": {
        "Authorization": "your-api-key-here"
    }
}
```

For stdio transport:
```json
{
    "command": "uv",
    "args": ["run", "komodor-mcp", "--transport", "stdio"],
    "env": {
        "KOMODOR_API_KEY": "your-api-key-here"
    }
}
```

## 🔍 Usage Examples

### Health Analysis
```python
# Get health risks for a specific cluster
health_risks = await get_health_risks(
    cluster_name=["production-cluster"],
    namespace=["default", "monitoring"],
    status=["open", "confirmed"],
    check_category=["workload", "infrastructure"],
    page_size=100,
    offset=0
)

# Get detailed violation data
violation_data = await get_health_risk_data(risk_id="7e3eeda1-b70c-44be-826d-87e68b0d3e2c")
```

### Service Management
```python
# Search for unhealthy services
unhealthy_services = await get_services_by(
    cluster="production-cluster",
    namespaces=["default", "monitoring"],
    service_kind=["Deployment", "StatefulSet"],
    status="unhealthy"
)

# Get service YAML configuration
service_yaml = await get_service_yaml(
    cluster="production-cluster",
    namespace="default",
    kind="Deployment",
    name="nginx-deployment"
)
```

### Root Cause Analysis
```python
# Trigger RCA for a specific resource
rca_response = await trigger_klaudia_rca(
    cluster="production-cluster",
    namespace="default",
    resource_kind="Deployment",
    resource_name="nginx-deployment",
    wait=True
)

# Get RCA results using session ID
rca_results = await get_klaudia_rca_results(
    session_id=rca_response.session_id,
    wait=True
)
```

### Cost Optimization
```python
# Get service-level cost recommendations
service_recommendations = await get_cost_right_sizing_per_service(
    service="nginx-deployment",
    cluster_scope=["production-cluster"],
    optimization_strategy="moderate"
)

# Get container-level recommendations
container_recommendations = await get_cost_right_sizing_per_container(
    cluster="production-cluster",
    namespace="default",
    service_kind="Deployment",
    service_name="nginx-deployment"
)
```

## 🐛 Troubleshooting

### Common Issues

**Server won't start:**
- Verify Python 3.11+ is installed
- Check that `KOMODOR_API_KEY` is set correctly
- Ensure port 8002 is available

**API authentication errors:**
- Verify your Komodor API key is valid
- Check that the API key has proper permissions
- Ensure `KOMODOR_API_BASE_URL` is correct

**MCP client connection issues:**
- For HTTP transport: Check server is running on correct port
- For stdio transport: Verify environment variables are set
- Check MCP client configuration format

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
uv run komodor-mcp
```

Enable remote debugging:
```bash
export DEBUG_MODE=true
uv run komodor-mcp
# Attach debugger to localhost:5678
```

## 📄 License

This project is licensed under the Apache License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Komodor Docs](https://docs.komodor.com)
- **Issues**: [GitHub Issues](https://github.com/komodor/komodor-mcp/issues)
- **Support**: [support@komodor.com](mailto:support@komodor.com)

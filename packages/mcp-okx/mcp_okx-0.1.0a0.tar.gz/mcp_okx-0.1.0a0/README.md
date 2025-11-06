# 🆗 OKX MCP Server

<!-- mcp-name: io.github.aahl/mcp-okx -->


## Install

### Method 1: uvx
```yaml
{
  "mcpServers": {
    "mcp-okx": {
      "command": "uvx",
      "args": ["mcp-okx"],
      "env": {
        "OKX_API_KEY": "your-okx-api-key",
        "OKX_API_SECRET": "api-secret-key",
        "OKX_PASSPHRASE": "api-passphrase",
        "OKX_TRADE_FLAG": "1" # 0: Production trading, 1: Demo trading
      }
    }
  }
}
```

### Method 2: Docker
```bash
mkdir /opt/mcp-okx
cd /opt/mcp-okx
wget https://raw.githubusercontent.com/aahl/mcp-okx/refs/heads/main/docker-compose.yml
docker-compose up -d
```
```yaml
{
  "mcpServers": {
    "mcp-okx": {
      "url": "http://0.0.0.0:8811/mcp" # Streamable HTTP
    }
  }
}
```

# MCP Server Setup Guide

## Tổng Quan

MCP (Multi-Cloud Platform) DB Server là một service riêng biệt cần được start trước khi sử dụng các tính năng DBA domain.

## Cách Start MCP Server

### Option 1: Chạy Local (Development)

```bash
# Từ project root
python -m mcp_server.run_server

# Hoặc sử dụng script
# Linux/Mac:
./scripts/start_mcp_server.sh

# Windows:
scripts\start_mcp_server.bat
```

Server sẽ chạy tại `http://localhost:8387`

### Option 2: Chạy trong Docker

MCP Server đã được thêm vào `docker-compose.yml`:

```bash
# Start MCP server cùng với backend
docker-compose up -d mcp-server backend

# Hoặc start tất cả services
docker-compose up -d
```

MCP Server sẽ accessible tại:
- **Trong Docker network**: `http://mcp-server:8387`
- **Từ host machine**: `http://localhost:8387`

## Configuration

### Environment Variables

```bash
# MCP Server Configuration
MCP_SERVER_PORT=8387
MCP_SERVER_HOST=0.0.0.0

# Backend cần biết URL của MCP Server
# Local development:
MCP_DB_SERVER_URL=http://localhost:8387

# Docker:
MCP_DB_SERVER_URL=http://mcp-server:8387
```

### Docker Compose

MCP Server service đã được config trong `docker-compose.yml`:

```yaml
mcp-server:
  container_name: bot_mcp_server
  ports:
    - "8387:8387"
  environment:
    MCP_SERVER_PORT: 8387
    MCP_SERVER_HOST: 0.0.0.0
```

Backend service sẽ tự động connect đến MCP server qua Docker network.

## Verify MCP Server is Running

```bash
# Health check
curl http://localhost:8387/health

# Expected response:
# {"status": "healthy", "service": "mcp-db-server"}
```

## Troubleshooting

### Error: "Failed to connect to MCP server"

**Nguyên nhân:**
- MCP Server chưa được start
- URL không đúng (localhost vs service name trong Docker)
- Port bị conflict

**Giải pháp:**

1. **Kiểm tra MCP Server đang chạy:**
   ```bash
   curl http://localhost:8387/health
   ```

2. **Nếu chạy trong Docker:**
   - Đảm bảo `MCP_DB_SERVER_URL=http://mcp-server:8387` trong backend environment
   - Kiểm tra cả 2 containers đều trong cùng network:
     ```bash
     docker-compose ps
     docker network inspect hub_shared_net
     ```

3. **Nếu chạy local:**
   - Đảm bảo `MCP_DB_SERVER_URL=http://localhost:8387`
   - Kiểm tra port 8387 không bị chiếm:
     ```bash
     # Windows
     netstat -ano | findstr :8387
     
     # Linux/Mac
     lsof -i :8387
     ```

### Error: "Connection test failed"

**Nguyên nhân:**
- Database connection string không đúng
- Database server không accessible từ MCP server
- Database credentials sai

**Giải pháp:**
- Kiểm tra connection string format
- Test connection trực tiếp từ MCP server container/host
- Kiểm tra firewall và network connectivity

## Development Workflow

1. **Start MCP Server:**
   ```bash
   python -m mcp_server.run_server
   ```

2. **Start Backend:**
   ```bash
   # Local
   python -m uvicorn backend.interface.api:app --reload
   
   # Docker
   docker-compose up -d backend
   ```

3. **Test Connection:**
   - Mở frontend: `http://localhost:3002/admin/dba/connections/new`
   - Nhập connection string và click "Test Connection"

## Production Deployment

Trong production, đảm bảo:
1. MCP Server chạy như một service riêng biệt
2. Backend config `MCP_DB_SERVER_URL` đúng với production URL
3. Health checks và monitoring cho MCP Server
4. Connection pooling và rate limiting





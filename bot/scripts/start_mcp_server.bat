@echo off
REM Start MCP DB Server (Windows)
REM Usage: scripts\start_mcp_server.bat

cd /d "%~dp0\.."

echo Starting MCP DB Server...
echo.

REM Set environment variables
if "%MCP_SERVER_PORT%"=="" set MCP_SERVER_PORT=8387
if "%MCP_SERVER_HOST%"=="" set MCP_SERVER_HOST=0.0.0.0

echo Configuration:
echo    Host: %MCP_SERVER_HOST%
echo    Port: %MCP_SERVER_PORT%
echo    URL: http://%MCP_SERVER_HOST%:%MCP_SERVER_PORT%
echo.

REM Start server
python -m mcp_server.run_server


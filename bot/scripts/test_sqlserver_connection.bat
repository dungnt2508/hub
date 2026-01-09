@echo off
REM Script để test kết nối SQL Server từ container (Windows)
REM Usage: docker exec -it bot_mcp_server bash /app/scripts/test_sqlserver_connection.sh <connection_string>

echo ==========================================
echo Testing SQL Server Connection from Host
echo ==========================================
echo.

REM Get IP address of host machine
echo 1. Getting host machine IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set IP=%%a
    set IP=!IP:~1!
    echo    Found IP: !IP!
    goto :found_ip
)
:found_ip

echo.
echo 2. Testing connection string formats:
echo    Option 1: sqlserver://sa:abcd1234@host.docker.internal:1444?database=master
echo    Option 2: sqlserver://sa:abcd1234@%IP%:1444?database=master
echo.

echo 3. To test from container, run:
echo    docker exec -it bot_mcp_server bash /app/scripts/test_sqlserver_connection.sh "sqlserver://sa:abcd1234@host.docker.internal:1444?database=master"
echo.

pause


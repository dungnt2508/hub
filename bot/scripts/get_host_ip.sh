#!/bin/bash
# Script để lấy IP address của host machine từ container
# Usage: docker exec -it bot_mcp_server bash /app/scripts/get_host_ip.sh

echo "=========================================="
echo "Getting Host Machine IP Address"
echo "=========================================="
echo ""

# Method 1: Try host.docker.internal (Windows/Mac Docker Desktop)
echo "1. Testing host.docker.internal..."
if ping -c 1 host.docker.internal > /dev/null 2>&1; then
    echo "   ✅ host.docker.internal is available"
    echo "   💡 Use: sqlserver://sa:password@host.docker.internal:1444?database=master"
else
    echo "   ❌ host.docker.internal is NOT available"
fi

# Method 2: Get gateway IP (usually host IP on Linux)
echo ""
echo "2. Getting Docker gateway IP (host IP on Linux)..."
GATEWAY_IP=$(ip route | grep default | awk '{print $3}' | head -1)
if [ -n "$GATEWAY_IP" ]; then
    echo "   Gateway IP: $GATEWAY_IP"
    if ping -c 1 "$GATEWAY_IP" > /dev/null 2>&1; then
        echo "   ✅ Gateway IP is reachable"
        echo "   💡 Use: sqlserver://sa:password@$GATEWAY_IP:1444?database=master"
    else
        echo "   ❌ Gateway IP is NOT reachable"
    fi
else
    echo "   ❌ Could not determine gateway IP"
fi

# Method 3: Try common host IPs
echo ""
echo "3. Common host IP addresses to try:"
echo "   - 192.168.1.1 (common router IP)"
echo "   - 192.168.0.1 (common router IP)"
echo "   - 172.17.0.1 (Docker default bridge gateway)"
echo "   - host.docker.internal (Windows/Mac Docker Desktop)"
echo ""

# Method 4: Check network interfaces
echo "4. Network interfaces in container:"
ip addr show | grep -E "inet " | awk '{print "   - " $2}'

echo ""
echo "=========================================="
echo "To find your host IP from Windows:"
echo "  ipconfig | findstr IPv4"
echo ""
echo "To find your host IP from Linux/Mac:"
echo "  hostname -I"
echo "  or"
echo "  ip addr show | grep inet"
echo "=========================================="


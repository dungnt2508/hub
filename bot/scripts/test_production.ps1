# Production Testing Helper Script (PowerShell)
# Usage: .\test_production.ps1 -ApiKey "your-api-key" -TenantId "your-tenant-id"

param(
    [string]$ApiKey = "your-api-key",
    [string]$TenantId = "your-tenant-id"
)

$ApiUrl = "http://localhost:8386/api/v1/chat"
$UserId = "550e8400-e29b-41d4-a716-446655440000"

Write-Host "=== Production Testing Script ===" -ForegroundColor Green
Write-Host ""

# Function to send request
function Send-Request {
    param(
        [string]$Message,
        [string]$SessionId = $null,
        [string]$Description
    )
    
    Write-Host "Test: $Description" -ForegroundColor Yellow
    Write-Host "Message: $Message"
    
    $body = @{
        message = $Message
        user_id = $UserId
        metadata = @{
            tenant_id = $TenantId
        }
    }
    
    if ($SessionId) {
        $body.session_id = $SessionId
    }
    
    $jsonBody = $body | ConvertTo-Json -Depth 10
    
    try {
        $response = Invoke-RestMethod -Uri $ApiUrl `
            -Method POST `
            -Headers @{
                "Content-Type" = "application/json"
                "X-API-Key" = $ApiKey
            } `
            -Body $jsonBody
        
        Write-Host "Response:"
        $response | ConvertTo-Json -Depth 10
        Write-Host ""
        
        return $response.session_id
    }
    catch {
        Write-Host "Error: $_" -ForegroundColor Red
        Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Red
        return $null
    }
}

# Test F1.1: Session Persistence
Write-Host "=== Test F1.1: Session Persistence ===" -ForegroundColor Green
Write-Host ""

$sessionId = Send-Request -Message "Tôi muốn xin nghỉ phép" -Description "F1.1.1: NEED_MORE_INFO persistence"

if (-not $sessionId) {
    Write-Host "ERROR: No session_id returned" -ForegroundColor Red
    exit 1
}

# Test F1.2: Slot Merge
Write-Host "=== Test F1.2: Slot Merge ===" -ForegroundColor Green
Write-Host ""

Send-Request -Message "từ ngày 2025-02-01" -SessionId $sessionId -Description "F1.2.1: Provide start_date"
Send-Request -Message "đến ngày 2025-02-05" -SessionId $sessionId -Description "F1.2.2: Provide end_date"
Send-Request -Message "nghỉ phép gia đình" -SessionId $sessionId -Description "F1.2.3: Provide reason (should SUCCESS)"

# Test F1.3: UNKNOWN Recovery
Write-Host "=== Test F1.3: UNKNOWN Recovery ===" -ForegroundColor Green
Write-Host ""

Send-Request -Message "xyz abc 123" -Description "F1.3.1: UNKNOWN without last_domain"

# Test F2.1: Continuation
Write-Host "=== Test F2.1: Continuation Check ===" -ForegroundColor Green
Write-Host ""

$contSession = Send-Request -Message "Tôi muốn xin nghỉ phép" -Description "F2.1.1: Start leave request"
Send-Request -Message "mai" -SessionId $contSession -Description "F2.1.2: Continue with 'mai' (should CONTINUATION)"

# Test F2.3: Next Action
Write-Host "=== Test F2.3: Next Action ===" -ForegroundColor Green
Write-Host ""

Send-Request -Message "Tôi muốn xin nghỉ phép" -Description "F2.3.1: Check next_action=ASK_SLOT"

# Test F3.1: Intent Mapping
Write-Host "=== Test F3.1: Intent Mapping From Config ===" -ForegroundColor Green
Write-Host ""

Send-Request -Message "Tìm kiếm sản phẩm workflow" -Description "F3.1.1: Catalog search (should map to catalog.search)"

# Test F3.3: Context Boost
Write-Host "=== Test F3.3: Context Boost ===" -ForegroundColor Green
Write-Host ""

$boostSession = Send-Request -Message "Tôi còn bao nhiêu ngày phép?" -Description "F3.3.1: Set last_domain=hr"
Send-Request -Message "Tìm kiếm thông tin" -SessionId $boostSession -Description "F3.3.2: Ambiguous (should boost HR)"

# Test F4.1: Slot Validation
Write-Host "=== Test F4.1: Slot Validation ===" -ForegroundColor Green
Write-Host ""

Send-Request -Message "Tôi muốn xin nghỉ phép từ ngày 32/13/2025" -Description "F4.1.1: Invalid date (should warn)"

Write-Host ""
Write-Host "=== Testing Complete ===" -ForegroundColor Green
Write-Host "Check Redis for session state:"
Write-Host "  redis-cli GET `"session:$sessionId`""

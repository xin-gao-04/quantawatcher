param(
    [string]$File = "data\\morning_brief.md",
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

if (-Not (Test-Path $File)) {
    throw "File not found: $File"
}

$content = Get-Content $File -Raw
$payload = @{ content = $content } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$BaseUrl/reports/morning-brief" -Body $payload -ContentType "application/json"
Invoke-RestMethod -Method Post -Uri "$BaseUrl/reports/morning-brief/send"

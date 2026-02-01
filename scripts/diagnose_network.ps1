param(
    [string]$Proxy = "",
    [int]$TimeoutSec = 10
)

Set-StrictMode -Version Latest

function Get-ProxyFromEnvFile {
    $envPath = Join-Path (Get-Location) ".env"
    if (-not (Test-Path $envPath)) {
        return $null
    }
    $lines = Get-Content $envPath -ErrorAction SilentlyContinue
    $https = $lines | Where-Object { $_ -match '^QW_HTTPS_PROXY=' } | Select-Object -First 1
    if ($https) {
        return $https.Split('=', 2)[1]
    }
    $http = $lines | Where-Object { $_ -match '^QW_HTTP_PROXY=' } | Select-Object -First 1
    if ($http) {
        return $http.Split('=', 2)[1]
    }
    return $null
}

function Test-ProxyPort {
    param([string]$ProxyUrl)
    try {
        $uri = [System.Uri]::new($ProxyUrl)
        if (-not $uri.Port -or $uri.Port -le 0) {
            Write-Host "Proxy port parse failed: $ProxyUrl"
            return
        }
        $result = Test-NetConnection 127.0.0.1 -Port $uri.Port -WarningAction SilentlyContinue
        Write-Host ("Proxy port {0} reachable: {1}" -f $uri.Port, $result.TcpTestSucceeded)
    } catch {
        Write-Host "Proxy port parse failed: $ProxyUrl"
    }
}

function Test-HttpRequest {
    param(
        [string]$Label,
        [string]$Url,
        [string]$ProxyUrl
    )
    try {
        if ($ProxyUrl) {
            $resp = Invoke-WebRequest -Uri $Url -Proxy $ProxyUrl -TimeoutSec $TimeoutSec
        } else {
            $resp = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSec
        }
        Write-Host ("{0} status: {1}" -f $Label, $resp.StatusCode)
    } catch {
        Write-Host ("{0} error: {1}" -f $Label, $_.Exception.Message)
    }
}

$proxyUrl = $Proxy
if (-not $proxyUrl) {
    $proxyUrl = Get-ProxyFromEnvFile
}

Write-Host ("Timestamp: {0}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
if ($proxyUrl) {
    Write-Host ("Proxy: {0}" -f $proxyUrl)
} else {
    Write-Host "Proxy: none"
}

if ($proxyUrl) {
    Test-ProxyPort -ProxyUrl $proxyUrl
}

$baiduUrl = "https://www.baidu.com"
$eastmoneyUrl = "https://82.push2.eastmoney.com/api/qt/clist/get?pn=1&pz=20&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f12&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048&fields=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152"

Test-HttpRequest -Label "Direct baidu" -Url $baiduUrl -ProxyUrl ""
Test-HttpRequest -Label "Direct eastmoney" -Url $eastmoneyUrl -ProxyUrl ""

if ($proxyUrl) {
    Test-HttpRequest -Label "Proxy baidu" -Url $baiduUrl -ProxyUrl $proxyUrl
    Test-HttpRequest -Label "Proxy eastmoney" -Url $eastmoneyUrl -ProxyUrl $proxyUrl
}

Write-Host "Tip: if eastmoney fails, try switching Clash node or adding DOMAIN-SUFFIX,eastmoney.com,PROXY."
Write-Host "Tip: auto cookie fetch uses https://quote.eastmoney.com/; verify it is reachable."

if ($proxyUrl -and $proxyUrl.StartsWith("socks", [System.StringComparison]::OrdinalIgnoreCase)) {
    Write-Host "SOCKS proxy detected; Python requests need PySocks to work with SOCKS."
}

if (Get-Command python -ErrorAction SilentlyContinue) {
    if ($proxyUrl) {
        $env:HTTP_PROXY = $proxyUrl
        $env:HTTPS_PROXY = $proxyUrl
    } else {
        Remove-Item Env:HTTP_PROXY -ErrorAction SilentlyContinue
        Remove-Item Env:HTTPS_PROXY -ErrorAction SilentlyContinue
        $env:NO_PROXY = "*"
    }
    $py = @'
import os
import traceback
import akshare as ak

print("HTTP_PROXY", os.getenv("HTTP_PROXY"))
print("HTTPS_PROXY", os.getenv("HTTPS_PROXY"))
try:
    df = ak.stock_zh_a_spot_em()
    print("akshare rows", len(df))
    print(df.head(2).to_string(index=False))
except Exception as exc:
    print("akshare error", exc)
    traceback.print_exc()
'@
    $py | python -
} else {
    Write-Host "Python not found; skip akshare check."
}

Param(
    [switch]$Build,
    [switch]$Logs
)

$ErrorActionPreference = "Stop"

function Assert-Docker {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker CLI 未找到，请先安装 Docker Desktop 并确保命令行可用。"
    }
}

function Invoke-Compose {
    Param(
        [string[]]$Args
    )

    $cmd = "docker", "compose" + $Args
    Write-Host ">> $($cmd -join ' ')" -ForegroundColor Cyan
    & docker compose @Args
}

Push-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
Push-Location ..

try {
    Assert-Docker

    if ($Build) {
        Invoke-Compose -Args @("build", "--pull")
    }

    Invoke-Compose -Args @("up", "-d")

    if ($Logs) {
        Write-Host "`n服务已启动，附加日志输出 (Ctrl+C 退出日志)" -ForegroundColor Green
        Invoke-Compose -Args @("logs", "-f")
    } else {
        Write-Host "`n⭐ 服务已启动。" -ForegroundColor Green
        Write-Host "   API:        http://localhost:8000/api/v1/docs"
        Write-Host "   前端页面:  http://localhost:8000/app"
        Write-Host "使用 -Logs 参数可跟随日志输出。例如: .\scripts\docker-up.ps1 -Logs"
    }
}
finally {
    Pop-Location
    Pop-Location
}

# Gradle File Downloader - PowerShell Scripts
# Windows 下的便捷开发脚本，等同于 Makefile

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

function Show-Help {
    Write-Host "Gradle File Downloader - 可用命令:" -ForegroundColor Green
    Write-Host ""
    Write-Host "  help        - 显示此帮助信息" -ForegroundColor Yellow
    Write-Host "  install     - 安装项目依赖" -ForegroundColor Yellow
    Write-Host "  install-dev - 安装开发依赖" -ForegroundColor Yellow
    Write-Host "  test        - 运行单元测试" -ForegroundColor Yellow
    Write-Host "  test-basic  - 运行基本功能测试" -ForegroundColor Yellow
    Write-Host "  lint        - 运行代码检查" -ForegroundColor Yellow
    Write-Host "  format      - 格式化代码" -ForegroundColor Yellow
    Write-Host "  build       - 构建项目" -ForegroundColor Yellow
    Write-Host "  run-gui     - 启动 GUI" -ForegroundColor Yellow
    Write-Host "  run-cli     - 启动 CLI (需要额外参数)" -ForegroundColor Yellow
    Write-Host "  gfd         - 使用 gfd 命令 (需要额外参数)" -ForegroundColor Yellow
    Write-Host "  clean       - 清理构建文件" -ForegroundColor Yellow
    Write-Host "  sync        - 同步依赖" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "使用示例:" -ForegroundColor Cyan
    Write-Host "  .\scripts.ps1 install" -ForegroundColor Gray
    Write-Host "  .\scripts.ps1 run-cli search gson" -ForegroundColor Gray
    Write-Host "  .\scripts.ps1 gfd download com.google.gson:gson:2.8.9" -ForegroundColor Gray
    Write-Host "  .\scripts.ps1 run-gui" -ForegroundColor Gray
}

function Install-Dependencies {
    Write-Host "安装项目依赖..." -ForegroundColor Green
    uv venv --python 3.7
    uv sync
}

function Install-DevDependencies {
    Write-Host "安装开发依赖..." -ForegroundColor Green
    uv venv --python 3.7
    uv sync --all-extras
}

function Sync-Dependencies {
    Write-Host "同步依赖..." -ForegroundColor Green
    uv sync
}

function Test-Basic {
    Write-Host "运行基本功能测试..." -ForegroundColor Green
    uv run python test_basic.py
}

function Test-Unit {
    Write-Host "运行单元测试..." -ForegroundColor Green
    uv run pytest
}

function Lint-Code {
    Write-Host "运行代码检查..." -ForegroundColor Green
    Write-Host "flake8..." -ForegroundColor Yellow
    uv run flake8 src/ test_basic.py
    Write-Host "mypy..." -ForegroundColor Yellow
    uv run mypy src/
}

function Format-Code {
    Write-Host "格式化代码..." -ForegroundColor Green
    uv run black src/ test_basic.py
}

function Build-Project {
    Write-Host "构建项目..." -ForegroundColor Green
    uv build
}

function Run-GUI {
    Write-Host "启动 GUI..." -ForegroundColor Green
    uv run gradle-downloader gui
}

function Run-CLI {
    if ($Args.Count -eq 0) {
        Write-Host "启动 CLI 帮助..." -ForegroundColor Green
        uv run gfd --help
    } else {
        Write-Host "启动 CLI: $($Args -join ' ')" -ForegroundColor Green
        $ArgsString = $Args -join ' '
        Invoke-Expression "uv run gfd $ArgsString"
    }
}

function Run-GFD {
    if ($Args.Count -eq 0) {
        Write-Host "GFD 帮助..." -ForegroundColor Green
        uv run gfd --help
    } else {
        Write-Host "运行 GFD: $($Args -join ' ')" -ForegroundColor Green
        $ArgsString = $Args -join ' '
        Invoke-Expression "uv run gfd $ArgsString"
    }
}

function Clean-Build {
    Write-Host "清理构建文件..." -ForegroundColor Green
    
    $foldersToRemove = @("build", "dist", ".pytest_cache", ".mypy_cache")
    foreach ($folder in $foldersToRemove) {
        if (Test-Path $folder) {
            Remove-Item -Recurse -Force $folder
            Write-Host "删除: $folder" -ForegroundColor Yellow
        }
    }
    
    # 删除 .egg-info 文件夹
    Get-ChildItem -Path . -Directory -Name "*.egg-info" | ForEach-Object {
        Remove-Item -Recurse -Force $_
        Write-Host "删除: $_" -ForegroundColor Yellow
    }
    
    # 删除 __pycache__ 文件夹
    Get-ChildItem -Path . -Recurse -Directory -Name "__pycache__" | ForEach-Object {
        Remove-Item -Recurse -Force $_.FullName
        Write-Host "删除: $($_.FullName)" -ForegroundColor Yellow
    }
    
    # 删除 .pyc 文件
    Get-ChildItem -Path . -Recurse -File -Name "*.pyc" | ForEach-Object {
        Remove-Item -Force $_.FullName
        Write-Host "删除: $($_.FullName)" -ForegroundColor Yellow
    }
}

# 主命令分发
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "install" { Install-Dependencies }
    "install-dev" { Install-DevDependencies }
    "sync" { Sync-Dependencies }
    "test" { Test-Unit }
    "test-basic" { Test-Basic }
    "lint" { Lint-Code }
    "format" { Format-Code }
    "build" { Build-Project }
    "run-gui" { Run-GUI }
    "run-cli" { Run-CLI @Args }
    "gfd" { Run-GFD @Args }
    "clean" { Clean-Build }
    default { 
        Write-Host "未知命令: $Command" -ForegroundColor Red
        Write-Host "使用 '.\scripts.ps1 help' 查看可用命令" -ForegroundColor Yellow
    }
} 
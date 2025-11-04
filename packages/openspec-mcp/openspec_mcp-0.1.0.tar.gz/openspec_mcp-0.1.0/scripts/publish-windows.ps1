# OpenSpec MCP - Windows 11 发布脚本
# 使用方法: powershell -ExecutionPolicy Bypass -File scripts/publish-windows.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  OpenSpec MCP - Windows 11 发布工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在正确的目录
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "❌ 错误: 请在项目根目录运行此脚本" -ForegroundColor Red
    Write-Host "   当前目录: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# 1. 检查 Python 和工具
Write-Host "🔍 检查环境..." -ForegroundColor Yellow
Write-Host "   Python 版本: " -NoNewline
python --version

Write-Host "   检查必需工具..." -NoNewline
$tools = @("build", "twine", "pytest")
$missing = @()

foreach ($tool in $tools) {
    $result = pip show $tool 2>$null
    if (-not $result) {
        $missing += $tool
    }
}

if ($missing.Count -gt 0) {
    Write-Host " ❌" -ForegroundColor Red
    Write-Host "   缺少工具: $($missing -join ', ')" -ForegroundColor Red
    $install = Read-Host "   是否安装? (y/n)"
    if ($install -eq "y") {
        Write-Host "   安装工具..." -ForegroundColor Yellow
        pip install --upgrade $missing
    } else {
        exit 1
    }
} else {
    Write-Host " ✓" -ForegroundColor Green
}

Write-Host ""

# 2. 检查 .pypirc 配置
Write-Host "🔍 检查 PyPI 配置..." -ForegroundColor Yellow
$pypirc = "$env:USERPROFILE\.pypirc"
if (-not (Test-Path $pypirc)) {
    Write-Host "   ❌ 未找到 .pypirc 配置文件" -ForegroundColor Red
    Write-Host "   位置: $pypirc" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   请创建配置文件并填入 API Token:" -ForegroundColor Yellow
    Write-Host "   notepad $pypirc" -ForegroundColor Cyan
    exit 1
} else {
    Write-Host "   ✓ 配置文件存在" -ForegroundColor Green
}

Write-Host ""

# 3. 显示当前版本
Write-Host "📋 当前版本信息..." -ForegroundColor Yellow
$content = Get-Content "pyproject.toml" -Raw
if ($content -match 'version\s*=\s*"([^"]+)"') {
    $currentVersion = $matches[1]
    Write-Host "   当前版本: $currentVersion" -ForegroundColor Cyan
} else {
    Write-Host "   ❌ 无法读取版本号" -ForegroundColor Red
    exit 1
}

Write-Host ""
$updateVersion = Read-Host "是否需要更新版本号? (y/n)"
if ($updateVersion -eq "y") {
    $newVersion = Read-Host "请输入新版本号 (例如: 0.1.1)"
    if ($newVersion) {
        Write-Host "   更新版本号到 $newVersion..." -ForegroundColor Yellow
        notepad pyproject.toml
        Write-Host "   请手动修改版本号，保存后按任意键继续..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
}

Write-Host ""

# 4. 运行测试
Write-Host "🧪 运行测试..." -ForegroundColor Yellow
pytest -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ 测试失败" -ForegroundColor Red
    $continue = Read-Host "是否继续? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
} else {
    Write-Host "   ✓ 测试通过" -ForegroundColor Green
}

Write-Host ""

# 5. 代码质量检查（可选）
$checkQuality = Read-Host "是否运行代码质量检查? (y/n)"
if ($checkQuality -eq "y") {
    Write-Host "🔍 检查代码质量..." -ForegroundColor Yellow
    
    Write-Host "   运行 black..." -NoNewline
    black src tests 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓" -ForegroundColor Green
    } else {
        Write-Host " ⚠" -ForegroundColor Yellow
    }
    
    Write-Host "   运行 ruff..." -NoNewline
    ruff check src tests 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✓" -ForegroundColor Green
    } else {
        Write-Host " ⚠" -ForegroundColor Yellow
    }
}

Write-Host ""

# 6. 清理旧构建
Write-Host "🧹 清理旧构建..." -ForegroundColor Yellow
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
Write-Host "   ✓ 清理完成" -ForegroundColor Green

Write-Host ""

# 7. 构建包
Write-Host "📦 构建包..." -ForegroundColor Yellow
python -m build
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ 构建失败" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ 构建成功" -ForegroundColor Green

Write-Host ""

# 8. 检查包
Write-Host "✅ 检查包..." -ForegroundColor Yellow
twine check dist/*
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ 包检查失败" -ForegroundColor Red
    exit 1
}
Write-Host "   ✓ 包检查通过" -ForegroundColor Green

Write-Host ""

# 9. 显示构建的文件
Write-Host "📦 构建的文件:" -ForegroundColor Cyan
Get-ChildItem dist | ForEach-Object {
    Write-Host "   - $($_.Name)" -ForegroundColor White
}

Write-Host ""

# 10. 询问发布到 TestPyPI
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  准备发布" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$uploadTest = Read-Host "📤 是否上传到 TestPyPI (测试环境)? (y/n)"
if ($uploadTest -eq "y") {
    Write-Host "   上传到 TestPyPI..." -ForegroundColor Yellow
    twine upload --repository testpypi dist/*
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ 上传成功" -ForegroundColor Green
        Write-Host ""
        Write-Host "   测试安装命令:" -ForegroundColor Cyan
        Write-Host "   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ openspec-mcp" -ForegroundColor White
        Write-Host ""
        
        $testInstall = Read-Host "是否测试安装? (y/n)"
        if ($testInstall -eq "y") {
            Write-Host "   测试安装..." -ForegroundColor Yellow
            pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ openspec-mcp --upgrade
        }
    } else {
        Write-Host "   ❌ 上传失败" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# 11. 询问发布到正式 PyPI
$uploadProd = Read-Host "📤 是否上传到正式 PyPI? (y/n)"
if ($uploadProd -eq "y") {
    Write-Host ""
    Write-Host "⚠️  警告: 即将发布到正式 PyPI" -ForegroundColor Yellow
    Write-Host "   发布后无法删除或覆盖版本" -ForegroundColor Yellow
    Write-Host ""
    $confirm = Read-Host "确认发布? 输入 'yes' 继续"
    
    if ($confirm -eq "yes") {
        Write-Host "   上传到 PyPI..." -ForegroundColor Yellow
        twine upload dist/*
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "========================================" -ForegroundColor Green
            Write-Host "  ✨ 发布成功!" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "下一步:" -ForegroundColor Cyan
            Write-Host "1. 访问 https://pypi.org/project/openspec-mcp/" -ForegroundColor White
            Write-Host "2. 创建 Git Tag:" -ForegroundColor White
            Write-Host "   git tag -a v$currentVersion -m 'Release version $currentVersion'" -ForegroundColor Gray
            Write-Host "   git push origin v$currentVersion" -ForegroundColor Gray
            Write-Host "3. 在 GitHub 创建 Release" -ForegroundColor White
            Write-Host ""
            Write-Host "安装命令:" -ForegroundColor Cyan
            Write-Host "   pip install openspec-mcp" -ForegroundColor White
            Write-Host "   uvx openspec-mcp" -ForegroundColor White
            Write-Host ""
        } else {
            Write-Host "   ❌ 上传失败" -ForegroundColor Red
            Write-Host ""
            Write-Host "常见问题:" -ForegroundColor Yellow
            Write-Host "- 检查 .pypirc 配置是否正确" -ForegroundColor White
            Write-Host "- 确认 API Token 有效" -ForegroundColor White
            Write-Host "- 确认版本号未被使用" -ForegroundColor White
            exit 1
        }
    } else {
        Write-Host "   已取消发布" -ForegroundColor Yellow
    }
} else {
    Write-Host "   已跳过正式发布" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "完成!" -ForegroundColor Green

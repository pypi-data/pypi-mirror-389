# 发布到 PyPI 指南

本文档详细说明如何将 OpenSpec MCP Server 发布到 PyPI，使其可以通过 `uvx` 或 `pip` 安装。

## 🎯 快速导航

**Windows 11 用户（推荐）：**
- 已有 PyPI 账号和 API Key？→ 跳转到 [Windows 11 快速发布指南](#windows-11-快速发布指南)
- 使用一键脚本？→ 跳转到 [快速发布脚本](#快速发布脚本)
- 查看快速参考？→ 查看 [PUBLISH_QUICK_REFERENCE.md](PUBLISH_QUICK_REFERENCE.md)

**首次发布用户：**
- 从 [前置准备](#前置准备) 开始阅读

**Linux/macOS 用户：**
- 查看 [详细发布流程](#详细发布流程所有平台)

## 前置准备

### 1. 注册 PyPI 账号

1. 访问 [PyPI](https://pypi.org/) 并注册账号
2. 访问 [TestPyPI](https://test.pypi.org/) 并注册账号（用于测试）
3. 验证邮箱

### 2. 创建 API Token

#### PyPI (生产环境)
1. 登录 [PyPI](https://pypi.org/)
2. 进入 Account Settings → API tokens
3. 点击 "Add API token"
4. 名称：`openspec-mcp-upload`
5. 范围：选择 "Entire account" 或特定项目
6. 复制生成的 token（只显示一次！）

#### TestPyPI (测试环境)
1. 登录 [TestPyPI](https://test.pypi.org/)
2. 重复上述步骤创建测试 token

### 3. 配置 PyPI 凭证

#### Windows 11 用户配置步骤

**步骤 1: 找到配置文件位置**

在 Windows 11 中，`.pypirc` 文件应该放在用户主目录：

```
C:\Users\你的用户名\.pypirc
```

**步骤 2: 创建配置文件**

打开 PowerShell 或命令提示符，执行：

```powershell
# 使用 PowerShell 创建配置文件
notepad $env:USERPROFILE\.pypirc
```

或者直接在文件资源管理器中：
1. 按 `Win + R` 打开运行对话框
2. 输入 `%USERPROFILE%` 并回车
3. 在打开的文件夹中创建新文件 `.pypirc`（注意前面有个点）

**步骤 3: 填写配置内容**

在 `.pypirc` 文件中填入以下内容：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-你的PyPI_API_Token

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-你的TestPyPI_API_Token
```

**重要提示**：
- `username` 必须是 `__token__`（不要改）
- `password` 是完整的 API token（包括 `pypi-` 前缀）
- 例如：`pypi-AgEIcHlwaS5vcmcCJGFiY2RlZi0xMjM0LTU2NzgtOTBhYi1jZGVmMTIzNDU2Nzg...`
- 保存文件后关闭

**步骤 4: 验证配置**

在 PowerShell 中验证文件是否创建成功：

```powershell
# 检查文件是否存在
Test-Path $env:USERPROFILE\.pypirc

# 查看文件内容（确认配置正确）
Get-Content $env:USERPROFILE\.pypirc
```

#### Linux/macOS 用户配置

创建或编辑 `~/.pypirc` 文件：

```bash
nano ~/.pypirc
```

填入相同的配置内容，然后设置权限：

```bash
chmod 600 ~/.pypirc
```

### 4. 安装发布工具

```bash
pip install --upgrade build twine
```

## Windows 11 快速发布指南

> 如果你使用 Windows 11，已经有 PyPI 账号和 API Key，按照以下步骤操作：

### 前提条件检查

```powershell
# 1. 检查 Python 版本（需要 3.8+）
python --version

# 2. 检查 pip 版本
pip --version

# 3. 进入项目目录
cd D:\github\specMcp\openspec-mcp
```

### 完整发布步骤

#### 1. 配置 API Token（首次）

```powershell
# 创建配置文件
notepad $env:USERPROFILE\.pypirc
```

填入内容：
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-你的PyPI_API_Token

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-你的TestPyPI_API_Token
```

#### 2. 安装发布工具

```powershell
pip install --upgrade build twine
```

#### 3. 运行测试

```powershell
pytest -v
```

#### 4. 更新版本号

编辑 `pyproject.toml`，修改版本号：
```toml
version = "0.1.0"  # 改为你的新版本号
```

#### 5. 清理旧构建

```powershell
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
```

#### 6. 构建包

```powershell
python -m build
```

成功后会看到：
```
Successfully built openspec_mcp-0.1.0.tar.gz and openspec_mcp-0.1.0-py3-none-any.whl
```

#### 7. 检查包

```powershell
twine check dist/*
```

应该显示：
```
Checking dist/openspec_mcp-0.1.0-py3-none-any.whl: PASSED
Checking dist/openspec_mcp-0.1.0.tar.gz: PASSED
```

#### 8. 测试发布到 TestPyPI（推荐）

```powershell
twine upload --repository testpypi dist/*
```

#### 9. 测试安装

```powershell
# 从 TestPyPI 安装测试
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ openspec-mcp

# 测试运行
python -m openspec_mcp
```

#### 10. 发布到正式 PyPI

```powershell
twine upload dist/*
```

#### 11. 验证发布

```powershell
# 安装正式版本
pip install openspec-mcp

# 或使用 uvx
uvx openspec-mcp
```

#### 12. 创建 Git Tag

```powershell
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

### 常见问题（Windows 11）

**Q: 提示 "twine: command not found"**
```powershell
# 重新安装 twine
pip install --upgrade twine

# 或者使用完整路径
python -m twine upload dist/*
```

**Q: 提示 "Invalid or non-existent authentication information"**
- 检查 `.pypirc` 文件位置是否正确
- 确认 API token 完整复制（包括 `pypi-` 前缀）
- 确认 `username = __token__`（不是你的用户名）

**Q: 构建失败**
```powershell
# 确保安装了 build 工具
pip install --upgrade build

# 清理后重试
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
python -m build
```

**Q: 上传时提示版本已存在**
- PyPI 不允许覆盖已发布的版本
- 必须修改 `pyproject.toml` 中的版本号
- 重新构建和上传

---

## 详细发布流程（所有平台）

### 步骤 1: 更新版本号

编辑 `pyproject.toml`，更新版本号：

```toml
[project]
name = "openspec-mcp"
version = "0.1.0"  # 修改这里
```

版本号规则（遵循 [语义化版本](https://semver.org/lang/zh-CN/)）：
- **主版本号**：不兼容的 API 修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

示例：
- `0.1.0` → `0.1.1`（修复 bug）
- `0.1.0` → `0.2.0`（新增功能）
- `0.1.0` → `1.0.0`（重大更新）

### 步骤 2: 更新 CHANGELOG

创建或更新 `CHANGELOG.md`：

```markdown
# Changelog

## [0.1.1] - 2025-11-04

### Added
- 新增 xxx 功能

### Fixed
- 修复 xxx 问题

### Changed
- 改进 xxx 性能

## [0.1.0] - 2025-11-03

### Added
- 初始版本发布
- 支持 10 个核心 MCP 工具
```

### 步骤 3: 运行测试

确保所有测试通过：

```bash
# 运行测试
pytest -v

# 检查代码质量
black src tests
ruff check src tests

# 类型检查
mypy src
```

### 步骤 4: 清理旧构建

**Windows 11 PowerShell:**
```powershell
# 进入项目目录
cd D:\github\specMcp\openspec-mcp

# 删除旧的构建文件
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
```

**Linux/macOS:**
```bash
rm -rf dist/ build/ *.egg-info
```

### 步骤 5: 构建包

```bash
python -m build
```

这会在 `dist/` 目录生成两个文件：
- `openspec_mcp-0.1.0-py3-none-any.whl`（wheel 格式）
- `openspec_mcp-0.1.0.tar.gz`（源码格式）

### 步骤 6: 检查包

```bash
twine check dist/*
```

应该看到：
```
Checking dist/openspec_mcp-0.1.0-py3-none-any.whl: PASSED
Checking dist/openspec_mcp-0.1.0.tar.gz: PASSED
```

### 步骤 7: 测试发布到 TestPyPI

先发布到测试环境：

```bash
twine upload --repository testpypi dist/*
```

或使用 token 直接上传：

```bash
twine upload --repository testpypi dist/* --username __token__ --password pypi-你的测试token
```

### 步骤 8: 测试安装

从 TestPyPI 安装测试：

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ openspec-mcp
```

测试功能：

```bash
python -m openspec_mcp
```

### 步骤 9: 发布到 PyPI

确认测试无误后，发布到正式环境：

```bash
twine upload dist/*
```

或使用 token：

```bash
twine upload dist/* --username __token__ --password pypi-你的正式token
```

### 步骤 10: 验证发布

1. 访问 [PyPI 项目页面](https://pypi.org/project/openspec-mcp/)
2. 检查版本号、描述、链接等信息
3. 测试安装：

```bash
pip install openspec-mcp
```

或使用 uvx：

```bash
uvx openspec-mcp
```

### 步骤 11: 创建 Git Tag

```bash
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

### 步骤 12: 创建 GitHub Release

1. 访问 GitHub 仓库的 Releases 页面
2. 点击 "Create a new release"
3. 选择刚创建的 tag
4. 填写 Release notes（可以从 CHANGELOG 复制）
5. 发布

## 快速发布脚本

### Windows 11 一键发布脚本

我们提供了一个交互式的 PowerShell 脚本，自动完成所有发布步骤。

**使用方法：**

```powershell
# 进入项目目录
cd D:\github\specMcp\openspec-mcp

# 运行发布脚本
powershell -ExecutionPolicy Bypass -File scripts/publish-windows.ps1
```

**脚本功能：**
- ✅ 自动检查环境和工具
- ✅ 验证 PyPI 配置
- ✅ 运行测试
- ✅ 代码质量检查（可选）
- ✅ 清理旧构建
- ✅ 构建包
- ✅ 检查包格式
- ✅ 交互式发布到 TestPyPI
- ✅ 交互式发布到正式 PyPI
- ✅ 提供下一步操作提示

**脚本截图示例：**

```
========================================
  OpenSpec MCP - Windows 11 发布工具
========================================

🔍 检查环境...
   Python 版本: Python 3.13.2
   检查必需工具... ✓

🔍 检查 PyPI 配置...
   ✓ 配置文件存在

📋 当前版本信息...
   当前版本: 0.1.0

是否需要更新版本号? (y/n): n

🧪 运行测试...
   ✓ 测试通过

🧹 清理旧构建...
   ✓ 清理完成

📦 构建包...
   ✓ 构建成功

✅ 检查包...
   ✓ 包检查通过

📦 构建的文件:
   - openspec_mcp-0.1.0-py3-none-any.whl
   - openspec_mcp-0.1.0.tar.gz

========================================
  准备发布
========================================

📤 是否上传到 TestPyPI (测试环境)? (y/n): y
   上传到 TestPyPI...
   ✓ 上传成功

📤 是否上传到正式 PyPI? (y/n): y

⚠️  警告: 即将发布到正式 PyPI
   发布后无法删除或覆盖版本

确认发布? 输入 'yes' 继续: yes
   上传到 PyPI...

========================================
  ✨ 发布成功!
========================================

下一步:
1. 访问 https://pypi.org/project/openspec-mcp/
2. 创建 Git Tag:
   git tag -a v0.1.0 -m 'Release version 0.1.0'
   git push origin v0.1.0
3. 在 GitHub 创建 Release

安装命令:
   pip install openspec-mcp
   uvx openspec-mcp

完成!
```

### Linux/macOS 发布脚本

创建 `scripts/publish.sh`（Linux/macOS）：

```bash
#!/bin/bash
set -e

echo "🚀 Starting publish process..."

# 1. 运行测试
echo "📝 Running tests..."
pytest -v

# 2. 代码质量检查
echo "🔍 Checking code quality..."
black src tests
ruff check src tests

# 3. 清理旧构建
echo "🧹 Cleaning old builds..."
rm -rf dist/ build/ *.egg-info

# 4. 构建包
echo "📦 Building package..."
python -m build

# 5. 检查包
echo "✅ Checking package..."
twine check dist/*

# 6. 询问是否继续
read -p "📤 Upload to TestPyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    twine upload --repository testpypi dist/*
fi

read -p "📤 Upload to PyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    twine upload dist/*
    echo "✨ Published successfully!"
fi
```

Windows PowerShell 版本 `scripts/publish.ps1`：

```powershell
Write-Host "🚀 Starting publish process..." -ForegroundColor Green

# 1. 运行测试
Write-Host "📝 Running tests..." -ForegroundColor Yellow
pytest -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 2. 代码质量检查
Write-Host "🔍 Checking code quality..." -ForegroundColor Yellow
black src tests
ruff check src tests

# 3. 清理旧构建
Write-Host "🧹 Cleaning old builds..." -ForegroundColor Yellow
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# 4. 构建包
Write-Host "📦 Building package..." -ForegroundColor Yellow
python -m build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 5. 检查包
Write-Host "✅ Checking package..." -ForegroundColor Yellow
twine check dist/*
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 6. 询问是否继续
$testpypi = Read-Host "📤 Upload to TestPyPI? (y/n)"
if ($testpypi -eq "y") {
    twine upload --repository testpypi dist/*
}

$pypi = Read-Host "📤 Upload to PyPI? (y/n)"
if ($pypi -eq "y") {
    twine upload dist/*
    Write-Host "✨ Published successfully!" -ForegroundColor Green
}
```

使用脚本：

```bash
# Linux/macOS
chmod +x scripts/publish.sh
./scripts/publish.sh

# Windows
powershell -ExecutionPolicy Bypass -File scripts/publish.ps1
```

## 常见问题

### 1. 包名已存在

错误：`The name 'openspec-mcp' is already taken`

解决：
- 修改 `pyproject.toml` 中的包名
- 或联系现有包的所有者

### 2. 版本号已存在

错误：`File already exists`

解决：
- PyPI 不允许覆盖已发布的版本
- 必须增加版本号重新发布

### 3. README 渲染错误

错误：`The description failed to render`

解决：
- 检查 README.md 的 Markdown 语法
- 使用 `twine check dist/*` 预检查

### 4. 依赖安装失败

错误：用户安装时依赖无法解析

解决：
- 检查 `pyproject.toml` 中的依赖版本
- 确保依赖在 PyPI 上可用
- 使用宽松的版本约束（如 `>=1.0.0` 而不是 `==1.0.0`）

### 5. Token 权限不足

错误：`403 Forbidden`

解决：
- 确认 token 有上传权限
- 重新生成 token
- 检查 token 的作用域设置

## 自动化发布（GitHub Actions）

创建 `.github/workflows/publish.yml`：

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

配置步骤：
1. 在 GitHub 仓库设置中添加 Secret：`PYPI_API_TOKEN`
2. 创建 GitHub Release 时自动触发发布

## 版本管理最佳实践

### 开发版本

在开发过程中使用开发版本号：

```toml
version = "0.1.0.dev1"  # 开发版本
version = "0.1.0a1"     # Alpha 版本
version = "0.1.0b1"     # Beta 版本
version = "0.1.0rc1"    # Release Candidate
version = "0.1.0"       # 正式版本
```

### 版本号策略

```
主版本.次版本.修订号[-预发布版本][+构建元数据]

示例：
1.0.0          # 正式版本
1.0.1          # 修复版本
1.1.0          # 功能更新
2.0.0          # 重大更新
1.0.0-alpha.1  # Alpha 版本
1.0.0-beta.2   # Beta 版本
1.0.0-rc.1     # Release Candidate
```

## 发布检查清单

发布前确认：

- [ ] 所有测试通过
- [ ] 代码质量检查通过
- [ ] 更新了版本号
- [ ] 更新了 CHANGELOG
- [ ] 更新了 README（如有必要）
- [ ] 清理了旧的构建文件
- [ ] 构建成功
- [ ] 包检查通过
- [ ] 在 TestPyPI 测试成功
- [ ] 创建了 Git tag
- [ ] 准备好 Release notes

## 回滚发布

如果发现严重问题：

1. **不能删除已发布的版本**（PyPI 政策）
2. **立即发布修复版本**：
   ```bash
   # 修复问题
   # 增加版本号（如 0.1.0 → 0.1.1）
   python -m build
   twine upload dist/*
   ```
3. **标记问题版本**：
   - 在 PyPI 项目页面添加说明
   - 在 GitHub Release 中标注

## 维护发布

### 定期更新

- 每月检查依赖更新
- 及时修复安全漏洞
- 响应用户反馈

### 版本支持策略

- 最新版本：完全支持
- 前一个主版本：安全更新
- 更早版本：不再支持

## 参考资源

- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Semantic Versioning](https://semver.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [PEP 440 - Version Identification](https://peps.python.org/pep-0440/)

## 获取帮助

遇到问题？

1. 查看 [PyPI 帮助文档](https://pypi.org/help/)
2. 搜索 [Stack Overflow](https://stackoverflow.com/questions/tagged/pypi)
3. 提交 [GitHub Issue](https://github.com/yourusername/openspec-mcp/issues)

---

**祝发布顺利！** 🎉

# PyPI 发布快速参考 (Windows 11)

## 🚀 一键发布（推荐）

```powershell
cd D:\github\specMcp\openspec-mcp
powershell -ExecutionPolicy Bypass -File scripts/publish-windows.ps1
```

按照提示操作即可！

---

## 📝 手动发布步骤

### 1. 首次配置（只需一次）

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

### 2. 安装工具（只需一次）

```powershell
pip install --upgrade build twine pytest
```

### 3. 发布新版本

```powershell
# 进入项目目录
cd D:\github\specMcp\openspec-mcp

# 1. 更新版本号
notepad pyproject.toml  # 修改 version = "0.1.x"

# 2. 运行测试
pytest -v

# 3. 清理旧构建
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue

# 4. 构建包
python -m build

# 5. 检查包
twine check dist/*

# 6. 上传到 TestPyPI（测试）
twine upload --repository testpypi dist/*

# 7. 测试安装
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ openspec-mcp

# 8. 上传到正式 PyPI
twine upload dist/*

# 9. 创建 Git Tag
git tag -a v0.1.x -m "Release version 0.1.x"
git push origin v0.1.x
```

---

## ❓ 常见问题

### Q: 提示 "Invalid or non-existent authentication information"

**检查清单：**
- [ ] `.pypirc` 文件位置：`C:\Users\你的用户名\.pypirc`
- [ ] `username = __token__`（不是你的用户名）
- [ ] `password` 包含完整 token（包括 `pypi-` 前缀）
- [ ] token 没有过期

**验证配置：**
```powershell
# 检查文件是否存在
Test-Path $env:USERPROFILE\.pypirc

# 查看文件内容
Get-Content $env:USERPROFILE\.pypirc
```

### Q: 提示 "File already exists"

**原因：** PyPI 不允许覆盖已发布的版本

**解决：**
1. 修改 `pyproject.toml` 中的版本号
2. 重新构建和上传

### Q: 提示 "twine: command not found"

```powershell
# 重新安装
pip install --upgrade twine

# 或使用完整路径
python -m twine upload dist/*
```

### Q: 构建失败

```powershell
# 确保安装了 build 工具
pip install --upgrade build

# 清理后重试
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
python -m build
```

---

## 📋 发布检查清单

发布前确认：

- [ ] 所有测试通过 (`pytest -v`)
- [ ] 更新了版本号 (`pyproject.toml`)
- [ ] 更新了 CHANGELOG.md
- [ ] 清理了旧构建
- [ ] 构建成功 (`python -m build`)
- [ ] 包检查通过 (`twine check dist/*`)
- [ ] 在 TestPyPI 测试成功
- [ ] 准备好 Release notes

---

## 🔗 有用的链接

- **PyPI 项目页面**: https://pypi.org/project/openspec-mcp/
- **TestPyPI 项目页面**: https://test.pypi.org/project/openspec-mcp/
- **PyPI 账号设置**: https://pypi.org/manage/account/
- **API Token 管理**: https://pypi.org/manage/account/token/

---

## 📞 获取帮助

- 详细文档：`PUBLISHING.md`
- GitHub Issues：https://github.com/yourusername/openspec-mcp/issues
- PyPI 帮助：https://pypi.org/help/

---

**提示：** 使用一键发布脚本可以避免大部分问题！

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish-windows.ps1
```

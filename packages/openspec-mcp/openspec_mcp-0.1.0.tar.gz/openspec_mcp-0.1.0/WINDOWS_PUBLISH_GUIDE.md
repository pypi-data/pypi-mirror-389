# Windows 11 发布指南

> 专为 Windows 11 用户准备的 PyPI 发布指南

## 📋 前提条件

- ✅ Windows 11 操作系统
- ✅ Python 3.8+ 已安装
- ✅ PyPI 账号已注册
- ✅ PyPI API Token 已获取

## 🚀 方式 1: 一键发布（推荐）

### 使用自动化脚本

```powershell
# 1. 打开 PowerShell
# 2. 进入项目目录
cd D:\github\specMcp\openspec-mcp

# 3. 运行发布脚本
powershell -ExecutionPolicy Bypass -File scripts\publish-windows.ps1
```

### 脚本会自动完成：

1. ✅ 检查 Python 和必需工具
2. ✅ 验证 PyPI 配置文件
3. ✅ 运行测试套件
4. ✅ 清理旧的构建文件
5. ✅ 构建新的发布包
6. ✅ 检查包的格式
7. ✅ 上传到 TestPyPI（可选）
8. ✅ 上传到正式 PyPI
9. ✅ 提供下一步操作指引

### 交互式操作

脚本会在关键步骤询问你：
- 是否更新版本号？
- 是否运行代码质量检查？
- 是否上传到 TestPyPI？
- 是否上传到正式 PyPI？

---

## 📝 方式 2: 手动发布

### 步骤 1: 配置 API Token（首次）

```powershell
# 创建配置文件
notepad $env:USERPROFILE\.pypirc
```

填入以下内容：

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

**重要提示：**
- `username` 必须是 `__token__`
- `password` 是完整的 token（包括 `pypi-` 前缀）
- 保存后关闭记事本

**验证配置：**

```powershell
# 检查文件是否存在
Test-Path $env:USERPROFILE\.pypirc

# 查看文件内容（确认配置正确）
Get-Content $env:USERPROFILE\.pypirc
```

### 步骤 2: 安装发布工具

```powershell
pip install --upgrade build twine pytest
```

### 步骤 3: 更新版本号

```powershell
# 打开配置文件
notepad pyproject.toml
```

找到并修改版本号：

```toml
[project]
name = "openspec-mcp"
version = "0.1.0"  # 修改这里，例如改为 "0.1.1"
```

### 步骤 4: 运行测试

```powershell
pytest -v
```

确保所有测试通过。

### 步骤 5: 清理旧构建

```powershell
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
```

### 步骤 6: 构建包

```powershell
python -m build
```

成功后会看到：

```
Successfully built openspec_mcp-0.1.0.tar.gz and openspec_mcp-0.1.0-py3-none-any.whl
```

### 步骤 7: 检查包

```powershell
twine check dist/*
```

应该显示：

```
Checking dist/openspec_mcp-0.1.0-py3-none-any.whl: PASSED
Checking dist/openspec_mcp-0.1.0.tar.gz: PASSED
```

### 步骤 8: 上传到 TestPyPI（推荐先测试）

```powershell
twine upload --repository testpypi dist/*
```

### 步骤 9: 测试安装

```powershell
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ openspec-mcp
```

测试运行：

```powershell
python -m openspec_mcp
```

### 步骤 10: 上传到正式 PyPI

```powershell
twine upload dist/*
```

### 步骤 11: 验证发布

访问 https://pypi.org/project/openspec-mcp/ 确认发布成功。

测试安装：

```powershell
pip install openspec-mcp
```

或使用 uvx：

```powershell
uvx openspec-mcp
```

### 步骤 12: 创建 Git Tag

```powershell
git tag -a v0.1.0 -m "Release version 0.1.0"
git push origin v0.1.0
```

---

## ❓ 常见问题

### Q1: 提示 "Invalid or non-existent authentication information"

**原因：** API Token 配置不正确

**解决步骤：**

1. 检查配置文件位置：

```powershell
Test-Path $env:USERPROFILE\.pypirc
```

2. 查看配置内容：

```powershell
Get-Content $env:USERPROFILE\.pypirc
```

3. 确认以下内容：
   - `username = __token__`（不是你的用户名）
   - `password` 包含完整 token（包括 `pypi-` 前缀）
   - token 没有过期

4. 如果有问题，重新编辑：

```powershell
notepad $env:USERPROFILE\.pypirc
```

### Q2: 提示 "File already exists"

**原因：** PyPI 不允许覆盖已发布的版本

**解决：**

1. 修改 `pyproject.toml` 中的版本号
2. 清理旧构建：

```powershell
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
```

3. 重新构建和上传：

```powershell
python -m build
twine upload dist/*
```

### Q3: 提示 "twine: command not found"

**原因：** twine 未安装或不在 PATH 中

**解决：**

```powershell
# 重新安装
pip install --upgrade twine

# 或使用完整路径
python -m twine upload dist/*
```

### Q4: 构建失败

**解决：**

```powershell
# 确保安装了 build 工具
pip install --upgrade build

# 清理后重试
Remove-Item -Recurse -Force dist, build, *.egg-info -ErrorAction SilentlyContinue
python -m build
```

### Q5: 测试失败

**解决：**

```powershell
# 查看详细错误
pytest -v

# 如果是依赖问题
pip install -e ".[dev]"

# 重新运行测试
pytest -v
```

### Q6: 上传速度慢

**原因：** 网络问题

**解决：**

- 使用稳定的网络连接
- 如果多次失败，可以重试：

```powershell
twine upload dist/*
```

### Q7: 如何查看已发布的版本？

访问以下链接：

- **正式版本**: https://pypi.org/project/openspec-mcp/
- **测试版本**: https://test.pypi.org/project/openspec-mcp/

或使用命令：

```powershell
pip index versions openspec-mcp
```

---

## 📋 发布检查清单

在发布前，确认以下事项：

- [ ] Python 版本 ≥ 3.8
- [ ] 已安装 build 和 twine
- [ ] 已配置 `.pypirc` 文件
- [ ] API Token 有效
- [ ] 更新了版本号
- [ ] 所有测试通过
- [ ] 清理了旧构建
- [ ] 构建成功
- [ ] 包检查通过
- [ ] 在 TestPyPI 测试成功（推荐）

---

## 🔗 有用的链接

### PyPI 相关
- **PyPI 主页**: https://pypi.org/
- **TestPyPI 主页**: https://test.pypi.org/
- **项目页面**: https://pypi.org/project/openspec-mcp/
- **账号设置**: https://pypi.org/manage/account/
- **API Token 管理**: https://pypi.org/manage/account/token/

### 文档
- **详细发布指南**: [PUBLISHING.md](PUBLISHING.md)
- **快速参考**: [PUBLISH_QUICK_REFERENCE.md](PUBLISH_QUICK_REFERENCE.md)
- **用户手册**: [USER_MANUAL_CN.md](USER_MANUAL_CN.md)

### 工具文档
- **Python Packaging**: https://packaging.python.org/
- **Twine 文档**: https://twine.readthedocs.io/
- **语义化版本**: https://semver.org/lang/zh-CN/

---

## 💡 最佳实践

### 1. 版本号管理

遵循语义化版本规范：

- `0.1.0` → `0.1.1`：修复 bug
- `0.1.0` → `0.2.0`：新增功能
- `0.1.0` → `1.0.0`：重大更新

### 2. 发布流程

推荐流程：

```
1. 开发和测试
   ↓
2. 更新版本号和 CHANGELOG
   ↓
3. 运行完整测试
   ↓
4. 构建包
   ↓
5. 发布到 TestPyPI
   ↓
6. 测试安装
   ↓
7. 发布到正式 PyPI
   ↓
8. 创建 Git Tag
   ↓
9. 创建 GitHub Release
```

### 3. 安全建议

- ✅ 不要将 `.pypirc` 提交到 Git
- ✅ 定期更新 API Token
- ✅ 使用项目级别的 Token（而不是账号级别）
- ✅ 发布后立即验证

### 4. 测试建议

- ✅ 始终先发布到 TestPyPI
- ✅ 在干净的虚拟环境中测试安装
- ✅ 测试所有主要功能
- ✅ 检查依赖是否正确安装

---

## 🎯 下一步

发布成功后：

1. **更新文档**
   - 在 README.md 添加 PyPI 徽章
   - 更新安装说明

2. **创建 Release**
   - 在 GitHub 创建 Release
   - 添加 Release Notes

3. **通知用户**
   - 发布公告
   - 更新文档网站

4. **监控反馈**
   - 关注 GitHub Issues
   - 响应用户问题

---

## 📞 获取帮助

遇到问题？

1. 查看 [常见问题](#常见问题)
2. 阅读 [详细发布指南](PUBLISHING.md)
3. 搜索 [PyPI 帮助文档](https://pypi.org/help/)
4. 提交 [GitHub Issue](https://github.com/yourusername/openspec-mcp/issues)

---

**祝发布顺利！** 🎉

使用一键脚本可以避免大部分问题：

```powershell
powershell -ExecutionPolicy Bypass -File scripts\publish-windows.ps1
```

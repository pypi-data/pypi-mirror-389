# 发布指南

## ✅ 构建完成

项目已成功构建！构建产物位于 `dist/` 目录：

- `volcengine_video_mcp-0.1.0-py3-none-any.whl` (14KB) - Wheel 包
- `volcengine_video_mcp-0.1.0.tar.gz` (85KB) - 源码分发包

## 📦 发布到 PyPI

### 选项 1: 发布到 Test PyPI（推荐先测试）

1. **获取 Test PyPI API Token**:
   - 访问 https://test.pypi.org/manage/account/token/
   - 登录或注册账号
   - 创建新的 API token
   - 复制 token（格式：`pypi-...`）

2. **发布命令**:
```bash
uv publish --publish-url https://test.pypi.org/legacy/ --token pypi-YOUR_TOKEN_HERE
```

3. **验证安装**:
```bash
pip install --index-url https://test.pypi.org/simple/ volcengine-video-mcp
```

### 选项 2: 发布到正式 PyPI

1. **获取 PyPI API Token**:
   - 访问 https://pypi.org/manage/account/token/
   - 登录或注册账号
   - 创建新的 API token
   - 复制 token（格式：`pypi-...`）

2. **发布命令**:
```bash
uv publish --token pypi-YOUR_TOKEN_HERE
```

或使用环境变量：
```bash
export UV_PUBLISH_TOKEN=pypi-YOUR_TOKEN_HERE
uv publish
```

3. **验证安装**:
```bash
pip install volcengine-video-mcp
```

### 选项 3: 使用配置文件（推荐用于持续发布）

创建或编辑 `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PRODUCTION_TOKEN

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_TOKEN
```

然后直接运行：
```bash
# 发布到 Test PyPI
uv publish --index testpypi

# 发布到正式 PyPI
uv publish
```

## 🔄 版本更新流程

1. **更新版本号**:
   编辑 `pyproject.toml` 中的 `version` 字段：
   ```toml
   version = "0.1.1"  # 或 0.2.0, 1.0.0 等
   ```

2. **重新构建**:
   ```bash
   rm -rf dist/
   uv build
   ```

3. **发布新版本**:
   ```bash
   uv publish --token pypi-YOUR_TOKEN_HERE
   ```

## 📋 检查清单

在发布前确保：

- [x] 所有测试通过 (`uv run pytest`)
- [x] 版本号正确更新
- [x] README.md 包含使用说明
- [x] LICENSE 文件存在
- [x] 排除了测试文件和临时文件
- [x] pyproject.toml 元数据完整

## 🌐 包信息

发布后，包将在以下位置可见：

- **PyPI**: https://pypi.org/project/volcengine-video-mcp/
- **Test PyPI**: https://test.pypi.org/project/volcengine-video-mcp/

## 📚 安装使用

用户可以通过以下方式安装：

```bash
# 使用 pip
pip install volcengine-video-mcp

# 使用 uv
uv add volcengine-video-mcp

# 在 MCP 配置中使用
# .mcp.json 或 claude_desktop_config.json
{
  "mcpServers": {
    "volcengine-video": {
      "command": "uvx",
      "args": ["volcengine-video-mcp"],
      "env": {
        "ARK_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## 🔧 故障排除

### 401 Unauthorized
- 检查 API token 是否正确
- 确保 token 以 `pypi-` 开头
- 验证 token 是否过期

### 403 Forbidden
- 包名可能已被占用
- 需要在 PyPI 上注册新的包名
- 或请求现有包的维护权限

### 文件已存在
- 不能重复发布相同版本
- 需要更新版本号后重新构建

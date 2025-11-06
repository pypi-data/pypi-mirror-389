# Release Notes - volcengine-video-mcp v0.1.0

## 🎉 首次发布 (2025-11-06)

`volcengine-video-mcp` 已成功发布到 PyPI！

### 📦 包信息

- **包名称**: volcengine-video-mcp
- **版本**: 0.1.0
- **PyPI 链接**: https://pypi.org/project/volcengine-video-mcp/
- **许可证**: MIT
- **Python 版本**: >=3.11

### ✨ 功能特性

#### MCP 工具 (4个)
1. **create_video_task** - 创建视频生成任务
   - 支持文生视频（Text-to-Video）
   - 支持图生视频（Image-to-Video）
     - 首帧模式
     - 首尾帧模式
     - 参考图模式（1-4张）
   - 完整参数控制（分辨率、宽高比、时长、帧率等）

2. **get_video_task** - 查询任务状态和结果
   - 获取任务状态（queued/running/succeeded/failed/cancelled）
   - 获取生成的视频 URL
   - 获取任务详细信息（种子值、参数等）

3. **list_video_tasks** - 列出任务列表
   - 分页查询
   - 状态过滤
   - 模型过滤
   - 任务 ID 过滤

4. **cancel_video_task** - 取消或删除任务
   - 取消排队中的任务
   - 删除已完成/失败的任务记录

#### MCP 资源 (3个)
1. **status://server** - 服务器状态信息
2. **models://list** - 支持的模型列表
3. **docs://api** - API 使用文档

#### 支持的模型
- doubao-seedance-1-0-pro
- doubao-seedance-1-0-pro-fast
- doubao-seedance-1-0-lite-t2v
- doubao-seedance-1-0-lite-i2v

### 📋 安装方式

```bash
# 使用 pip
pip install volcengine-video-mcp

# 使用 uv
uv add volcengine-video-mcp

# 使用 pipx (推荐用于 MCP)
pipx install volcengine-video-mcp
```

### 🚀 使用方法

#### 在 Claude Desktop 中使用

编辑 `claude_desktop_config.json`:

```json
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

#### 在 Claude Code 中使用

编辑 `.mcp.json`:

```json
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

### 🔧 配置要求

需要火山引擎（豆包）API Key：

1. 访问 https://ark.cn-beijing.volces.com
2. 注册账号并创建 API Key
3. 将 API Key 配置到环境变量或 MCP 配置中

### 📚 示例用法

**文生视频**:
```
请用火山引擎生成一个视频：一只可爱的猫在草地上玩耍，阳光明媚
```

**图生视频**:
```
请用火山引擎根据这张图片生成视频，添加镜头推进效果
```

**查询任务**:
```
查询视频任务 cgt-20251106125638-96mx5 的状态
```

### 🧪 测试覆盖

- ✅ 配置验证测试
- ✅ 资源访问测试
- ✅ 端到端集成测试
- ✅ 实际视频生成测试

### 📊 依赖项

核心依赖：
- fastmcp==2.13.0.1
- httpx==0.28.1
- python-dotenv==1.2.1

### 🐛 已知问题

- 视频 URL 有效期为 24 小时，需及时下载
- 仅支持最近 7 天的任务查询

### 🔜 后续计划

- [ ] 添加批量视频生成支持
- [ ] 添加视频编辑功能
- [ ] 支持更多模型
- [ ] 添加 webhook 回调支持
- [ ] 优化错误处理和重试机制

### 🙏 致谢

感谢火山引擎提供的视频生成 API 和 FastMCP 框架的支持。

### 📝 更新日志

**v0.1.0 (2025-11-06)**
- 首次发布
- 实现基础的视频生成功能
- 支持 4 个核心 API 操作
- 提供完整的 MCP 工具和资源
- 通过端到端测试验证

---

**GitHub**: 待添加
**文档**: 参见 README.md
**问题反馈**: 待添加 issue tracker

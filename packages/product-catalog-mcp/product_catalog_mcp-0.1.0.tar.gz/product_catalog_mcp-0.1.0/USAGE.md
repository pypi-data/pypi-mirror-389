# 快速开始指南

## 项目结构

```
sales-mapping/
├── src/
│   └── product_catalog_mcp/
│       ├── __init__.py
│       └── server.py          # MCP 服务器主代码
├── pyproject.toml              # Python 包配置
├── requirements.txt            # 依赖列表
├── product-catalog.json        # 产品数据文件（需要自行准备）
├── product_catalog_server.py   # 独立运行脚本（向后兼容）
└── README_MCP_SERVER.md        # 详细文档
```

## 本地测试

### 1. 安装到本地环境

```bash
# 在项目根目录下
pip install -e .
```

### 2. 测试运行

```bash
# 设置数据文件路径并运行
PRODUCT_CATALOG_PATH=/Users/chene/repos/sales-mapping/product-catalog.json product-catalog-mcp
```

### 3. 使用 MCP Inspector 测试

```bash
# 安装 MCP Inspector
npm install -g @modelcontextprotocol/inspector

# 测试服务器
PRODUCT_CATALOG_PATH=/Users/chene/repos/sales-mapping/product-catalog.json \
  npx @modelcontextprotocol/inspector product-catalog-mcp
```

## 在 Claude Desktop 中使用

编辑配置文件 `~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "product-catalog": {
      "command": "uvx",
      "args": ["product-catalog-mcp"],
      "env": {
        "PRODUCT_CATALOG_PATH": "/Users/chene/repos/sales-mapping/product-catalog.json"
      }
    }
  }
}
```

保存后重启 Claude Desktop。

## 发布到 PyPI（可选）

如果想让其他人也能使用 `uvx product-catalog-mcp`，需要发布到 PyPI：

### 1. 构建包

```bash
# 安装构建工具
pip install build

# 构建
python -m build
```

### 2. 发布到 PyPI

```bash
# 安装 twine
pip install twine

# 上传到 PyPI
twine upload dist/*
```

### 3. 发布到 TestPyPI（测试用）

```bash
# 上传到 TestPyPI
twine upload --repository testpypi dist/*

# 从 TestPyPI 测试安装
uvx --index-url https://test.pypi.org/simple/ product-catalog-mcp
```

## 常见问题

### Q: 如何验证包是否正确安装？

```bash
# 检查命令是否可用
which product-catalog-mcp

# 查看包信息
pip show product-catalog-mcp
```

### Q: 如何更新包？

```bash
# 如果是本地开发模式（-e），修改代码后无需重新安装
# 如果是正常安装，需要重新安装
pip install -e . --force-reinstall
```

### Q: uvx 和 pip 有什么区别？

- `pip install`: 安装到当前 Python 环境
- `uvx`: 在隔离的临时环境中运行，不污染系统环境，更适合运行 CLI 工具

### Q: 数据文件必须在特定位置吗？

不是。通过环境变量 `PRODUCT_CATALOG_PATH` 可以指定任意位置的数据文件。

## 工具使用示例

一旦在 Claude Desktop 中配置好，可以这样使用：

```
# 列出所有分类
请使用 list_categories 工具列出所有产品分类

# 搜索产品
请搜索关键词"流平剂"相关的产品

# 获取产品详情
请获取产品 ID 为 386 的详细信息
```

# Product Catalog MCP Server

基于 Python fastmcp 实现的产品目录查询 MCP 服务器，使用 stdio 模式通信。

## 功能特性

该 MCP 服务器提供以下 5 个工具接口：

1. **list_categories** - 列出所有分类信息
2. **list_products_by_category** - 根据分类ID列出该分类下的所有产品
3. **get_product_by_id** - 根据产品ID获取产品的完整信息
4. **search_categories** - 使用关键词搜索分类信息
5. **search_products** - 使用关键词搜索产品信息

## 安装方式

### 方式一：使用 uvx（推荐）

最简单的方式是使用 `uvx` 直接运行，无需安装：

```bash
# 直接运行（需要设置环境变量指定数据文件路径）
PRODUCT_CATALOG_PATH=/path/to/product-catalog.json uvx product-catalog-mcp
```

### 方式二：从本地安装

```bash
# 在项目目录下安装
pip install -e .

# 运行
product-catalog-mcp
```

### 方式三：传统方式

```bash
# 安装依赖
pip install -r requirements.txt

# 直接运行脚本
python product_catalog_server.py
```

## 配置环境变量

服务器需要知道产品目录文件的位置。默认会在当前工作目录查找 `product-catalog.json`。

设置环境变量指定文件路径：

```bash
export PRODUCT_CATALOG_PATH=/path/to/your/product-catalog.json
```

## 使用方法

### 使用 uvx 在 Claude Desktop 中配置

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`：

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

### 使用 Python 直接运行

```json
{
  "mcpServers": {
    "product-catalog": {
      "command": "python",
      "args": ["/Users/chene/repos/sales-mapping/product_catalog_server.py"],
      "env": {
        "PRODUCT_CATALOG_PATH": "/Users/chene/repos/sales-mapping/product-catalog.json"
      }
    }
  }
}
```

## 工具接口说明

### 1. list_categories()

列出所有产品分类信息。

**返回值：**
```json
[
  {
    "id": 8,
    "name": "抗涂鸦/防粘贴/反应性助剂",
    "slug": "anti-stick-graffiti",
    "description": "...",
    "order": 20,
    "summary": "...",
    "productCount": 15
  }
]
```

### 2. list_products_by_category(category_id: int)

根据分类ID列出该分类下的所有产品。

**参数：**
- `category_id`: 分类ID（整数）

**返回值：**
```json
[
  {
    "id": 386,
    "name": "BD-2100",
    "description": "有机硅润湿剂、防粘助剂、丙烯酸树脂润湿剂、印刷油墨润湿剂"
  }
]
```

### 3. get_product_by_id(product_id: int)

根据产品ID获取产品的完整信息。

**参数：**
- `product_id`: 产品ID（整数）

**返回值：**
```json
{
  "id": 386,
  "name": "BD-2100",
  "slug": "bd-2100",
  "description": "...",
  "details": "...",
  "summary": "...",
  "categories": ["wetting-agents", "anti-stick-graffiti"],
  "categoryNames": ["抗涂鸦/防粘贴/反应性助剂", "有机硅润湿剂"],
  "category_id": 8,
  "category_name": "抗涂鸦/防粘贴/反应性助剂"
}
```

### 4. search_categories(keyword: str)

使用关键词搜索分类信息。

**参数：**
- `keyword`: 搜索关键词（字符串）

**搜索范围：** name, slug, description, summary

**返回值：** 匹配的分类信息列表（格式同 list_categories）

### 5. search_products(keyword: str)

使用关键词搜索产品信息。

**参数：**
- `keyword`: 搜索关键词（字符串）

**搜索范围：** name, slug, description, details, summary

**返回值：** 匹配的产品信息列表（格式同 get_product_by_id）

## 数据结构

### 产品目录文件格式

```json
{
  "metadata": {
    "generatedAt": "2025-11-03T06:47:49.832Z",
    "version": "1.0.0",
    "totalCategories": 11,
    "totalProducts": 79
  },
  "categories": [
    {
      "id": 8,
      "name": "分类名称",
      "slug": "category-slug",
      "description": "分类描述",
      "order": 20,
      "summary": "分类摘要",
      "productCount": 15,
      "products": [
        {
          "id": 386,
          "name": "产品名称",
          "slug": "product-slug",
          "description": "产品描述",
          "details": "产品详情",
          "summary": "产品摘要",
          "categories": ["category-slug"],
          "categoryNames": ["分类名称"]
        }
      ]
    }
  ]
}
```

## 故障排除

### 文件未找到错误

如果遇到 "产品目录文件未找到" 错误：
1. 检查 `PRODUCT_CATALOG_PATH` 环境变量是否正确设置
2. 确认文件路径存在且可读
3. 确认文件名为 `product-catalog.json`

### JSON 格式错误

如果遇到 "产品目录文件格式错误"：
1. 使用 JSON 验证工具检查文件格式
2. 确认文件编码为 UTF-8

## 开发

### 测试工具

可以使用 MCP Inspector 测试服务器：

```bash
npx @modelcontextprotocol/inspector python product_catalog_server.py
```

### 添加新工具

在 `product_catalog_server.py` 中使用 `@mcp.tool()` 装饰器添加新的工具函数。

## 许可证

本项目基于产品目录数据提供查询服务。

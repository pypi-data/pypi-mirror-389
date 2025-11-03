#!/usr/bin/env python3
"""
Product Catalog MCP Server
使用 fastmcp 实现的产品目录查询服务器
"""

import json
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# 初始化 FastMCP 服务器
mcp = FastMCP("Product Catalog Server")

# 全局变量存储产品目录数据
_catalog_data: Optional[Dict[str, Any]] = None


def load_catalog() -> Dict[str, Any]:
    """加载产品目录数据"""
    global _catalog_data
    
    if _catalog_data is not None:
        return _catalog_data
    
    # 从环境变量获取文件路径，默认为当前目录下的 product-catalog.json
    catalog_path = os.environ.get(
        "PRODUCT_CATALOG_PATH",
        str(Path(__file__).parent / "product-catalog.json")
    )
    
    try:
        with open(catalog_path, "r", encoding="utf-8") as f:
            _catalog_data = json.load(f)
        return _catalog_data
    except FileNotFoundError:
        raise FileNotFoundError(
            f"产品目录文件未找到: {catalog_path}\n"
            f"请设置环境变量 PRODUCT_CATALOG_PATH 指向正确的文件路径"
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"产品目录文件格式错误: {e}")


@mcp.tool()
def list_categories() -> List[Dict[str, Any]]:
    """
    列出所有分类信息
    
    返回分类信息的列表，包含数据文件中的所有分类信息。
    每个分类包含: id, name, slug, description, order, summary, productCount
    """
    catalog = load_catalog()
    categories = catalog.get("categories", [])
    
    # 返回完整的分类信息（不包含 products 字段）
    result = []
    for category in categories:
        cat_info = {
            "id": category.get("id"),
            "name": category.get("name"),
            "slug": category.get("slug"),
            "description": category.get("description"),
            "order": category.get("order"),
            "summary": category.get("summary"),
            "productCount": category.get("productCount")
        }
        result.append(cat_info)
    
    return result


@mcp.tool()
def list_products_by_category(category_id: int) -> List[Dict[str, Any]]:
    """
    根据分类ID列出此分类下的所有产品信息
    
    Args:
        category_id: 分类ID
    
    Returns:
        产品列表，每个产品包含: id, name, description
    """
    catalog = load_catalog()
    categories = catalog.get("categories", [])
    
    # 查找指定的分类
    target_category = None
    for category in categories:
        if category.get("id") == category_id:
            target_category = category
            break
    
    if target_category is None:
        return []
    
    # 提取产品的 id, name, description
    products = target_category.get("products", [])
    result = []
    for product in products:
        product_info = {
            "id": product.get("id"),
            "name": product.get("name"),
            "description": product.get("description")
        }
        result.append(product_info)
    
    return result


@mcp.tool()
def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    """
    根据产品ID获取某产品的具体信息
    
    Args:
        product_id: 产品ID
    
    Returns:
        完整的产品信息，包含所有字段以及所属分类的名称和ID
        如果产品不存在，返回 None
    """
    catalog = load_catalog()
    categories = catalog.get("categories", [])
    
    # 遍历所有分类查找产品
    for category in categories:
        products = category.get("products", [])
        for product in products:
            if product.get("id") == product_id:
                # 返回完整产品信息，并添加所属分类信息
                result = product.copy()
                result["category_id"] = category.get("id")
                result["category_name"] = category.get("name")
                return result
    
    return None


@mcp.tool()
def search_categories(keyword: str) -> List[Dict[str, Any]]:
    """
    使用关键词搜索产品分类信息
    
    Args:
        keyword: 搜索关键词
    
    Returns:
        匹配的分类信息列表（完整字段）
        搜索范围包括: name, slug, description, summary
    """
    catalog = load_catalog()
    categories = catalog.get("categories", [])
    
    keyword_lower = keyword.lower()
    result = []
    
    for category in categories:
        # 在多个字段中搜索关键词
        searchable_fields = [
            str(category.get("name", "")),
            str(category.get("slug", "")),
            str(category.get("description", "")),
            str(category.get("summary", ""))
        ]
        
        # 如果任何字段包含关键词，则添加到结果中
        if any(keyword_lower in field.lower() for field in searchable_fields):
            cat_info = {
                "id": category.get("id"),
                "name": category.get("name"),
                "slug": category.get("slug"),
                "description": category.get("description"),
                "order": category.get("order"),
                "summary": category.get("summary"),
                "productCount": category.get("productCount")
            }
            result.append(cat_info)
    
    return result


@mcp.tool()
def search_products(keyword: str) -> List[Dict[str, Any]]:
    """
    使用关键词搜索产品信息
    
    Args:
        keyword: 搜索关键词
    
    Returns:
        匹配的产品信息列表（完整字段）
        搜索范围包括: name, slug, description, details, summary
        结果包含产品所属的分类信息
    """
    catalog = load_catalog()
    categories = catalog.get("categories", [])
    
    keyword_lower = keyword.lower()
    result = []
    
    for category in categories:
        products = category.get("products", [])
        for product in products:
            # 在多个字段中搜索关键词
            searchable_fields = [
                str(product.get("name", "")),
                str(product.get("slug", "")),
                str(product.get("description", "")),
                str(product.get("details", "")),
                str(product.get("summary", ""))
            ]
            
            # 如果任何字段包含关键词，则添加到结果中
            if any(keyword_lower in field.lower() for field in searchable_fields):
                product_info = product.copy()
                product_info["category_id"] = category.get("id")
                product_info["category_name"] = category.get("name")
                result.append(product_info)
    
    return result


if __name__ == "__main__":
    # 运行服务器 (stdio 模式)
    mcp.run()

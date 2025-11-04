#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @author  : chen-ke-chao
# @date    : 2025-11-04 15:08:18
# @desc    : 


import json
import sys

import httpx
from mcp.server.fastmcp import FastMCP

from wkdaily.log_utils import get_logger

logger = get_logger(__name__)

# 初始化FastMCP服务器
mcp = FastMCP()


@mcp.tool(
    "fetch_by_construction_daily_nos",
    description="用 construction_daily_nos 查询符合条件日报",
)
def fetch_by_construction_daily_nos(construction_daily_nos: list[str]) -> str:
    try:
        url = sys.argv[1]
        logger.info(f"API URL: {url}")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        response = httpx.post(
            url, headers=headers, json=json.dumps(construction_daily_nos), timeout=60
        )
        logger.info(f"响应: {response}")
        response.raise_for_status()
        response_json = response.json()
        # 提取data字段（此时是字符串类型）
        data_str = response_json.get("data")
        return data_str
    except httpx.HTTPError as e:
        logger.error(f"接口调用失败: {e}")
        return ""
    except json.JSONDecodeError:
        logger.error("响应内容不是有效的JSON格式")
        return ""


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

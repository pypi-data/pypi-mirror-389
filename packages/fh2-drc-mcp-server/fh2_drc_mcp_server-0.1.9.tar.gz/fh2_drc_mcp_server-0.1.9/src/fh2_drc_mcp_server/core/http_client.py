# -*- coding: utf-8 -*-
"""
HTTP客户端 - 统一的HTTP请求处理
支持Mock模式，用于开发和测试环境
"""
from typing import Any, Dict, Optional
import httpx
from ..config.settings import BASE_URL, TIMEOUT, MOCK_MODE
from .mock_data import mock_provider


# Mock模式白名单：这些API路径即使在Mock模式下也真实调用
MOCK_WHITELIST = [
    "/element-groups",  # get_pin_points
    "/alert-config",    # get_alert_config, enable_llm_alert, disable_alert
]


def should_skip_mock(path: str) -> bool:
    """判断是否应该跳过Mock，真实调用API"""
    if not MOCK_MODE:
        return True  # 非Mock模式，所有请求都真实调用
    
    # 检查路径是否在白名单中
    for whitelist_path in MOCK_WHITELIST:
        if whitelist_path in path:
            return True
    
    return False


async def get_json(path: str, token: str, use_auth_token: bool = False) -> Dict[str, Any] | str:
    """发送GET请求并返回JSON数据"""
    # 检查是否应该跳过Mock
    if MOCK_MODE and not should_skip_mock(path):
        print(f"🎭 [MOCK GET] {path}")
        return mock_provider.get_mock_response(path, "GET")
    
    # 真实API调用
    token_header = "x-auth-token" if use_auth_token else "x-auth-token"
    headers = {token_header: token}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.get(f"{BASE_URL}{path}", headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"Upstream {e.response.status_code}: {e.response.text}"
        except Exception as e:
            return f"Request error: {e}"


async def post_json(path: str, token: str, body: Dict[str, Any], use_auth_token: bool = False) -> Dict[str, Any] | str:
    """发送POST请求并返回JSON数据"""
    # 检查是否应该跳过Mock
    if MOCK_MODE and not should_skip_mock(path):
        print(f"🎭 [MOCK POST] {path}")
        return mock_provider.get_mock_response(path, "POST", body)
    
    # 真实API调用
    token_header = "x-auth-token" if use_auth_token else "x-auth-token"
    headers = {token_header: token, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.post(f"{BASE_URL}{path}", json=body, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"Upstream {e.response.status_code}: {e.response.text}"
        except Exception as e:
            return f"Request error: {e}"


async def put_json(path: str, token: str, body: Dict[str, Any], use_auth_token: bool = False) -> Dict[str, Any] | str:
    """发送PUT请求并返回JSON数据"""
    # 检查是否应该跳过Mock
    if MOCK_MODE and not should_skip_mock(path):
        print(f"🎭 [MOCK PUT] {path}")
        return mock_provider.get_mock_response(path, "PUT", body)
    
    # 真实API调用
    token_header = "x-auth-token" if use_auth_token else "x-auth-token"
    headers = {token_header: token, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.put(f"{BASE_URL}{path}", json=body, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"Upstream {e.response.status_code}: {e.response.text}"
        except Exception as e:
            return f"Request error: {e}"


async def delete_json(path: str, token: str, body: Optional[Dict[str, Any]] = None, use_auth_token: bool = False) -> Dict[str, Any] | str:
    """发送DELETE请求并返回JSON数据"""
    # 检查是否应该跳过Mock
    if MOCK_MODE and not should_skip_mock(path):
        print(f"🎭 [MOCK DELETE] {path}")
        return mock_provider.get_mock_response(path, "DELETE", body)
    
    # 真实API调用
    token_header = "x-auth-token" if use_auth_token else "x-auth-token"
    headers = {token_header: token, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            if body:
                response = await client.delete(f"{BASE_URL}{path}", json=body, headers=headers)
            else:
                response = await client.delete(f"{BASE_URL}{path}", headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return f"Upstream {e.response.status_code}: {e.response.text}"
        except Exception as e:
            return f"Request error: {e}"


# -*- coding: utf-8 -*-
"""
智能飞行服务 - 自动判断飞行器状态的智能封装函数
"""
import asyncio
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from ..core.http_client import post_json, put_json
from ..config.settings import (
    USER_TOKEN_FIXED, 
    DEFAULT_MAX_SPEED, 
    DEFAULT_RTH_ALTITUDE, 
    DEFAULT_SECURITY_TAKEOFF_HEIGHT,
    TAKEOFF_WAIT_TIME
)
from ..utils.helpers import auto_fill_device_sn, auto_fill_uuid
from .device_service import cloud_controls_create
from .status_service import get_flight_status
from .flight_service import drone_takeoff

# 获取全局MCP实例
mcp: Optional[FastMCP] = None


def set_mcp_instance(mcp_instance: FastMCP) -> None:
    """设置MCP实例"""
    global mcp
    mcp = mcp_instance


## 智能飞向目标点 - 自动判断状态
async def fly_to_point_smart(
    proj_uuid: str,
    target_latitude: float,
    target_longitude: float,
    target_height: float,
    gateway_sn: Optional[str] = None,
    drone_sn: Optional[str] = None,
    max_speed: int = DEFAULT_MAX_SPEED,
    media_folder_name: Optional[str] = None,
    security_takeoff_height: int = DEFAULT_SECURITY_TAKEOFF_HEIGHT,
    rth_altitude: int = DEFAULT_RTH_ALTITUDE,
    out_of_control_action: str = "ReturnHome",
    commander_flight_mode: int = 1,
    commander_flight_height: float = 100.0,
    rth_mode: int = 1,
    token: str = USER_TOKEN_FIXED,
    auto_acquire_control: bool = True,
    wait_for_arrival: bool = False,
    poll_interval: int = 10,
    max_wait_time: int = 300,
) -> Dict[str, Any] | str:
    """
    【智能飞向目标点】自动判断飞行器状态并执行正确操作
    
    🎯 核心功能：无需关心飞行器当前状态，直接说"飞到某个点"即可
    
    ✨ 自动化处理：
       1. 自动查询当前飞行状态
       2. 根据状态自动选择正确的接口：
          • 地面状态 → 自动起飞并飞向目标点
          • 飞行中   → 更新飞行目标点
          • 悬停中   → 创建新的飞行任务
       3. 自动获取飞行控制权
    
    📍 使用场景：
       - "让无人机飞到经纬度(22.793, 114.358)，高度100米"
       - "飞到新的目标点" （无需关心是否已经起飞）
       - AI助手自动控制无人机导航
    
    ⏱️ 执行时间说明：
       - 地面起飞场景：需等待约30秒（设备开机+起飞过程）
       - 空中飞行场景：3-5秒（指令下发时间）
       - 函数会自动处理等待逻辑，确保后续操作安全
    
    🔍 状态判断逻辑：
       情况1 - 地面状态（无飞行任务）
         判断：查询in-flight返回空数据或无flight_task_data
         操作：调用 POST drone-take-off（一键起飞）
         等待：30秒（等待设备开机和起飞）
       
       情况2 - 飞行中（有执行中的fly_to任务）
         判断：fly_to_task存在且status=1（执行中）
         操作：调用 PUT fly-to-points（更新目标点）
         等待：3秒（指令下发确认）
       
       情况3 - 空中悬停（在空中但无fly_to任务）
         判断：flight_task_data存在但fly_to_task为null或已完成
         操作：调用 POST fly-to-points（创建新任务）
         等待：3秒（指令下发确认）
    
    Args:
        proj_uuid: 项目 UUID
        target_latitude: 目标纬度
        target_longitude: 目标经度
        target_height: 目标高度（米）
        gateway_sn: **网关SN/机场SN**；默认取缓存
        drone_sn: **无人机SN**（用于申请控制权）；默认取缓存
        max_speed: 最大飞行速度 (m/s)，默认14
        media_folder_name: 媒体文件夹名称（仅起飞时使用）
        security_takeoff_height: 安全起飞高度（仅起飞时使用）
        rth_altitude: 返航高度（仅起飞时使用）
        out_of_control_action: 失控动作（仅起飞时使用）
        commander_flight_mode: 指点飞行模式（仅起飞时使用）
        commander_flight_height: 指点飞行高度（仅起飞时使用）
        rth_mode: 返航模式（仅起飞时使用）
        token: x-auth-token
        auto_acquire_control: 是否自动获取飞行控制权，默认True
        wait_for_arrival: 是否等待飞行到达目标点，默认False
            - False: 发送指令后立即返回（默认行为）
            - True: 轮询飞行状态直到到达目标点后才返回
        poll_interval: 轮询间隔（秒），默认10秒
        max_wait_time: 最大等待时间（秒），默认300秒（5分钟）
    
    Returns:
        {
            "code": 0,
            "message": "success",
            "data": {
                "action": "takeoff|create_flyto|update_flyto",  # 实际执行的操作
                "flight_id": "...",
                "fly_to_id": "...",
                "status_before": "...",  # 执行前的状态描述
                "arrived": true,  # 如果 wait_for_arrival=True，表示是否已到达
                "flight_time": 45.2  # 如果 wait_for_arrival=True，表示实际飞行耗时（秒）
            }
        }
        或错误信息字符串
    
    使用示例：
        # 简单调用，无需关心飞行器状态
        result = await fly_to_point_smart(
            proj_uuid="xxx",
            target_latitude=22.793,
            target_longitude=114.358,
            target_height=100.0
        )
        
        # 如果是地面状态，会自动起飞（等待30秒）
        # 如果在空中，会直接飞向目标点（3秒）
    """
    print("\n" + "=" * 60)
    print("🤖 智能飞向目标点 - 开始执行")
    print("=" * 60)
    
    # 自动填充设备SN
    filled_gateway_sn = auto_fill_device_sn(gateway_sn, use_gateway=True)
    filled_drone_sn = auto_fill_device_sn(drone_sn, use_gateway=False)
    
    if filled_gateway_sn is None:
        return "❌ gateway_sn is required (no previous recommendation found)"
    
    # 步骤1: 查询当前飞行状态
    print("\n📡 步骤1: 查询当前飞行状态...")
    status_result = await get_flight_status(
        proj_uuid=proj_uuid,
        gateway_sn=filled_gateway_sn,
        token=token,
        raw_data=True  # 获取原始数据用于判断
    )
    
    # 解析状态数据
    flight_data = None
    if isinstance(status_result, dict) and status_result.get("code") == 0:
        flight_data = status_result.get("data")
    
    # 步骤2: 根据状态判断并执行相应操作
    action = None
    status_description = None
    result = None
    
    # 情况1: 无飞行任务（地面状态）
    if flight_data is None or not flight_data:
        status_description = "地面状态（无飞行任务）"
        action = "takeoff"
        print(f"📊 当前状态: {status_description}")
        print("🛫 操作: 执行一键起飞...")
        print(f"⏱️  预计耗时: 约{TAKEOFF_WAIT_TIME}秒（设备开机+起飞）")
        
        # 生成媒体文件夹名称
        if media_folder_name is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            media_folder_name = f"{timestamp}_{filled_gateway_sn[-6:]}_MCP"
        
        # 调用一键起飞
        result = await drone_takeoff(
            proj_uuid=proj_uuid,
            media_folder_name=media_folder_name,
            target_height=target_height,
            gateway_sn=filled_gateway_sn,
            drone_sn=filled_drone_sn,
            target_latitude=target_latitude,
            target_longitude=target_longitude,
            security_takeoff_height=security_takeoff_height,
            max_speed=max_speed,
            out_of_control_action=out_of_control_action,
            rth_altitude=rth_altitude,
            commander_flight_mode=commander_flight_mode,
            commander_flight_height=commander_flight_height,
            rth_mode=rth_mode,
            token=token,
            auto_acquire_control=auto_acquire_control,
        )
    
    else:
        # 有飞行任务数据
        flight_task_data = flight_data.get("flight_task_data", {})
        fly_to_task = flight_data.get("fly_to_task")
        flight_id = flight_data.get("flight_id", "")
        task_status = flight_task_data.get("status", -1)
        
        # 情况2: 有执行中的fly_to任务
        if fly_to_task is not None and fly_to_task.get("status") == 1:
            status_description = "飞行中（有执行中的fly_to任务）"
            action = "update_flyto"
            fly_to_id = fly_to_task.get("uuid", "")
            
            print(f"📊 当前状态: {status_description}")
            print(f"🆔 Flight ID: {flight_id}")
            print(f"🆔 FlyTo ID: {fly_to_id}")
            print("✈️  操作: 更新飞行目标点...")
            print("⏱️  预计耗时: 约3秒（指令下发）")
            
            # 步骤2.1: 自动获取飞行控制权
            if auto_acquire_control:
                print("\n🔓 获取飞行控制权...")
                control_result = await cloud_controls_create(
                    proj_uuid=proj_uuid,
                    control_keys=["flight"],
                    drone_sn=filled_drone_sn,
                    token=token
                )
                if isinstance(control_result, str) or (isinstance(control_result, dict) and control_result.get("code") != 0):
                    return f"❌ 获取飞行控制权失败: {control_result}"
                print("✅ 飞行控制权获取成功")
            
            # 调用更新fly_to接口
            body = {
                "fly_to_id": fly_to_id,
                "max_speed": max_speed,
                "start_point": {
                    "latitude": target_latitude,
                    "longitude": target_longitude,
                    "height": target_height,
                },
                "points": [
                    {
                        "latitude": target_latitude,
                        "longitude": target_longitude,
                        "height": target_height,
                    }
                ],
            }
            
            result = await put_json(
                f"/task/api/v1/workspaces/{proj_uuid}/flight-tasks/fly-to-points",
                token,
                body,
            )
            
            # 等待指令下发确认
            if isinstance(result, dict) and result.get("code") == 0:
                print("✅ 目标点更新指令已发送，等待确认（3秒）...")
                await asyncio.sleep(3)
                print("✅ 指令确认完成")
        
        # 情况3: 在空中但无fly_to任务（悬停状态）
        elif task_status == 1:  # status=1表示飞行任务执行中
            status_description = "空中悬停（无fly_to任务）"
            action = "create_flyto"
            
            print(f"📊 当前状态: {status_description}")
            print(f"🆔 Flight ID: {flight_id}")
            print("🚁 操作: 创建新的飞行任务...")
            print("⏱️  预计耗时: 约3秒（指令下发）")
            
            # 步骤3.1: 自动获取飞行控制权
            if auto_acquire_control:
                print("\n🔓 获取飞行控制权...")
                control_result = await cloud_controls_create(
                    proj_uuid=proj_uuid,
                    control_keys=["flight"],
                    drone_sn=filled_drone_sn,
                    token=token
                )
                if isinstance(control_result, str) or (isinstance(control_result, dict) and control_result.get("code") != 0):
                    return f"❌ 获取飞行控制权失败: {control_result}"
                print("✅ 飞行控制权获取成功")
            
            # 调用创建fly_to接口
            body = {
                "device_sn": filled_gateway_sn,
                "max_speed": max_speed,
                "start_point": {
                    "latitude": target_latitude,
                    "longitude": target_longitude,
                    "height": target_height,
                },
                "points": [
                    {
                        "latitude": target_latitude,
                        "longitude": target_longitude,
                        "height": target_height,
                    }
                ],
            }
            
            result = await post_json(
                f"/task/api/v1/workspaces/{proj_uuid}/flight-tasks/fly-to-points",
                token,
                body,
            )
            
            # 等待指令下发确认
            if isinstance(result, dict) and result.get("code") == 0:
                print("✅ 飞行任务已创建，等待确认（3秒）...")
                await asyncio.sleep(3)
                print("✅ 指令确认完成")
        
        else:
            # 其他状态（任务已完成、失败等）
            return f"❌ 飞行器状态异常，无法执行飞行操作\n当前任务状态: {task_status}\n💡 建议: 检查飞行器状态或重新发起任务"
    
    # 步骤3: 返回结果
    print("\n" + "=" * 60)
    if isinstance(result, dict) and result.get("code") == 0:
        print("✅ 智能飞向目标点 - 执行成功")
        print("=" * 60)
        
        # 构造统一的返回格式
        original_data = result.get("data", {})
        enhanced_data = {
            "action": action,
            "status_before": status_description,
            "flight_id": original_data.get("flight_id", original_data.get("fly_to_id", "")),
            "fly_to_id": original_data.get("fly_to_id", ""),
            "target": {
                "latitude": target_latitude,
                "longitude": target_longitude,
                "height": target_height,
            }
        }
        
        # ✨ 步骤4: 如果需要等待到达，轮询飞行状态
        if wait_for_arrival:
            print("\n" + "=" * 60)
            print("⏳ 等待飞行到达目标点...")
            print("=" * 60)
            
            arrived, flight_time = await _wait_for_arrival(
                proj_uuid=proj_uuid,
                gateway_sn=filled_gateway_sn,
                token=token,
                poll_interval=poll_interval,
                max_wait_time=max_wait_time
            )
            
            # 将等待结果添加到返回数据中
            enhanced_data["arrived"] = arrived
            enhanced_data["flight_time"] = flight_time
            
            if not arrived:
                print("⚠️  等待超时，但指令已发送")
                print("=" * 60)
        
        return {
            "code": 0,
            "message": "success",
            "data": enhanced_data
        }
    else:
        print("❌ 智能飞向目标点 - 执行失败")
        print("=" * 60)
        return result


# ============================================================================
# 内部辅助函数 - 等待飞行到达
# ============================================================================

async def _wait_for_arrival(
    proj_uuid: str,
    gateway_sn: str,
    token: str,
    poll_interval: int,
    max_wait_time: int
) -> tuple[bool, float]:
    """
    轮询等待飞行到达目标点
    
    Args:
        proj_uuid: 项目 UUID
        gateway_sn: 网关 SN
        token: 认证 Token
        poll_interval: 轮询间隔（秒）
        max_wait_time: 最大等待时间（秒）
    
    Returns:
        (arrived, flight_time): 
            - arrived: 是否已到达
            - flight_time: 实际飞行耗时（秒）
    """
    import time
    
    print(f"⏳ 开始等待飞行到达（最长{max_wait_time}秒，每{poll_interval}秒查询一次）...")
    start_time = time.time()
    null_count = 0  # fly_to_task=null 的连续次数
    attempt = 0
    max_attempts = max_wait_time // poll_interval
    
    while time.time() - start_time < max_wait_time:
        attempt += 1
        await asyncio.sleep(poll_interval)
        
        print(f"\n📡 第 {attempt}/{max_attempts} 次查询飞行状态...")
        
        # 查询飞行状态
        status = await get_flight_status(
            proj_uuid=proj_uuid,
            gateway_sn=gateway_sn,
            token=token,
            raw_data=True
        )
        
        # 判断是否到达
        arrived, null_count = _check_arrival(status, null_count)
        
        if arrived:
            elapsed = time.time() - start_time
            print(f"✅ 已到达目标点（耗时 {elapsed:.1f} 秒）")
            return True, elapsed
        
        # 输出当前状态信息
        _print_flight_progress(status, attempt, max_attempts)
    
    # 超时
    elapsed = time.time() - start_time
    print(f"⚠️  等待超时（{elapsed:.1f} 秒），可能还在飞行中")
    return False, elapsed


def _check_arrival(status_data: dict, null_count: int) -> tuple[bool, int]:
    """
    判断是否到达目标点
    （移植 Go 代码中的 waitForFlightArrival 逻辑）
    
    判断逻辑（对于手动飞行 flight_type=2）：
    1. flight_task_data.status=1 (EXECUTING) + fly_to_task=null → 已到达（空中悬停）
    2. fly_to_task.status=2 (FINISH) + remaining_distance < 5m → 即将到达
    3. flight_task_data.status=2 (FINISH) → 任务完成
    
    Args:
        status_data: 飞行状态数据（get_flight_status的返回值）
        null_count: 当前的 null 计数器
    
    Returns:
        (arrived, new_null_count): 
            - arrived: 是否已到达
            - new_null_count: 更新后的 null 计数器
    """
    if not isinstance(status_data, dict) or status_data.get("code") != 0:
        return False, 0
    
    data = status_data.get("data", {})
    if not data:
        return False, 0
    
    flight_task = data.get("flight_task_data", {})
    fly_to_task = data.get("fly_to_task")
    flight_type = data.get("flight_type", 0)
    
    task_status = flight_task.get("status", -1)
    
    # 情况1: status=1 + fly_to_task=null → 已到达（连续3次确认）
    if (flight_type == 2 and 
        task_status == 1 and 
        fly_to_task is None):
        
        null_count += 1
        print(f"   检测到 fly_to_task=null（确认 {null_count}/3）")
        
        if null_count >= 3:
            print("   ✅ 连续3次确认，已到达目标点（空中悬停）")
            return True, null_count
        else:
            return False, null_count
    
    # 如果 fly_to_task 存在，重置 null 计数器
    if fly_to_task is not None and null_count > 0:
        print(f"   重置 null 计数器（之前: {null_count}）")
        null_count = 0
    
    # 情况2: fly_to_task.status=2 + distance<5m
    if fly_to_task is not None:
        flyto_status = fly_to_task.get("status", -1)
        remaining_distance = fly_to_task.get("remaining_distance", 999)
        
        if flyto_status == 2 and remaining_distance < 5.0:
            print(f"   ✅ FlyTo任务完成且距离<5米 (distance={remaining_distance:.1f}m)")
            return True, 0
        elif flyto_status == 2:
            print(f"   FlyTo任务完成但距离>5米 (distance={remaining_distance:.1f}m)，继续等待...")
        elif flyto_status == 1:
            print(f"   飞行中：剩余距离 {remaining_distance:.1f}m")
    
    # 情况3: flight_task_data.status=2 (FINISH)
    if task_status == 2:
        print("   ✅ 飞行任务完成（status=2）")
        return True, 0
    
    return False, null_count


def _print_flight_progress(status_data: dict, attempt: int, max_attempts: int):
    """打印飞行进度信息"""
    if not isinstance(status_data, dict) or status_data.get("code") != 0:
        return
    
    data = status_data.get("data", {})
    if not data:
        return
    
    flight_task = data.get("flight_task_data", {})
    fly_to_task = data.get("fly_to_task")
    
    task_status = flight_task.get("status", -1)
    
    progress_parts = [f"第 {attempt}/{max_attempts} 次"]
    progress_parts.append(f"主任务状态: {task_status}")
    
    if fly_to_task:
        flyto_status = fly_to_task.get("status", -1)
        remaining_distance = fly_to_task.get("remaining_distance", 0)
        remaining_time = fly_to_task.get("remaining_time", 0)
        
        progress_parts.append(f"FlyTo状态: {flyto_status}")
        if remaining_distance > 0:
            progress_parts.append(f"剩余: {remaining_distance:.1f}m")
        if remaining_time > 0:
            progress_parts.append(f"预计: {remaining_time:.0f}s")
    else:
        progress_parts.append("FlyTo: null")
    
    print(f"   📊 {' | '.join(progress_parts)}")



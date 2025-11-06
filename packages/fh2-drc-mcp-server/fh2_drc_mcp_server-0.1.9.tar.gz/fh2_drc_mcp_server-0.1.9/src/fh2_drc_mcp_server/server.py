# -*- coding: utf-8 -*-
"""
DRC MCP服务 - 重构后的主入口文件
pip install "mcp-server>=0.9.0" "httpx>=0.27"
python main_refactored.py
"""
from mcp.server.fastmcp import FastMCP

# 导入所有服务函数（不使用装饰器版本）
from .services.device_service import (
    # device_recommendation,
    cloud_controls_create)
from .services.flight_service import drone_takeoff, fly_to_points, drone_return_home
from .services.smart_flight_service import fly_to_point_smart
from .services.camera_service import (
    camera_photo_take,
    camera_aim,
    camera_look_at,
    gimbal_reset_horizontal,
    gimbal_reset_downward,
    camera_tilt_down,
    camera_mode_switch,
    camera_lens_switch
    # camera_recording_start,  # 基础函数，不暴露给用户，由camera_recording_task调用
    # camera_recording_stop,   # 基础函数，不暴露给用户，由camera_recording_task调用
)
from .services.poi_service import poi_enter, poi_exit
from .services.status_service import get_flight_status
from .services.panoramic_service import panoramic_shooting
from .services.recording_service import camera_recording_task
from .services.map_service import get_pin_points, create_pin_point, get_default_group_id
from .services.ai_alert_service import (
    get_alert_config,
    # update_alert_config,
    enable_llm_alert,
    disable_alert
)

# 创建MCP服务实例
mcp = FastMCP("drc_mcp_service")

# 注册所有工具
# mcp.tool()(device_recommendation)

# ===== 智能飞行接口（推荐使用） =====
# 这些是对AI友好的智能接口，会自动判断飞行器状态
mcp.tool()(fly_to_point_smart)  # 智能飞向目标点（自动判断是起飞/创建/更新）
mcp.tool()(get_flight_status)   # 查询飞行状态

# ===== 底层飞行接口（高级用户使用） =====
# 注意：建议优先使用上面的智能接口，除非明确知道飞行器状态
# mcp.tool()(drone_takeoff)       # 底层：一键起飞（仅地面状态）
# mcp.tool()(fly_to_points)       # 底层：飞向目标点（仅空中悬停状态）
mcp.tool()(cloud_controls_create) # 控制权管理（智能接口会自动调用）
mcp.tool()(drone_return_home)     # 返航（所有状态可用）
# 以下函数作为内部函数，不直接暴露给用户
# mcp.tool()(camera_recording_start)  # 使用 camera_recording_task 代替
# mcp.tool()(camera_recording_stop)   # 使用 camera_recording_task 代替

# ===== 相机与负载控制 =====
mcp.tool()(camera_photo_take)
mcp.tool()(camera_aim)
mcp.tool()(camera_look_at)
mcp.tool()(gimbal_reset_horizontal)
mcp.tool()(gimbal_reset_downward)
mcp.tool()(camera_tilt_down)
mcp.tool()(camera_mode_switch)
mcp.tool()(camera_lens_switch)
mcp.tool()(camera_recording_task)

# ===== POI与任务 =====
mcp.tool()(poi_enter)
mcp.tool()(poi_exit)
mcp.tool()(panoramic_shooting)

# ===== 地图与标注 =====
mcp.tool()(get_pin_points)
mcp.tool()(create_pin_point)
mcp.tool()(get_default_group_id)

# ===== AI告警 =====
mcp.tool()(get_alert_config)
# mcp.tool()(update_alert_config)
mcp.tool()(enable_llm_alert)
mcp.tool()(disable_alert)


def run():
    mcp.run()


if __name__ == '__main__':
    run()

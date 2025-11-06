# -*- coding: utf-8 -*-
"""
Mock数据模块 - 为每个工具函数提供准确的返回体结构
用于开发和测试环境，避免真实调用无人机接口
"""
from typing import Any, Dict, Optional
import time
import uuid


def generate_uuid() -> str:
    """生成随机UUID"""
    return str(uuid.uuid4())


class MockFlightState:
    """飞行状态管理"""
    def __init__(self):
        self.flight_id = generate_uuid()
        self.has_flight = False
        
    def start_flight(self):
        self.flight_id = generate_uuid()
        self.has_flight = True
    
    def get_status(self) -> Dict[str, Any]:
        if not self.has_flight:
            return {}
        return {
            "flight_id": self.flight_id,
            "flight_task_data": {
                "uuid": self.flight_id,
                "status": 1,
                "name": "Mock Flight",
                "created_time": int(time.time() * 1000),
                "updated_time": int(time.time() * 1000)
            },
            "flight_type": 2,
            "fly_to_task": None,  # 已到达
            "return_home_info": None,
            "is_first_fly_to": False
        }


flight_state = MockFlightState()


class MockDataProvider:
    """Mock数据提供器 - 每个工具函数有准确的返回体"""
    
    @staticmethod
    def get_mock_response(path: str, method: str, body: Dict[str, Any] = None) -> Dict[str, Any]:
        """根据API路径返回准确的Mock数据"""
        
        # ==================== 1. fly_to_point_smart ====================
        # 调用多个底层接口，返回统一格式
        if "/device-recommendation" in path:
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "devices": [{
                        "gateway_sn": "8UUDMAQ00A0197",
                        "drone_sn": "1581F8HGD24BN0010223",
                        "workspace_id": "a2e4f0d4-1a8d-47e3-a4b0-fdfb904f798b"
                    }]
                }
            }
        
        if "/drone-take-off" in path:
            flight_state.start_flight()
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "flight_id": flight_state.flight_id,
                    "fly_to_id": generate_uuid()
                }
            }
        
        if "/fly-to-points" in path and method == "POST":
            flight_state.start_flight()
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "fly_to_id": generate_uuid(),
                    "flight_id": flight_state.flight_id
                }
            }
        
        if "/fly-to-points" in path and method == "PUT":
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "fly_to_id": generate_uuid()
                }
            }
        
        # ==================== 2. get_flight_status ====================
        if "/in-flight" in path:
            return {
                "code": 0,
                "message": "success",
                "data": flight_state.get_status()
            }
        
        # ==================== 3. cloud_controls_create ====================
        if "/cloud_controls" in path or "/cloud-controls" in path:
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "control_keys": body.get("control_keys", ["flight", "payload_99-0-0"]) if body else ["flight"]
                }
            }
        
        # ==================== 4. drone_return_home ====================
        if "/return-home" in path or "/return_home" in path:
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "status": "returning_home"
                }
            }
        
        # ==================== 5-11. 相机控制 (camera_photo_take等) ====================
        if "/payload-commands" in path:
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "biz_code": generate_uuid()
                }
            }
        
        # ==================== 12. camera_lens_switch ====================
        if "/change-lens" in path or "/switch-select-video" in path:
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "status": "switched"
                }
            }
        
        # ==================== 13. camera_recording_task ====================
        # 这个函数返回字符串，不是JSON，由函数自己处理
        
        # ==================== 14. poi_enter ====================
        if "/poi-enter" in path:
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "poi_task_id": generate_uuid()
                }
            }
        
        # ==================== 15. poi_exit ====================
        if "/poi-exit" in path:
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "status": "exited"
                }
            }
        
        # ==================== 16. panoramic_shooting ====================
        # 这个函数返回字符串，不是JSON，由函数自己处理
        
        # ==================== 17. get_pin_points ====================
        if "/element-groups" in path and method == "GET":
            return {
                "code": 0,
                "message": "success",
                "data": [{
                    "id": "6e4eeb06-27b9-4438-ab23-1abaa7c80a14",
                    "name": "default",
                    "workspace_id": "a2e4f0d4-1a8d-47e3-a4b0-fdfb904f798b",
                    "elements": [{
                        "uuid": generate_uuid(),
                        "name": "Mock目标点",
                        "group_id": "6e4eeb06-27b9-4438-ab23-1abaa7c80a14",
                        "resource": {
                            "type": 0,
                            "content": {
                                "type": "Feature",
                                "geometry": {
                                    "type": "Point",
                                    "coordinates": [114.356593, 22.793825, 100.0]
                                }
                            }
                        }
                    }]
                }]
            }
        
        # ==================== 18. create_pin_point ====================
        if "/elements" in path and method == "POST":
            return {
                "code": 0,
                "message": "success",
                "data": {
                    "uuid": generate_uuid()
                }
            }
        
        # ==================== 19. get_default_group_id ====================
        # 这个函数调用get_pin_points然后返回字符串，由函数自己处理
        
        # ==================== 20. get_alert_config ====================
        if "/alert-config" in path and method == "GET":
            return {
                "code": 0,
                "message": "OK",
                "data": {
                    "uuid": generate_uuid(),
                    "project_id": "mock-project",
                    "drone_sn": "1581F8HGD24BN0010223",
                    "payload_index": "99-0-0",
                    "status": {
                        "aircraft_status": 0,
                        "llm_status": 0,
                        "third_aircraft_status": 0,
                        "third_llm_status": 0
                    },
                    "prompt_uuid": "49e47eaa-339b-4e9d-898f-0008a584c804",
                    "labels": {
                        "aircraft_labels": [],
                        "llm_labels": [],
                        "third_aircraft_labels": [],
                        "third_llm_labels": []
                    },
                    "thresholds": {
                        "use_min_threshold": False,
                        "use_max_threshold": False,
                        "min_threshold": 0,
                        "max_threshold": 0
                    },
                    "interval_seconds": {
                        "aircraft_interval": 0,
                        "llm_interval": 5,
                        "third_aircraft_interval": 0,
                        "third_llm_interval": 0
                    }
                }
            }
        
        # ==================== 21. enable_llm_alert ====================
        # ==================== 22. disable_alert ====================
        if "/alert-config" in path and method == "PUT":
            return {
                "code": 0,
                "message": "OK",
                "data": None
            }
        
        # 默认成功响应
        return {
            "code": 0,
            "message": "success",
            "data": None
        }


# 导出单例
mock_provider = MockDataProvider()

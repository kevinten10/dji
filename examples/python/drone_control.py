#!/usr/bin/env python3
"""
DJI 无人机控制示例

此脚本演示如何使用DJI SDK控制无人机的基础操作。
注意：此为示例代码，实际使用需要DJI SDK和相关硬件。

支持的SDK:
- DJI Mobile SDK (iOS/Android)
- DJI Onboard SDK (ROS)
- DJI Payload SDK
"""

import time
import math
from typing import Optional, Tuple


class DroneController:
    """无人机控制器基类"""
    
    def __init__(self):
        self.is_connected = False
        self.battery_level = 100
        self.gps_signal = 0
        self.altitude = 0
        self.position = (0, 0, 0)  # x, y, z
    
    def connect(self) -> bool:
        """连接无人机"""
        print("[*] 正在连接无人机...")
        # 模拟连接过程
        time.sleep(1)
        self.is_connected = True
        print("[+] 无人机已连接")
        return True
    
    def disconnect(self):
        """断开连接"""
        if self.is_connected:
            print("[*] 正在断开连接...")
            self.is_connected = False
            print("[+] 已断开连接")
    
    def get_status(self) -> dict:
        """获取无人机状态"""
        return {
            "connected": self.is_connected,
            "battery": self.battery_level,
            "gps": self.gps_signal,
            "altitude": self.altitude,
            "position": self.position
        }
    
    def takeoff(self) -> bool:
        """起飞"""
        if not self.is_connected:
            print("[!] 无人机未连接")
            return False
        print("[*] 执行起飞...")
        print("[*] 等待电机启动...")
        time.sleep(1)
        print("[*] 上升中...")
        self.altitude = 10
        print(f"[+] 到达目标高度: {self.altitude}m")
        return True
    
    def land(self) -> bool:
        """降落"""
        if not self.is_connected:
            print("[!] 无人机未连接")
            return False
        print("[*] 执行降落...")
        while self.altitude > 0:
            self.altitude = max(0, self.altitude - 1)
            print(f"[*] 当前高度: {self.altitude}m")
            time.sleep(0.5)
        print("[+] 降落完成")
        return True
    
    def go_to(self, x: float, y: float, z: float, speed: float = 5.0) -> bool:
        """移动到指定位置"""
        if not self.is_connected:
            print("[!] 无人机未连接")
            return False
        print(f"[*] 飞向目标位置: ({x}, {y}, {z})")
        self.position = (x, y, z)
        self.altitude = z
        print("[+] 到达目标位置")
        return True
    
    def rotate(self, yaw: float) -> bool:
        """旋转（偏航）"""
        if not self.is_connected:
            print("[!] 无人机未连接")
            return False
        print(f"[*] 旋转偏航角: {yaw}°")
        print("[+] 旋转完成")
        return True
    
    def move(self, direction: str, distance: float = 10) -> bool:
        """
        沿指定方向移动
        
        Args:
            direction: 方向 ('forward', 'backward', 'left', 'right', 'up', 'down')
            distance: 距离（米）
        """
        if not self.is_connected:
            print("[!] 无人机未连接")
            return False
        
        movements = {
            'forward': ("前方", 0, 0, 1),
            'backward': ("后方", 0, 0, -1),
            'left': ("左侧", -1, 0, 0),
            'right': ("右侧", 1, 0, 0),
            'up': ("上方", 0, 1, 0),
            'down': ("下方", 0, -1, 0)
        }
        
        if direction not in movements:
            print(f"[!] 无效方向: {direction}")
            return False
        
        name, dx, dy, dz = movements[direction]
        print(f"[*] 向{name}移动 {distance}m")
        
        x, y, z = self.position
        self.position = (x + dx * distance, y + dy * distance, z + dz * distance)
        self.altitude = self.position[2]
        
        print(f"[+] 当前位置: {self.position}")
        return True


class MockDroneController(DroneController):
    """模拟无人机控制器（用于测试）"""
    
    def __init__(self):
        super().__init__()
        self._mock_battery = 85
        self._mock_gps = 50
    
    def connect(self) -> bool:
        print("[Mock] 模拟连接中...")
        self.is_connected = True
        self._mock_battery = 85
        return True


def demo_basic_control():
    """演示基本控制"""
    print("=" * 50)
    print("DJI 无人机控制演示")
    print("=" * 50)
    
    # 创建控制器（使用模拟版本）
    drone = MockDroneController()
    
    # 连接
    drone.connect()
    print(f"状态: {drone.get_status()}")
    print()
    
    # 起飞
    drone.takeoff()
    print()
    
    # 执行一系列动作
    print("执行航线...")
    drone.move('forward', 20)
    drone.rotate(90)
    drone.move('right', 15)
    drone.move('forward', 10)
    print()
    
    # 返航
    print("执行返航...")
    drone.go_to(0, 0, 10)
    print()
    
    # 降落
    drone.land()
    print()
    
    # 断开连接
    drone.disconnect()
    
    print("=" * 50)
    print("演示完成！")
    print("=" * 50)


def calculate_distance(pos1: Tuple[float, float, float], 
                       pos2: Tuple[float, float, float]) -> float:
    """计算两点之间的距离"""
    return math.sqrt(
        (pos2[0] - pos1[0]) ** 2 +
        (pos2[1] - pos1[1]) ** 2 +
        (pos2[2] - pos1[2]) ** 2
    )


def plan_path(points: list) -> float:
    """规划飞行路径，计算总距离"""
    total = 0
    for i in range(len(points) - 1):
        total += calculate_distance(points[i], points[i + 1])
    return total


if __name__ == "__main__":
    # 运行演示
    demo_basic_control()
    
    # 示例：路径规划
    print("\n路径规划示例:")
    waypoints = [
        (0, 0, 10),    # 起飞点
        (20, 0, 10),   # 点1
        (20, 20, 15),  # 点2
        (0, 20, 15),   # 点3
        (0, 0, 10)     # 返航点
    ]
    total_distance = plan_path(waypoints)
    print(f"航点: {waypoints}")
    print(f"总飞行距离: {total_distance:.2f} 米")
    print(f"预估飞行时间: {total_distance / 10 * 60:.0f} 秒 (按10m/s计算)")

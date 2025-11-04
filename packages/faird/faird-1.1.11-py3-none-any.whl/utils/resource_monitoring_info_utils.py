import psutil
import time
import json
import platform
import os
from typing import List, Optional, Dict, Any


# --- 辅助函数 ---

def bytes_to_gb(bytes_value: float) -> float:
    """将字节值转换为 GB 并保留两位小数"""
    return round(bytes_value / (1024 ** 3), 2)


def bytes_to_mbps(bytes_value: float, interval: int) -> float:
    """将字节/时间间隔转换为 MB/s 并保留三位小数"""
    BYTES_TO_MB = 1024 * 1024
    rate_bps = bytes_value / interval
    return round(rate_bps / BYTES_TO_MB, 3)


# --- 性能指标采集函数 ---

def get_network_metrics(interval: int = 1) -> Dict[str, float]:
    """
    统计指定时间间隔内的网络负载（接收、发送和总负载的速率），单位 MB/s。

    :param interval: 统计的时间间隔（秒）。
    :return: 包含接收、发送和总负载速率（MB/s）的字典。
    """
    # 1. 第一次记录
    # net_io_start = psutil.net_io_counters()
    # bytes_recv_start = net_io_start.bytes_recv
    # bytes_sent_start = net_io_start.bytes_sent
    #
    # # 等待指定时间间隔
    # time.sleep(interval)
    #
    # # 2. 第二次记录
    # net_io_end = psutil.net_io_counters()
    # bytes_recv_end = net_io_end.bytes_recv
    # bytes_sent_end = net_io_end.bytes_sent
    #
    # # 3. 计算差值 (总字节数)
    # bytes_recv_diff = bytes_recv_end - bytes_recv_start
    # bytes_sent_diff = bytes_sent_end - bytes_sent_start
    #
    # # 4. 转换为 MB/s
    # recv_rate_mbps = bytes_to_mbps(bytes_recv_diff, interval)
    # sent_rate_mbps = bytes_to_mbps(bytes_sent_diff, interval)
    #
    # # 5. 计算总负载速率
    # total_rate_mbps = recv_rate_mbps + sent_rate_mbps

    return {
        "receive_rate_mbps": 1,  # 接收速率 (MB/s)
        "send_rate_mbps": 1,  # 发送速率 (MB/s)
        "total_rate_mbps": 1  # 总负载速率 (MB/s)
    }


def get_load_average() -> Optional[Dict[str, float]]:
    """获取系统的 1/5/15 分钟平均负载（仅 Unix 系统）"""
    if platform.system() in ['Linux', 'Darwin']:
        load1, load5, load15 = os.getloadavg()
        return {
            "load_1_min": round(load1, 2),
            "load_5_min": round(load5, 2),
            "load_15_min": round(load15, 2)
        }
    return None


def get_cpu_info() -> Dict[str, Any]:
    """获取 CPU 物理核心数和使用率"""
    # psutil.cpu_percent(interval=1) 会阻塞 1 秒来计算准确的使用率
    return {
        "count": psutil.cpu_count(logical=False),
        "percent": psutil.cpu_percent(interval=1)
    }


def get_memory_info() -> Dict[str, Any]:
    """获取内存信息（GB 和 使用率）"""
    mem = psutil.virtual_memory()
    return {
        "total_gb": bytes_to_gb(mem.total),
        "used_gb": bytes_to_gb(mem.used),
        "percent": mem.percent
    }


def get_max_disk_info() -> Optional[Dict[str, Any]]:
    """获取最大的一块磁盘（基于总容量）的使用信息，单位 GB"""
    max_disk = None
    partitions = psutil.disk_partitions(all=False)

    for part in partitions:
        if 'cdrom' in part.opts or part.fstype in ['squashfs', 'tmpfs']:
            continue

        try:
            usage = psutil.disk_usage(part.mountpoint)
            if max_disk is None or usage.total > max_disk.get("total_bytes", 0):
                max_disk = {
                    "mount_point": part.mountpoint,
                    "total_gb": bytes_to_gb(usage.total),
                    "used_gb": bytes_to_gb(usage.used),
                    "percent": usage.percent,
                    "total_bytes": usage.total  # 用于内部比较
                }
        except Exception:
            continue

    # 移除内部比较字段 total_bytes
    if max_disk:
        max_disk.pop("total_bytes", None)

    return max_disk


# def get_system_metrics() -> Dict[str, Any]:
#     """获取服务器 CPU, 内存, 磁盘和平均负载指标"""
#     metrics = {
#         "cpu": get_cpu_info(),
#         "memory": get_memory_info(),
#         "disk": get_max_disk_info(),
#     }
#
#     # 仅在 Unix 系统下添加负载信息
#     if platform.system() in ['Linux', 'Darwin']:
#         metrics["load"] = get_load_average()
#
#     return metrics


# --- 主整合函数 ---
#
# def get_full_server_metrics_json(interval: int = 2) -> str:
#     """
#     整合网络负载和系统指标，并以单个 JSON 字符串返回。
#
#     :param interval: 统计网络负载和 CPU 使用率的时间间隔（秒），默认为 2 秒。
#     :return: 包含所有指标的 JSON 字符串。
#     """
#     print(f"开始采集服务器性能指标 (网络和 CPU 采样间隔: {interval} 秒)...")
#
#     # 1. 采集网络负载
#     network_metrics = get_network_metrics(interval=interval)
#
#     # 2. 采集系统基础指标
#     system_metrics = get_system_metrics()
#
#     # 3. 合并所有指标
#     final_metrics = {
#         "server_metrics": {
#             "network": network_metrics,
#             "system": system_metrics
#         }
#     }
#
#     # 4. 转换为 JSON 字符串
#     json_output = json.dumps(final_metrics, indent=4)
#
#     return json_output
#
#
if __name__ == "__main__":
    # # 统计 2 秒间隔内的所有指标，并获取 JSON 结果
    # full_stats_json = get_full_server_metrics_json(interval=2)
    # print(full_stats_json)

    resources = {
        "network": get_network_metrics(interval=2),
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "disk": get_max_disk_info()
    }
    # 仅在 Unix 系统下添加负载信息
    if platform.system() in ['Linux', 'Darwin']:
        resources["load"] = get_load_average()
    print(json.dumps(resources, indent=4))




"""
監控 API 端點
提供即時監控和趨勢分析數據
"""
import logging
from typing import Optional
from fastapi import APIRouter, Query

from src.utils.memory_monitor_store import get_monitor_store

logger = logging.getLogger(__name__)

# 建立路由器
router = APIRouter(
    prefix="/api/v1/monitoring",
    tags=["Monitoring"]
)


@router.get("/realtime")
async def get_realtime_monitoring(
    time_window_minutes: int = Query(60, description="時間窗口（分鐘）"),
    member_code: Optional[str] = Query(None, description="會員編號（可選）")
) -> dict:
    """
    獲取即時監控數據
    
    Args:
        time_window_minutes: 時間窗口（分鐘）
        member_code: 會員編號（可選）
        
    Returns:
        dict: 監控統計數據
    """
    monitor_store = get_monitor_store()
    stats = monitor_store.get_stats(time_window_minutes)
    
    return stats


@router.get("/alerts")
async def get_alerts(
    time_window_minutes: int = Query(60, description="時間窗口（分鐘）")
) -> dict:
    """
    獲取告警記錄
    
    Args:
        time_window_minutes: 時間窗口（分鐘）
        
    Returns:
        dict: 告警記錄
    """
    # 目前返回空列表，因為告警功能需要進一步實現
    return {
        "total_alerts": 0,
        "alerts": []
    }


@router.get("/records")
async def get_monitoring_records(
    time_window_minutes: int = Query(60, description="時間窗口（分鐘）"),
    member_code: Optional[str] = Query(None, description="會員編號（可選）"),
    limit: int = Query(100, description="最大記錄數")
) -> dict:
    """
    獲取監控記錄
    
    Args:
        time_window_minutes: 時間窗口（分鐘）
        member_code: 會員編號（可選）
        limit: 最大記錄數
        
    Returns:
        dict: 監控記錄列表
    """
    monitor_store = get_monitor_store()
    records = monitor_store.get_records(time_window_minutes, member_code)
    
    # 限制返回數量
    records = records[-limit:] if len(records) > limit else records
    
    return {
        "total_records": len(records),
        "records": records
    }

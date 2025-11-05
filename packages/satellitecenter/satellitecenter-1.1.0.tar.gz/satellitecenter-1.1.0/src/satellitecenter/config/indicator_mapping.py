"""指标映射配置模块"""

from __future__ import annotations

from typing import Any, Dict, List

INDICATOR_MAPPING: Dict[str, List[str]] = {
    "Turb": [
        "turbidity",
        "浊度",
        "turb",
    ],
    "SS": [
        "ss",
        "悬浮物",
        "suspended solids",
    ],
    "DO": [
        "do",
        "溶解氧",
        "dissolved oxygen",
    ],
    "COD": [
        "cod",
        "codcr",
        "化学需氧量",
        "chemical oxygen demand",
    ],
    "CODMn": [
        "codmn",
        "高锰酸盐",
        "高锰酸盐指数",
    ],
    "BOD": [
        "bod",
        "bod5",
        "生化需氧量",
        "biochemical oxygen demand",
    ],
    "NH3-N": [
        "nh3-n",
        "nh3n",
        "氨氮",
        "nh3_n",
        "ammonia nitrogen",
    ],
    "TN": [
        "tn",
        "总氮",
        "total nitrogen",
    ],
    "TP": [
        "tp",
        "总磷",
        "total phosphorus",
    ],
    "pH": [
        "ph",
        "ph值",
    ],
    "EC": [
        "ec",
        "电导率",
        "conductivity",
    ],
    "Temp": [
        "temp",
        "温度",
        "temperature",
    ],
    "BGA": [
        "bga",
        "蓝绿藻",
    ],
    "Chla": [
        "chla",
        "叶绿素",
        "叶绿素a",
        "chlorophyll",
        "chl",
        "chl_a",
    ],
    "SD": [
        "sd",
        "透明度",
    ],
    "Chroma": [
        "chroma",
        "色度",
    ],
    "NDVI": [
        "ndvi",
        "归一化植被指数",
        "normalized difference vegetation index",
    ],
}

DESCRIPTION: str = "Water quality and environmental parameters indicator name mapping"
VERSION: str = "1.0"

CONFIG: Dict[str, Any] = {
    "indicator_mapping": INDICATOR_MAPPING,
    "description": DESCRIPTION,
    "version": VERSION,
}

__all__ = ["INDICATOR_MAPPING", "DESCRIPTION", "VERSION", "CONFIG"]

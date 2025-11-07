"""工具函数测试"""
import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from src.langchain_agent.tools import get_current_time


class TestGetCurrentTime:
    """测试 get_current_time 工具"""
    
    def test_utc_time(self):
        """测试 UTC 时间"""
        result = get_current_time("UTC")
        # 验证格式是否正确 (HH:MM:SS)
        assert len(result) == 8
        assert result.count(":") == 2
        
        # 验证各部分是否为数字
        parts = result.split(":")
        assert all(part.isdigit() for part in parts)
    
    def test_shanghai_time(self):
        """测试上海时间"""
        result = get_current_time("Asia/Shanghai")
        assert len(result) == 8
        assert result.count(":") == 2
    
    def test_invalid_timezone(self):
        """测试无效时区"""
        with pytest.raises(ValueError) as exc_info:
            get_current_time("Invalid/Timezone")
        assert "无效的时区名称" in str(exc_info.value)
    
    def test_default_timezone(self):
        """测试默认时区（UTC）"""
        result = get_current_time()
        assert len(result) == 8
    
    def test_time_format(self):
        """测试时间格式的准确性"""
        result = get_current_time("UTC")
        hours, minutes, seconds = map(int, result.split(":"))
        
        # 验证范围
        assert 0 <= hours < 24
        assert 0 <= minutes < 60
        assert 0 <= seconds < 60


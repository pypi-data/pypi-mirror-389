"""配置测试"""
import os
import pytest
from src.langchain_agent.config import LLMConfig, AgentConfig, AppConfig


class TestLLMConfig:
    """测试 LLM 配置"""
    
    def test_default_values(self):
        """测试默认值"""
        config = LLMConfig()
        assert config.model == "gpt-oss"
        assert config.temperature == 0.0
        assert config.max_tokens == 1000
        assert config.verbose is False
    
    def test_from_env(self, monkeypatch):
        """测试从环境变量加载"""
        monkeypatch.setenv("LLM_MODEL", "test-model")
        monkeypatch.setenv("LLM_TEMPERATURE", "0.5")
        monkeypatch.setenv("LLM_MAX_TOKENS", "2000")
        monkeypatch.setenv("LLM_VERBOSE", "true")
        
        config = LLMConfig.from_env()
        assert config.model == "test-model"
        assert config.temperature == 0.5
        assert config.max_tokens == 2000
        assert config.verbose is True


class TestAgentConfig:
    """测试 Agent 配置"""
    
    def test_default_values(self):
        """测试默认值"""
        config = AgentConfig()
        assert "helpful assistant" in config.system_prompt.lower()
    
    def test_from_env(self, monkeypatch):
        """测试从环境变量加载"""
        custom_prompt = "Custom system prompt"
        monkeypatch.setenv("AGENT_SYSTEM_PROMPT", custom_prompt)
        
        config = AgentConfig.from_env()
        assert config.system_prompt == custom_prompt


class TestAppConfig:
    """测试应用配置"""
    
    def test_from_env(self):
        """测试从环境变量加载完整配置"""
        config = AppConfig.from_env()
        assert isinstance(config.llm, LLMConfig)
        assert isinstance(config.agent, AgentConfig)


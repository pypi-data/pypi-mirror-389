"""
Tests for provider adapters
"""
import pytest
from core.provider.noop_adapter import NoopAdapter
from core.provider.base_adapter import ProviderAdapter
from core.types import (
    ProviderConfig,
    ProviderType,
    Prompt,
    GenerateOptions,
    IntentType,
)


class TestNoopAdapter:
    """Test the noop adapter"""
    
    def setup_method(self):
        config = ProviderConfig(
            id="test",
            provider=ProviderType.NOOP,
            model="mock",
        )
        self.adapter = NoopAdapter(config)
    
    def test_initialize(self):
        """Test adapter initialization"""
        self.adapter.initialize()
        assert self.adapter.initialized
    
    def test_generate(self):
        """Test basic generation"""
        prompt = Prompt(user_query="test query", shell_type="bash")
        options = GenerateOptions()
        
        response = self.adapter.generate(prompt, options)
        
        assert response.intent == IntentType.RUNNABLE_COMMAND
        assert len(response.commands) > 0
        assert response.commands[0].cmd == "echo 'test'"
    
    def test_stream_generate(self):
        """Test streaming generation"""
        prompt = Prompt(user_query="test query", shell_type="bash")
        options = GenerateOptions()
        
        chunks = []
        def on_chunk(chunk):
            chunks.append(chunk)
        
        response = self.adapter.stream_generate(prompt, options, on_chunk)
        
        assert len(chunks) > 0
        assert response.intent == IntentType.RUNNABLE_COMMAND
    
    def test_health_check(self):
        """Test health check"""
        status = self.adapter.health_check()
        
        assert status.healthy
        assert status.provider == "noop"
    
    def test_cost_estimate(self):
        """Test cost estimation"""
        prompt = Prompt(user_query="test query", shell_type="bash")
        
        estimate = self.adapter.token_cost_estimate(prompt)
        
        assert estimate.estimated_tokens > 0
        assert estimate.estimated_cost_usd == 0.0
        assert estimate.provider == "noop"


class TestAdapterInterface:
    """Test that all adapters implement the interface correctly"""
    
    def test_noop_adapter_implements_interface(self):
        """Verify noop adapter implements all required methods"""
        config = ProviderConfig(
            id="test",
            provider=ProviderType.NOOP,
            model="mock",
        )
        adapter = NoopAdapter(config)
        
        # Check all abstract methods are implemented
        assert hasattr(adapter, 'initialize')
        assert hasattr(adapter, 'generate')
        assert hasattr(adapter, 'stream_generate')
        assert hasattr(adapter, 'function_call')
        assert hasattr(adapter, 'health_check')
        assert hasattr(adapter, 'token_cost_estimate')
        assert hasattr(adapter, 'close')


if __name__ == '__main__':
    pytest.main([__file__])

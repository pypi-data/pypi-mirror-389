"""
Integration tests for heybud
"""
import pytest
import tempfile
from pathlib import Path

from core.config import ConfigManager
from core.context import ContextManager
from core.orchestrator import ProviderOrchestrator
from core.types import (
    ProviderConfig,
    ProviderType,
    Prompt,
    GenerateOptions,
    IntentType,
)


class TestEndToEnd:
    """End-to-end integration tests"""
    
    def setup_method(self):
        # Use temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.heybud_dir = Path(self.temp_dir) / ".heybud"
        self.heybud_dir.mkdir()
    
    def test_full_query_flow(self):
        """Test complete query flow from prompt to response"""
        # Setup
        config_mgr = ConfigManager(self.heybud_dir)
        context_mgr = ContextManager(self.heybud_dir)
        
        # Configure noop provider for testing
        provider = ProviderConfig(
            id="test",
            provider=ProviderType.NOOP,
            model="mock",
            priority=1,
        )
        config_mgr.config.providers = [provider]
        config_mgr.save_config()
        
        # Create orchestrator
        orchestrator = ProviderOrchestrator([provider])
        
        # Generate response
        prompt = Prompt(
            user_query="create a python virtual environment",
            shell_type="bash",
        )
        
        response = orchestrator.generate(prompt, GenerateOptions())
        
        # Verify response
        assert response.intent == IntentType.RUNNABLE_COMMAND
        assert len(response.commands) > 0
        
        # Save last command
        context_mgr.save_last_command(response)
        
        # Load it back
        loaded = context_mgr.load_last_command()
        assert loaded is not None
        assert len(loaded.commands) == len(response.commands)
    
    def test_config_persistence(self):
        """Test configuration is saved and loaded correctly"""
        config_mgr = ConfigManager(self.heybud_dir)
        
        # Add provider
        provider = ProviderConfig(
            id="test-provider",
            provider=ProviderType.OPENAI,
            model="gpt-4",
            priority=1,
            api_key_name="OPENAI_API_KEY",
        )
        
        config_mgr.config.providers = [provider]
        config_mgr.save_config()
        
        # Create new config manager (simulates restart)
        new_config_mgr = ConfigManager(self.heybud_dir)
        
        # Verify config loaded
        assert len(new_config_mgr.config.providers) == 1
        assert new_config_mgr.config.providers[0].id == "test-provider"
        assert new_config_mgr.config.providers[0].model == "gpt-4"


if __name__ == '__main__':
    pytest.main([__file__])

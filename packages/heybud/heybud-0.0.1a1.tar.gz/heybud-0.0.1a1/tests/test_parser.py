"""
Tests for response parser
"""
import pytest
import json
from core.parser import ResponseParser
from core.types import IntentType


class TestResponseParser:
    """Test LLM response parsing"""
    
    def setup_method(self):
        self.parser = ResponseParser()
    
    def test_parse_json_response(self):
        """Test parsing valid JSON response"""
        json_response = json.dumps({
            "intent": "runnable_command",
            "explanation": "Create a virtual environment",
            "commands": [
                {
                    "id": "c1",
                    "cmd": "python3 -m venv venv",
                    "description": "Create venv",
                    "runnable": True,
                }
            ],
            "safety": {
                "risk_score": 0.1,
                "warnings": [],
            }
        })
        
        response = self.parser.parse(json_response, "test", "test-model")
        
        assert response.intent == IntentType.RUNNABLE_COMMAND
        assert response.explanation == "Create a virtual environment"
        assert len(response.commands) == 1
        assert response.commands[0].cmd == "python3 -m venv venv"
        assert response.safety.risk_score == 0.1
    
    def test_parse_json_in_code_block(self):
        """Test parsing JSON wrapped in markdown code blocks"""
        markdown_response = '''
Here's what you need:

```json
{
    "intent": "runnable_command",
    "explanation": "Install Flask",
    "commands": [
        {"id": "c1", "cmd": "pip install flask", "description": "Install Flask"}
    ]
}
```
'''
        
        response = self.parser.parse(markdown_response, "test", "test-model")
        
        assert response.intent == IntentType.RUNNABLE_COMMAND
        assert len(response.commands) == 1
        assert "flask" in response.commands[0].cmd.lower()
    
    def test_parse_text_with_code_blocks(self):
        """Test parsing plain text with bash code blocks"""
        text_response = '''
To create a virtual environment, run:

```bash
python3 -m venv venv
source venv/bin/activate
```
'''
        
        response = self.parser.parse(text_response, "test", "test-model")
        
        assert len(response.commands) >= 1
        assert "venv" in response.commands[0].cmd
    
    def test_parse_plain_text(self):
        """Test parsing plain text without code blocks"""
        text_response = "This is just an explanation without commands."
        
        response = self.parser.parse(text_response, "test", "test-model")
        
        # Should default to explanation
        assert response.intent == IntentType.EXPLANATION
        assert len(response.commands) == 0
    
    def test_extract_commands_from_text(self):
        """Test extracting commands from plain text"""
        text = "First, run: cd /tmp\nThen: ls -la\nFinally: cat file.txt"
        
        response = self.parser.parse(text, "test", "test-model")
        
        # Should extract cd and ls commands
        assert len(response.commands) >= 2


if __name__ == '__main__':
    pytest.main([__file__])

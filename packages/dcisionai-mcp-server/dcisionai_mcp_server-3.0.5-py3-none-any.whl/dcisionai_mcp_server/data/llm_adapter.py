"""
LLM adapter for data simulator

Bridges model-builder's LLM interface with platform's LLM setup
"""

import logging
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import anthropic
import openai


@dataclass
class LLMRequest:
    """LLM request specification"""
    prompt: str
    max_tokens: int = 1000
    temperature: float = 0.7
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """LLM response"""
    content: str
    metadata: Optional[Dict[str, Any]] = None


class LLMManager:
    """
    Simple LLM manager that wraps Anthropic/OpenAI
    
    Compatible with data simulator's expected interface
    """
    
    def __init__(self, provider: str = "anthropic"):
        """
        Initialize LLM manager
        
        Args:
            provider: "anthropic" or "openai"
        """
        self.provider = provider
        self.logger = logging.getLogger(__name__)
        
        if provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set")
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = "claude-3-5-sonnet-20241022"
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set")
            self.client = openai.OpenAI(api_key=api_key)
            self.model = "gpt-4-turbo-preview"
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate LLM response
        
        Args:
            request: LLMRequest with prompt and parameters
        
        Returns:
            LLMResponse with generated content
        """
        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    messages=[
                        {"role": "user", "content": request.prompt}
                    ]
                )
                content = response.content[0].text
            else:  # openai
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    messages=[
                        {"role": "user", "content": request.prompt}
                    ]
                )
                content = response.choices[0].message.content
            
            return LLMResponse(
                content=content,
                metadata=request.metadata
            )
            
        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if LLM is available"""
        try:
            if self.provider == "anthropic":
                return bool(os.getenv("ANTHROPIC_API_KEY"))
            else:
                return bool(os.getenv("OPENAI_API_KEY"))
        except Exception:
            return False


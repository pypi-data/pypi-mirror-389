#!/usr/bin/env python3
"""
Simple LLM Client - Anthropic with OpenAI fallback

Provides a clean interface for LLM calls with automatic fallback.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Simple LLM client with Anthropic primary, OpenAI fallback
    """
    
    def __init__(self):
        """Initialize LLM clients"""
        self.anthropic_client = None
        self.openai_client = None
        self.call_count = 0
        
        # Initialize Anthropic
        try:
            import anthropic
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                logger.info("✅ Anthropic client initialized")
        except Exception as e:
            logger.warning(f"⚠️ Anthropic init failed: {e}")
        
        # Initialize OpenAI
        try:
            import openai
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.info("✅ OpenAI client initialized")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI init failed: {e}")
        
        if not self.anthropic_client and not self.openai_client:
            raise ValueError("No LLM API keys configured (ANTHROPIC_API_KEY or OPENAI_API_KEY)")
    
    
    async def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> str:
        """
        Generate text using LLM
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: 0.0 = deterministic, 1.0 = creative
            max_tokens: Maximum response tokens
        
        Returns:
            Generated text
        """
        self.call_count += 1
        
        # Alternate between providers for load balancing
        use_anthropic_first = (self.call_count % 2 == 1)
        
        providers = [
            ('Anthropic', self._call_anthropic),
            ('OpenAI', self._call_openai)
        ]
        
        if not use_anthropic_first:
            providers.reverse()
        
        # Try providers in order
        for provider_name, provider_func in providers:
            try:
                result = provider_func(prompt, system_prompt, temperature, max_tokens)
                logger.debug(f"✅ LLM call succeeded: {provider_name}")
                return result
            except Exception as e:
                logger.warning(f"⚠️ {provider_name} failed: {e}, trying fallback")
                continue
        
        # Both failed
        raise RuntimeError("All LLM providers failed")
    
    
    def _call_anthropic(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Call Anthropic Claude"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")
        
        response = self.anthropic_client.messages.create(
            model='claude-3-5-haiku-20241022',
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt if system_prompt else "You are a helpful assistant.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text
    
    
    def _call_openai(
        self,
        prompt: str,
        system_prompt: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """Call OpenAI GPT"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content


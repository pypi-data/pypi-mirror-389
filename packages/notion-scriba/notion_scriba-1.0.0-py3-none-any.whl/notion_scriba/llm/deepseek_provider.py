# Notion Scriba - AI-powered bilingual documentation generator
# Copyright (C) 2025 Davide Baldoni
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""DeepSeek models provider."""

from typing import Optional
from openai import OpenAI

from .base import BaseLLMProvider


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek models provider.
    
    DeepSeek uses OpenAI-compatible API, making integration simple.
    
    Supports:
    - deepseek-chat (general purpose, very cost-effective)
    - deepseek-coder (specialized for code tasks)
    """
    
    def _initialize_client(self):
        """Initialize DeepSeek client using OpenAI compatibility."""
        return OpenAI(
            api_key=self.config.api_key,
            base_url="https://api.deepseek.com"
        )
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using DeepSeek.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            
        Returns:
            Generated text from DeepSeek
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        return response.choices[0].message.content
    
    def get_token_count(self, text: str) -> int:
        """Estimate token count.
        
        DeepSeek doesn't provide public tokenizer,
        using standard approximation.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Approximation: ~4 characters per token
        return len(text) // 4
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "DeepSeek"

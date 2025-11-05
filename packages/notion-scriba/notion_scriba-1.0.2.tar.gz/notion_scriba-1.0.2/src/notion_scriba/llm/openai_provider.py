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


"""OpenAI GPT models provider."""

from typing import Optional
from openai import OpenAI
import tiktoken

from .base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT models provider.
    
    Supports:
    - GPT-4o (latest flagship model)
    - GPT-4-turbo
    - GPT-3.5-turbo (cost-effective)
    """
    
    def _initialize_client(self):
        """Initialize OpenAI client."""
        return OpenAI(api_key=self.config.api_key)
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using OpenAI chat completion.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            
        Returns:
            Generated text from the model
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.timeout
        )
        
        return response.choices[0].message.content
    
    def get_token_count(self, text: str) -> int:
        """Get accurate token count using tiktoken.
        
        Args:
            text: Input text
            
        Returns:
            Exact token count for the model
        """
        try:
            encoder = tiktoken.encoding_for_model(self.config.model)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            encoder = tiktoken.get_encoding("cl100k_base")
        
        return len(encoder.encode(text))
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "OpenAI"

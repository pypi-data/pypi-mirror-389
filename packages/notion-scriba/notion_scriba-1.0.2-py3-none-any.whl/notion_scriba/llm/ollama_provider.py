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


"""Ollama local models provider."""

from typing import Optional
import requests

from .base import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    """Ollama local models provider.
    
    Run AI models locally on your machine for:
    - Complete privacy (no data sent to cloud)
    - No API costs
    - Offline operation
    
    Supports popular models:
    - Llama 3.1 (Meta's latest)
    - Mistral
    - CodeLlama (code-specialized)
    - And many more from ollama.ai/library
    
    Prerequisites:
        Install Ollama from https://ollama.ai
        Pull models: ollama pull llama3.1
    """
    
    def _initialize_client(self):
        """Initialize Ollama connection.
        
        Ollama runs locally, no authentication needed.
        """
        self.base_url = self.config.extra_params.get(
            "base_url", 
            "http://localhost:11434"
        )
        
        # Verify Ollama is running
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Make sure Ollama is running. Error: {e}"
            )
        
        return None  # No client object needed
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text using Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            
        Returns:
            Generated text from local model
            
        Raises:
            requests.RequestException: If Ollama request fails
        """
        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }
        
        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.config.timeout
        )
        response.raise_for_status()
        
        return response.json()["response"]
    
    def get_token_count(self, text: str) -> int:
        """Estimate token count.
        
        Ollama doesn't provide built-in tokenizer access,
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
        return "Ollama"

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


"""Base classes for LLM provider abstraction."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    """Configuration for LLM provider.
    
    Attributes:
        api_key: API key for the provider
        model: Model name/identifier
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens to generate
        timeout: Request timeout in seconds
        extra_params: Provider-specific additional parameters
    """
    api_key: str
    model: str
    temperature: float = 0.3
    max_tokens: int = 4000
    timeout: int = 60
    extra_params: Dict[str, Any] = field(default_factory=dict)


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.
    
    All LLM providers must implement this interface to ensure
    consistent behavior across different AI services.
    """
    
    def __init__(self, config: LLMConfig):
        """Initialize provider with configuration.
        
        Args:
            config: LLMConfig instance with provider settings
        """
        self.config = config
        self.client = self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self):
        """Initialize provider-specific client.
        
        Returns:
            Initialized client object for the provider
        """
        pass
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text from prompt.
        
        Args:
            prompt: User prompt/request
            system_prompt: Optional system-level instructions
            
        Returns:
            Generated text response
            
        Raises:
            Exception: Provider-specific errors
        """
        pass
    
    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """Estimate token count for text.
        
        Args:
            text: Input text to count
            
        Returns:
            Estimated number of tokens
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name.
        
        Returns:
            Human-readable provider name
        """
        pass
    
    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(model={self.config.model})"

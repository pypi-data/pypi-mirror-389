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


"""Factory for creating LLM provider instances."""

from typing import Type, Dict, TYPE_CHECKING

from .base import BaseLLMProvider, LLMConfig
from .openai_provider import OpenAIProvider
from .deepseek_provider import DeepSeekProvider
from .ollama_provider import OllamaProvider

# Optional providers - imported lazily
if TYPE_CHECKING:
    from .anthropic_provider import AnthropicProvider
    from .google_provider import GoogleProvider


class LLMProviderFactory:
    """Factory for creating LLM provider instances.
    
    Centralized provider management with automatic discovery
    and default model configuration.
    
    Example:
        >>> config = LLMConfig(api_key="sk-...", model="gpt-4o")
        >>> provider = LLMProviderFactory.create("openai", config)
        >>> response = provider.generate("Write documentation for...")
    """
    
    # Registry of available providers (only core providers loaded initially)
    _providers: Dict[str, Type[BaseLLMProvider]] = {
        "openai": OpenAIProvider,
        "deepseek": DeepSeekProvider,
        "ollama": OllamaProvider,
    }
    
    # Default models for each provider
    _default_models: Dict[str, str] = {
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-20241022",
        "claude": "claude-3-5-sonnet-20241022",
        "google": "gemini-1.5-pro",
        "gemini": "gemini-1.5-pro",
        "deepseek": "deepseek-chat",
        "ollama": "llama3.1",
    }
    
    # Pricing information (per 1M tokens, approximate)
    _pricing_info: Dict[str, str] = {
        "openai": "$5-15 (varies by model)",
        "anthropic": "$3-15 (varies by model)",
        "claude": "$3-15 (varies by model)",
        "google": "Free tier available, then $1-7",
        "gemini": "Free tier available, then $1-7",
        "deepseek": "$0.14-0.28 (very cost-effective)",
        "ollama": "FREE (runs locally)",
    }
    
    @classmethod
    def _load_optional_provider(cls, provider: str) -> None:
        """Dynamically load optional provider if not already loaded.
        
        Args:
            provider: Provider name to load (anthropic, claude, google, gemini)
        """
        provider_lower = provider.lower()
        
        # Skip if already loaded
        if provider_lower in cls._providers:
            return
            
        # Load Anthropic provider
        if provider_lower in ("anthropic", "claude"):
            try:
                from .anthropic_provider import AnthropicProvider
                cls._providers["anthropic"] = AnthropicProvider
                cls._providers["claude"] = AnthropicProvider
            except ImportError:
                raise ImportError(
                    "Anthropic support not installed. "
                    "Install with: pip install notion-scriba[anthropic]"
                )
        
        # Load Google provider
        elif provider_lower in ("google", "gemini"):
            try:
                from .google_provider import GoogleProvider
                cls._providers["google"] = GoogleProvider
                cls._providers["gemini"] = GoogleProvider
            except ImportError:
                raise ImportError(
                    "Google Gemini support not installed. "
                    "Install with: pip install notion-scriba[google]"
                )
    
    @classmethod
    def create(cls, provider: str, config: LLMConfig) -> BaseLLMProvider:
        """Create LLM provider instance.
        
        Args:
            provider: Provider name (openai, anthropic, google, etc.)
            config: LLMConfig with provider settings
            
        Returns:
            Initialized provider instance
            
        Raises:
            ValueError: If provider is unknown
            ImportError: If optional provider dependencies not installed
            
        Example:
            >>> config = LLMConfig(api_key="sk-...", model="gpt-4o")
            >>> provider = LLMProviderFactory.create("openai", config)
        """
        provider_lower = provider.lower()
        
        # Try to load optional provider if not in registry
        if provider_lower not in cls._providers:
            if provider_lower in ("anthropic", "claude", "google", "gemini"):
                cls._load_optional_provider(provider_lower)
            else:
                available = ", ".join(sorted(set(cls._providers.keys())))
                raise ValueError(
                    f"Unknown provider: '{provider}'. "
                    f"Available providers: {available}"
                )
        
        provider_class = cls._providers[provider_lower]
        return provider_class(config)
    
    @classmethod
    def get_default_model(cls, provider: str) -> str:
        """Get default model for provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Default model identifier for the provider
            
        Example:
            >>> LLMProviderFactory.get_default_model("openai")
            'gpt-4o'
        """
        return cls._default_models.get(provider.lower(), "gpt-4o")
    
    @classmethod
    def list_providers(cls) -> list:
        """List all available providers.
        
        Returns:
            Sorted list of unique provider names
            
        Example:
            >>> LLMProviderFactory.list_providers()
            ['anthropic', 'claude', 'deepseek', 'gemini', 'google', 'ollama', 'openai']
        """
        return sorted(set(cls._providers.keys()))
    
    @classmethod
    def get_provider_info(cls) -> Dict[str, Dict[str, str]]:
        """Get detailed information about all providers.
        
        Returns:
            Dictionary with provider details (model, pricing, etc.)
            
        Example:
            >>> info = LLMProviderFactory.get_provider_info()
            >>> print(info['openai']['default_model'])
            'gpt-4o'
        """
        unique_providers = {}
        
        for provider in sorted(set(cls._providers.keys())):
            if provider not in ["claude", "gemini"]:  # Skip aliases
                unique_providers[provider] = {
                    "default_model": cls._default_models.get(provider, "N/A"),
                    "pricing": cls._pricing_info.get(provider, "N/A"),
                    "class": cls._providers[provider].__name__
                }
        
        return unique_providers
    
    @classmethod
    def print_providers_info(cls):
        """Print formatted provider information to console."""
        print("\n🤖 Available LLM Providers:")
        print("=" * 70)
        
        info = cls.get_provider_info()
        
        for provider, details in info.items():
            print(f"\n📌 {provider.upper()}")
            print(f"   Default Model: {details['default_model']}")
            print(f"   Pricing: {details['pricing']}")
            print(f"   Implementation: {details['class']}")
        
        print("\n" + "=" * 70)
        print("💡 Tip: Use aliases 'claude' for anthropic, 'gemini' for google")
        print()

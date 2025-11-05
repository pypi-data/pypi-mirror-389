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


"""
LLM Provider abstraction layer.

Supports multiple AI providers:
- OpenAI (GPT-4, GPT-4o, GPT-3.5-turbo)
- Anthropic (Claude 3.5 Sonnet, Opus, Haiku)
- Google (Gemini 1.5 Pro, Flash)
- DeepSeek (DeepSeek Chat, Coder)
- Ollama (Local models: Llama, Mistral, etc.)
"""

from .base import BaseLLMProvider, LLMConfig
from .factory import LLMProviderFactory

__all__ = ["BaseLLMProvider", "LLMConfig", "LLMProviderFactory"]

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
Notion Scriba - AI-powered documentation generator for Notion.

A modular system for automatic documentation generation with support
for multiple LLM providers and direct Notion synchronization.

"Verba volant, scripta manent" - Spoken words fly away, written words remain.
"""

__version__ = "1.1.0"

# Core components
from .llm import LLMProviderFactory, BaseLLMProvider, LLMConfig
from .code_analyzer import CodeAnalyzer
from .templates import DocumentationTemplates
from .doc_generator import DocumentationGenerator
from .notion_client import NotionClient
from .cli import NotionScribaCLI, main

__all__ = [
    "LLMProviderFactory",
    "BaseLLMProvider",
    "LLMConfig",
    "CodeAnalyzer",
    "DocumentationTemplates",
    "DocumentationGenerator",
    "NotionClient",
    "NotionScribaCLI",
    "main",
]

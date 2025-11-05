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
Documentation Generator
-----------------------
AI-powered documentation generation using LLM providers and templates.
"""

from typing import Optional, Dict, Tuple
from .llm import BaseLLMProvider
from .templates import DocumentationTemplates
from .code_analyzer import CodeAnalyzer


class DocumentationGenerator:
    """
    Generate professional documentation using AI and templates.
    
    Combines:
    - Code analysis for context
    - Professional templates
    - LLM generation
    - Bilingual output (IT/EN)
    """
    
    def __init__(self, llm_provider: BaseLLMProvider):
        """
        Initialize generator with LLM provider.
        
        Args:
            llm_provider: Initialized LLM provider instance
        """
        self.llm = llm_provider
        self.code_analyzer = CodeAnalyzer(max_files=15, max_code_length=10000)
        self.templates = DocumentationTemplates()
    
    def generate(
        self,
        component: str,
        template: str = "technical-deep-dive",
        user_prompt: Optional[str] = None,
        code_context: Optional[str] = None,
        project_root: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate bilingual documentation (IT + EN).
        
        Args:
            component: Component name to document
            template: Template name (investment-grade, technical-deep-dive, etc.)
            user_prompt: Optional custom user prompt
            code_context: Optional pre-analyzed code context
            project_root: Optional project root for code analysis
            
        Returns:
            Tuple of (italian_doc, english_doc)
        """
        print(f"\n🤖 Generating documentation for: {component}")
        print(f"   Template: {template}")
        print(f"   Provider: {self.llm.provider_name}")
        
        # Step 1: Get code context
        if code_context is None:
            print("\n🔍 Analyzing code...")
            analysis = self.code_analyzer.analyze_component(component, project_root)
            code_context = analysis.get("summary", "")
        
        # Step 2: Build prompt from template
        try:
            template_prompt = self.templates.get_template(template, code_context, component)
        except ValueError as e:
            print(f"⚠️  {e}")
            print("   Using fallback template")
            template_prompt = self.templates.fallback_documentation(component)
        
        # Step 3: Add user customization if provided
        if user_prompt:
            full_prompt = f"{user_prompt}\n\n{template_prompt}"
        else:
            full_prompt = template_prompt
        
        # Step 4: Generate Italian documentation
        print("\n🇮🇹 Generating Italian documentation...")
        italian_system_prompt = (
            "You are an expert technical writer. "
            "Generate professional documentation in ITALIAN language. "
            "Use clear, precise Italian terminology."
        )
        italian_doc = self.llm.generate(full_prompt, italian_system_prompt)
        print(f"   ✅ Generated: {len(italian_doc)} characters")
        
        # Step 5: Generate English documentation
        print("\n🇬🇧 Generating English documentation...")
        english_system_prompt = (
            "You are an expert technical writer. "
            "Generate professional documentation in ENGLISH language. "
            "Use clear, precise technical terminology."
        )
        english_doc = self.llm.generate(full_prompt, english_system_prompt)
        print(f"   ✅ Generated: {len(english_doc)} characters")
        
        return italian_doc, english_doc
    
    def generate_from_prompt(
        self,
        prompt: str,
        component: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate documentation from custom prompt only.
        
        Args:
            prompt: Custom user prompt
            component: Optional component name for context
            
        Returns:
            Tuple of (italian_doc, english_doc)
        """
        comp_name = component or "Documentation"
        print(f"\n🤖 Generating from custom prompt: {comp_name}")
        
        # Generate Italian
        italian_system = (
            "You are an expert technical writer. "
            "Generate professional documentation in ITALIAN language."
        )
        italian_doc = self.llm.generate(prompt, italian_system)
        
        # Generate English
        english_system = (
            "You are an expert technical writer. "
            "Generate professional documentation in ENGLISH language."
        )
        english_doc = self.llm.generate(prompt, english_system)
        
        return italian_doc, english_doc


# ============================================================================
# Quick test/example
# ============================================================================

if __name__ == "__main__":
    print("📝 DOCUMENTATION GENERATOR")
    print("=" * 60)
    print("\nThis module requires an initialized LLM provider.")
    print("\nExample usage:")
    print("""
from llm import LLMProviderFactory, LLMConfig
from doc_generator import DocumentationGenerator

# Setup LLM
config = LLMConfig(api_key="your-key", model="gpt-4o")
provider = LLMProviderFactory.create("openai", config)

# Generate docs
generator = DocumentationGenerator(provider)
it_doc, en_doc = generator.generate(
    component="api",
    template="technical-deep-dive"
)

print("IT:", it_doc[:200])
print("EN:", en_doc[:200])
    """)

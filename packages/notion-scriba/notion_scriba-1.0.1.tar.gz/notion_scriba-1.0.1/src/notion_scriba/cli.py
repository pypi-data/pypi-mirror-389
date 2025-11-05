#!/usr/bin/env python3
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
Command-line interface for Notion Scriba.

Main entry point for the documentation generator with multi-LLM support.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from .llm import LLMProviderFactory, LLMConfig
from .code_analyzer import CodeAnalyzer
from .templates import DocumentationTemplates
from .doc_generator import DocumentationGenerator
from .notion_client import NotionClient
from .setup_wizard import run_setup_wizard
from .interactive_mode import run_interactive_mode


class NotionScribaCLI:
    """Main CLI application for Notion Scriba."""
    
    def __init__(self, args: argparse.Namespace):
        """Initialize CLI with parsed arguments.
        
        Args:
            args: Parsed command-line arguments
        """
        self.args = args
        
        # Load environment variables
        load_dotenv()
        
        # Initialize components (will be set in run())
        self.llm_provider = None
        self.code_analyzer = None
        self.doc_generator = None
        self.notion_client = None
    
    def run(self):
        """Execute the CLI workflow."""
        try:
            # Print header
            self._print_header()
            
            # Step 1: Initialize LLM provider
            self.llm_provider = self._initialize_llm_provider()
            
            # Step 2: Initialize code analyzer (if needed)
            if not self.args.no_code_analysis:
                self.code_analyzer = CodeAnalyzer()
            
            # Step 3: Initialize documentation generator
            self.doc_generator = DocumentationGenerator(self.llm_provider)
            
            # Step 4: Initialize Notion client
            self.notion_client = self._initialize_notion_client()
            
            # Step 5: Generate documentation
            print("\n🤖 Generating documentation...")
            
            # Determine component and template
            component = self.args.component or "project"
            template = self.args.template or "technical-deep-dive"
            
            # Get user prompt (quick mode or default)
            prompt = self._get_prompt()
            
            # Analyze code if enabled
            code_analysis = None
            if self.code_analyzer and self.args.component:
                print(f"\n🔍 Analyzing component: {component}")
                code_analysis = self.code_analyzer.analyze_component(
                    component,
                    max_files=15
                )
                if code_analysis:
                    print(f"   ✅ Analyzed {code_analysis.get('total_files', 0)} files")
            
            # Generate documentation
            it_doc, en_doc = self.doc_generator.generate_bilingual(
                component=component,
                template_name=template,
                user_prompt=prompt,
                code_analysis=code_analysis
            )
            
            print(f"\n   ✅ Documentation generated!")
            print(f"      IT: {len(it_doc)} characters")
            print(f"      EN: {len(en_doc)} characters")
            
            # Step 6: Sync to Notion
            if self.notion_client:
                print("\n📤 Syncing to Notion...")
                
                # Format title
                title = component.replace("_", " ").title()
                
                # Sync IT
                print("   🇮🇹 Italian...")
                it_success = self.notion_client.update_page(
                    title=title,
                    content=it_doc,
                    lang="it",
                    create_backup=True,
                    merge_mode=self.args.merge_mode
                )
                
                # Sync EN
                print("   🇬🇧 English...")
                en_success = self.notion_client.update_page(
                    title=title,
                    content=en_doc,
                    lang="en",
                    create_backup=True,
                    merge_mode=self.args.merge_mode
                )
                
                if it_success and en_success:
                    print("   ✅ Sync complete!")
                else:
                    print("   ⚠️  Partial sync (check logs)")
            
            # Success
            self._print_success()
            
        except KeyboardInterrupt:
            print("\n\n❌ Cancelled by user")
            sys.exit(0)
        except Exception as e:
            print(f"\n\n❌ Error: {e}")
            if self.args.debug:
                import traceback
                traceback.print_exc()
            sys.exit(1)
    
    def _print_header(self):
        """Print application header with Latin elegance."""
        print("\n" + "=" * 70)
        print("🏛️  NOTION SCRIBA")
        print("   \"Verba volant, scripta manent\"")
        print("=" * 70)
        print(f"Provider: {self.args.provider.upper()}")
        if self.args.component:
            print(f"Component: {self.args.component}")
        if self.args.template:
            print(f"Template: {self.args.template}")
        print("=" * 70 + "\n")
    
    def _initialize_llm_provider(self):
        """Initialize LLM provider from arguments and environment.
        
        Returns:
            Initialized LLM provider instance
        """
        provider_name = self.args.provider.lower()
        
        # Get API key
        api_key = self._get_api_key(provider_name)
        
        # Get model
        model = self.args.model or self._get_default_model(provider_name)
        
        # Create config
        config = LLMConfig(
            api_key=api_key,
            model=model,
            temperature=self.args.temperature,
            max_tokens=self.args.max_tokens,
            extra_params={"base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")}
            if provider_name == "ollama" else {}
        )
        
        # Create provider
        print(f"🤖 Initializing {provider_name.upper()} provider...")
        print(f"   Model: {model}")
        
        try:
            provider = LLMProviderFactory.create(provider_name, config)
            print(f"   ✅ Provider ready")
            return provider
        except Exception as e:
            print(f"   ❌ Provider initialization failed: {e}")
            sys.exit(1)
    
    def _get_api_key(self, provider: str) -> str:
        """Get API key for provider.
        
        Args:
            provider: Provider name
            
        Returns:
            API key string
        """
        # Map provider to env var
        env_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "ollama": None,  # No key needed
        }
        
        env_var = env_map.get(provider)
        
        # Ollama doesn't need API key
        if provider == "ollama":
            return ""
        
        # Try CLI argument first
        if self.args.api_key:
            return self.args.api_key
        
        # Try environment variable
        api_key = os.getenv(env_var)
        if api_key:
            return api_key
        
        # API key required but not found
        print(f"\n❌ API key required for {provider}")
        print(f"   Set {env_var} in .env or use --api-key argument")
        print(f"\n💡 Run 'scriba setup' for interactive configuration")
        sys.exit(1)
    
    def _get_default_model(self, provider: str) -> str:
        """Get default model for provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Default model name
        """
        # Try environment variable first
        env_var = f"{provider.upper()}_MODEL"
        env_model = os.getenv(env_var)
        if env_model:
            return env_model
        
        # Use factory default
        return LLMProviderFactory.get_default_model(provider)
    
    def _initialize_notion_client(self) -> Optional[NotionClient]:
        """Initialize Notion client if configured.
        
        Returns:
            NotionClient instance or None
        """
        token = os.getenv("NOTION_TOKEN")
        
        if not token:
            print("\n⚠️  Notion not configured (skipping sync)")
            print("   Run 'scriba setup' to configure")
            return None
        
        print("\n🔗 Initializing Notion client...")
        
        client = NotionClient(
            token=token,
            db_it=os.getenv("NOTION_DB_IT"),
            db_en=os.getenv("NOTION_DB_EN"),
            page_it=os.getenv("NOTION_PAGE_IT"),
            page_en=os.getenv("NOTION_PAGE_EN")
        )
        
        # Test connection
        success, message = client.test_connection()
        if not success:
            print(f"   ⚠️  Connection failed: {message}")
            print("   Continuing without Notion sync...")
            return None
        
        print(f"   ✅ Connected ({client.mode} mode)")
        return client
    
    def _get_prompt(self) -> str:
        """Get user prompt for documentation generation.
        
        Returns:
            User prompt string
        """
        if self.args.quick:
            return self.args.quick
        
        # Default prompt based on template
        template_prompts = {
            "investment-grade": f"Generate investment-grade documentation for {self.args.component or 'this project'}",
            "technical-deep-dive": f"Create detailed technical documentation for {self.args.component or 'this component'}",
            "business-value": f"Write business-focused documentation explaining the value of {self.args.component or 'this feature'}",
            "api-documentation": f"Generate comprehensive API documentation for {self.args.component or 'this API'}"
        }
        
        return template_prompts.get(
            self.args.template,
            f"Generate documentation for {self.args.component or 'this project'}"
        )
    
    def _print_success(self):
        """Print success message."""
        print("\n" + "=" * 70)
        print("🎉 SUCCESS!")
        print("=" * 70)
        print("\n✅ Documentation generated and synced successfully!")
        print("\n💡 Next steps:")
        print("   - Check your Notion workspace for the new documentation")
        print("   - Review and edit as needed")
        print("   - Run again with --merge-mode to preserve edits")
        print("\n" + "=" * 70 + "\n")


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="scriba",
        description="🏛️ Notion Scriba - AI Documentation Generator\n   \"Verba volant, scripta manent\"",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --component myapp --template technical-deep-dive
  %(prog)s --provider anthropic --model claude-3-5-sonnet-20241022
  %(prog)s --quick "Generate API docs" --component auth
  %(prog)s --provider deepseek --component backend
  %(prog)s setup  # Run interactive configuration wizard
  %(prog)s --list-providers  # Show available LLM providers
        """
    )
    
    # Component & Template
    parser.add_argument(
        "--component",
        help="Component to document (e.g., auth, api, frontend)"
    )
    
    parser.add_argument(
        "--template",
        choices=["investment-grade", "technical-deep-dive", "business-value", "api-documentation"],
        help="Documentation template to use"
    )
    
    # LLM Configuration
    llm_group = parser.add_argument_group("LLM Provider Options")
    
    llm_group.add_argument(
        "--provider",
        choices=LLMProviderFactory.list_providers(),
        default=os.getenv("LLM_PROVIDER", "openai"),
        help="LLM provider (default: from env or openai)"
    )
    
    llm_group.add_argument(
        "--model",
        help="Model name (default: provider-specific)"
    )
    
    llm_group.add_argument(
        "--api-key",
        help="API key for LLM provider (or use env var)"
    )
    
    llm_group.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="Generation temperature 0.0-1.0 (default: 0.3)"
    )
    
    llm_group.add_argument(
        "--max-tokens",
        type=int,
        default=4000,
        help="Maximum tokens to generate (default: 4000)"
    )
    
    # Workflow Options
    workflow_group = parser.add_argument_group("Workflow Options")
    
    workflow_group.add_argument(
        "--quick",
        metavar="PROMPT",
        help="Quick mode: provide prompt directly"
    )
    
    workflow_group.add_argument(
        "--no-code-analysis",
        action="store_true",
        help="Disable automatic code analysis"
    )
    
    workflow_group.add_argument(
        "--merge-mode",
        action="store_true",
        help="Preserve existing Notion content (merge with new)"
    )
    
    # Information Commands
    info_group = parser.add_argument_group("Information")
    
    info_group.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Enter interactive mode with file autocomplete"
    )
    
    info_group.add_argument(
        "--list-providers",
        action="store_true",
        help="List available LLM providers and exit"
    )
    
    info_group.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle info commands
    if args.list_providers:
        LLMProviderFactory.print_providers_info()
        sys.exit(0)
    
    # Handle interactive mode
    if args.interactive:
        project_root = os.getcwd()
        run_interactive_mode(project_root)
        sys.exit(0)
    
    # Check if setup was requested (handled separately)
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        run_setup_wizard()
        sys.exit(0)
    
    # Validate required arguments
    if not args.component and not args.quick:
        parser.error("Either --component or --quick is required")
    
    # Run CLI
    cli = NotionScribaCLI(args)
    cli.run()


if __name__ == "__main__":
    main()

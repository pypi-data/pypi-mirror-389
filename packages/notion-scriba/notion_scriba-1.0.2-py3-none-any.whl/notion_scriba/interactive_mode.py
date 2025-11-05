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
Interactive mode with intelligent file autocomplete for Notion Scriba.

Provides an omnibox-style interface where users can type prompts with
automatic file detection and TAB completion.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style

# Import Scriba components
from .llm import LLMProviderFactory, LLMConfig
from .code_analyzer import CodeAnalyzer
from .doc_generator import DocumentationGenerator
from .notion_client import NotionClient


class FileCompleter(Completer):
    """Custom completer for project files with intelligent filtering."""
    
    def __init__(self, project_root: str, file_extensions: List[str] = None):
        """Initialize file completer.
        
        Args:
            project_root: Root directory of the project
            file_extensions: List of file extensions to include (e.g., ['.py', '.js'])
        """
        self.project_root = Path(project_root)
        self.file_extensions = file_extensions or ['.py']
        self.files = self._scan_project_files()
        
    def _scan_project_files(self) -> List[Tuple[str, Path, int]]:
        """Scan project directory for relevant files.
        
        Returns:
            List of tuples: (display_name, full_path, line_count)
        """
        files = []
        
        # Directories to exclude
        exclude_dirs = {
            '__pycache__', '.git', '.venv', 'venv', 'env', 
            'node_modules', '.pytest_cache', '.mypy_cache',
            'dist', 'build', '.eggs', '*.egg-info'
        }
        
        try:
            for root, dirs, filenames in os.walk(self.project_root):
                # Remove excluded directories from search
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                
                for filename in filenames:
                    # Check file extension
                    if any(filename.endswith(ext) for ext in self.file_extensions):
                        full_path = Path(root) / filename
                        relative_path = full_path.relative_to(self.project_root)
                        
                        # Count lines
                        try:
                            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                line_count = sum(1 for _ in f)
                        except:
                            line_count = 0
                        
                        files.append((str(relative_path), full_path, line_count))
        except Exception as e:
            print(f"Warning: Error scanning project files: {e}")
        
        return sorted(files, key=lambda x: x[0])
    
    def get_completions(self, document: Document, complete_event):
        """Generate completions based on current text.
        
        Args:
            document: Current document
            complete_event: Completion event
            
        Yields:
            Completion objects
        """
        text_before_cursor = document.text_before_cursor.lower()
        
        # Extract the last word (potential file name)
        words = text_before_cursor.split()
        if not words:
            return
        
        last_word = words[-1]
        
        # Find files that match
        for display_name, full_path, line_count in self.files:
            display_name_lower = display_name.lower()
            filename_lower = full_path.name.lower()
            
            # Match against relative path or just filename
            if last_word in display_name_lower or last_word in filename_lower:
                # Calculate how much to replace
                start_position = -len(last_word)
                
                # Format completion with file info
                display_meta = f"{line_count} LOC"
                
                yield Completion(
                    text=display_name,
                    start_position=start_position,
                    display=display_name,
                    display_meta=display_meta,
                )


class InteractiveMode:
    """Interactive mode for Notion Scriba with file autocomplete."""
    
    def __init__(self, project_root: str = None):
        """Initialize interactive mode.
        
        Args:
            project_root: Root directory of the project to document
        """
        self.project_root = project_root or os.getcwd()
        self.completer = FileCompleter(self.project_root)
        self.history = []
        
        # Custom style for prompt
        self.style = Style.from_dict({
            'prompt': '#00aa00 bold',
            'filename': '#00aaaa',
            'info': '#888888',
        })
    
    def print_header(self):
        """Print interactive mode header."""
        print("\n" + "=" * 70)
        print("🏛️  NOTION SCRIBA - Interactive Mode")
        print('   "Verba volant, scripta manent"')
        print("=" * 70)
        print(f"\n📂 Project: {self.project_root}")
        print(f"📁 Files found: {len(self.completer.files)} Python files")
        print("\n💡 Tips:")
        print("   • Start typing to see file suggestions")
        print("   • Press TAB to autocomplete file names")
        print("   • Type multiple files separated by commas")
        print("   • Press Ctrl+D or type 'exit' to quit")
        print("=" * 70 + "\n")
    
    def parse_files_from_prompt(self, text: str) -> List[str]:
        """Extract file references from prompt text.
        
        Args:
            text: User prompt text
            
        Returns:
            List of file paths found in the prompt
        """
        found_files = []
        
        # Check each known file
        for display_name, full_path, _ in self.completer.files:
            # Check if file path appears in text
            if display_name in text or full_path.name in text:
                found_files.append(str(full_path))
        
        return found_files
    
    def _generate_documentation(self, files: List[str], user_prompt: str):
        """Generate documentation for selected files.
        
        Args:
            files: List of file paths to document
            user_prompt: Original user prompt
        """
        # Load environment
        load_dotenv()
        
        print("\n🔧 Initializing documentation generator...")
        
        # Step 1: Initialize LLM provider
        provider_name = os.getenv("LLM_PROVIDER", "openai")
        api_key = os.getenv(f"{provider_name.upper()}_API_KEY")
        
        if not api_key and provider_name != "ollama":
            print(f"\n❌ No API key found for {provider_name}")
            print(f"   Set {provider_name.upper()}_API_KEY in .env")
            print("   Or run: scriba-setup")
            return
        
        # Create LLM config
        config = LLMConfig(
            api_key=api_key or "",
            model=os.getenv(f"{provider_name.upper()}_MODEL") or LLMProviderFactory.get_default_model(provider_name),
            temperature=0.3,
            max_tokens=4000
        )
        
        try:
            llm_provider = LLMProviderFactory.create(provider_name, config)
            print(f"   ✅ {provider_name.upper()} provider ready")
        except Exception as e:
            print(f"   ❌ Failed to initialize LLM: {e}")
            return
        
        # Step 2: Analyze files
        print("\n🔍 Analyzing files...")
        analyzer = CodeAnalyzer()
        
        all_analysis = {}
        for file_path in files:
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Simple analysis (could be enhanced)
                analysis = {
                    'file_path': file_path,
                    'content': content,
                    'lines': len(content.splitlines()),
                    'size': len(content)
                }
                all_analysis[file_path] = analysis
                print(f"   ✅ {Path(file_path).name}")
            except Exception as e:
                print(f"   ⚠️  {Path(file_path).name}: {e}")
        
        if not all_analysis:
            print("\n❌ No files could be analyzed")
            return
        
        # Step 3: Generate documentation
        print(f"\n🤖 Generating documentation...")
        doc_generator = DocumentationGenerator(llm_provider)
        
        try:
            # Use first file name as component name
            component = Path(files[0]).stem
            
            # Generate bilingual documentation
            it_doc, en_doc = doc_generator.generate_bilingual(
                component=component,
                template_name=os.getenv("DOC_TEMPLATE", "technical-deep-dive"),
                user_prompt=user_prompt,
                code_analysis=all_analysis
            )
            
            print(f"   ✅ Documentation generated!")
            print(f"      IT: {len(it_doc)} characters")
            print(f"      EN: {len(en_doc)} characters")
            
        except Exception as e:
            print(f"   ❌ Generation failed: {e}")
            return
        
        # Step 4: Sync to Notion (if configured)
        notion_token = os.getenv("NOTION_TOKEN")
        
        if notion_token:
            print("\n📤 Syncing to Notion...")
            
            try:
                client = NotionClient(
                    token=notion_token,
                    db_it=os.getenv("NOTION_DB_IT"),
                    db_en=os.getenv("NOTION_DB_EN"),
                    page_it=os.getenv("NOTION_PAGE_IT"),
                    page_en=os.getenv("NOTION_PAGE_EN")
                )
                
                # Test connection
                success, message = client.test_connection()
                if not success:
                    print(f"   ⚠️  Connection failed: {message}")
                    print("   Skipping Notion sync...")
                else:
                    # Sync IT
                    print("   🇮🇹 Italian...")
                    client.update_page(
                        title=component.replace("_", " ").title(),
                        content=it_doc,
                        lang="it",
                        create_backup=True,
                        merge_mode=False
                    )
                    
                    # Sync EN
                    print("   🇬🇧 English...")
                    client.update_page(
                        title=component.replace("_", " ").title(),
                        content=en_doc,
                        lang="en",
                        create_backup=True,
                        merge_mode=False
                    )
                    
                    print("   ✅ Sync complete!")
            except Exception as e:
                print(f"   ⚠️  Notion sync failed: {e}")
        else:
            print("\n⚠️  Notion not configured (skipping sync)")
            print("   Run: scriba-setup to configure Notion")
        
        print("\n✅ Done!\n")
    
    def run(self):
        """Run interactive mode loop."""
        self.print_header()
        
        while True:
            try:
                # Get user input with autocomplete
                user_input = prompt(
                    HTML('<prompt>scriba&gt;</prompt> '),
                    completer=self.completer,
                    style=self.style,
                    complete_while_typing=True,
                )
                
                # Check for exit commands
                if user_input.strip().lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Exiting interactive mode...\n")
                    break
                
                # Skip empty input
                if not user_input.strip():
                    continue
                
                # Parse files from prompt
                files = self.parse_files_from_prompt(user_input)
                
                if files:
                    print(f"\n✅ Files detected: {len(files)}")
                    for i, file_path in enumerate(files, 1):
                        rel_path = Path(file_path).relative_to(self.project_root)
                        
                        # Count lines
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                line_count = sum(1 for _ in f)
                        except:
                            line_count = 0
                        
                        print(f"   {i}. {rel_path} ({line_count} LOC)")
                    
                    # Ask for confirmation
                    confirm = input("\n📝 Generate documentation for these files? [Y/n]: ")
                    
                    if confirm.lower() not in ['n', 'no']:
                        # Generate documentation
                        try:
                            self._generate_documentation(files, user_input)
                        except Exception as e:
                            print(f"\n❌ Error: {e}")
                            if os.getenv("DEBUG"):
                                import traceback
                                traceback.print_exc()
                    else:
                        print("\n❌ Cancelled\n")
                else:
                    print("\n⚠️  No files detected in your prompt.")
                    print("💡 Try mentioning file names from your project.\n")
                
                # Add to history
                self.history.append(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 Exiting interactive mode...\n")
                break
            except EOFError:
                print("\n\n👋 Exiting interactive mode...\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                if '--debug' in sys.argv:
                    import traceback
                    traceback.print_exc()


def run_interactive_mode(project_root: str = None):
    """Entry point for interactive mode.
    
    Args:
        project_root: Root directory of the project to document
    """
    mode = InteractiveMode(project_root)
    mode.run()


if __name__ == "__main__":
    # Test interactive mode
    run_interactive_mode()

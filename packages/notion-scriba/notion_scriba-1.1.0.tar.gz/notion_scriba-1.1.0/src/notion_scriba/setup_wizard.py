# Notion Scriba - AI-powered documentation generator
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
Interactive setup wizard for Notion Scriba configuration.

Guides users through:
1. Notion integration token
2. Mode selection (Page or Database)
3. ID collection and validation
4. Configuration file generation
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional

try:
    import requests
except ImportError:
    requests = None


class SetupWizard:
    """Interactive configuration wizard for Notion Scriba."""
    
    def __init__(self):
        """Initialize the setup wizard."""
        self.config: Dict[str, str] = {}
        self.notion_token: Optional[str] = None
        
    def run(self) -> bool:
        """Run the complete setup wizard.
        
        Returns:
            True if setup completed successfully, False otherwise
        """
        self._print_welcome()
        
        try:
            # Step 1: Get Notion token
            if not self._get_notion_token():
                return False
            
            # Step 2: Choose mode
            mode = self._choose_mode()
            
            # Step 3: Configure based on mode
            if mode == "page":
                self._setup_page_mode()
            else:
                self._setup_database_mode()
            
            # Step 4: Validate configuration
            if not self._validate_config():
                print("\n❌ Configuration validation failed!")
                return False
            
            # Step 5: Save configuration
            self._save_config()
            
            self._print_success()
            return True
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Setup cancelled by user.")
            return False
        except Exception as e:
            print(f"\n\n❌ Setup failed: {e}")
            return False
    
    def _print_welcome(self):
        """Print welcome message."""
        print("\n" + "=" * 70)
        print("🏛️  NOTION SCRIBA - SETUP WIZARD")
        print("=" * 70)
        print("\nWelcome to Notion Scriba configuration!")
        print("This wizard will help you set up your Notion integration.\n")
        print("You'll need:")
        print("  • Notion Integration Token")
        print("  • Page ID or Database ID\n")
    
    def _get_notion_token(self) -> bool:
        """Get and validate Notion integration token.
        
        Returns:
            True if token obtained successfully, False otherwise
        """
        print("\n📝 NOTION INTEGRATION TOKEN")
        print("-" * 70)
        print("\n🔍 How to get your token:")
        print("   1. Go to https://www.notion.so/my-integrations")
        print("   2. Click '+ New integration'")
        print("   3. Give it a name (e.g., 'Notion Scriba')")
        print("   4. Select the workspace")
        print("   5. Click 'Submit'")
        print("   6. Copy the 'Internal Integration Token'\n")
        print("   Token format: secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n")
        
        while True:
            token = input("👉 Enter your Notion token: ").strip()
            
            if not token:
                print("   ❌ Token cannot be empty!")
                continue
            
            if not token.startswith("secret_") and not token.startswith("ntn_"):
                print("   ⚠️  Token should start with 'secret_' or 'ntn_'")
                retry = input("   Continue anyway? [y/N]: ").strip().lower()
                if retry != 'y':
                    continue
            
            self.notion_token = token
            self.config['NOTION_TOKEN'] = token
            print("   ✅ Token saved!\n")
            return True
    
    def _choose_mode(self) -> str:
        """Let user choose between Page or Database mode.
        
        Returns:
            "page" or "database"
        """
        print("\n🎯 DOCUMENTATION MODE")
        print("-" * 70)
        print("\nChoose your documentation mode:\n")
        print("   📄 [P]age Mode - Single page for documentation")
        print("      Best for: Simple projects, single documents")
        print()
        print("   🗄️  [D]atabase Mode - Database with multiple entries")
        print("      Best for: Multiple components, structured docs\n")
        
        while True:
            choice = input("👉 Choose mode [P/d]: ").strip().lower()
            
            if choice in ('', 'p', 'page'):
                return "page"
            elif choice in ('d', 'db', 'database'):
                return "database"
            else:
                print("   ❌ Invalid choice! Enter 'p' for Page or 'd' for Database")
    
    def _setup_page_mode(self):
        """Setup configuration for Page mode (single page)."""
        print("\n�� PAGE MODE CONFIGURATION")
        print("-" * 70)
        print("\n🔍 How to find Page ID:")
        print("   1. Open the target page in Notion")
        print("   2. Click 'Share' -> 'Copy link'")
        print("   3. The ID is in the URL:")
        print("      https://notion.so/Page-Title-[THIS-IS-THE-ID]?v=...")
        print("   4. ID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx\n")
        
        # Get page ID
        print("📄 Documentation Page:")
        page_id = self._get_notion_id("page")
        self.config['NOTION_PAGE_ID'] = page_id
        
        print("\n✅ Page configuration complete!\n")
    
    def _setup_database_mode(self):
        """Setup configuration for Database mode (single database)."""
        print("\n��️  DATABASE MODE CONFIGURATION")
        print("-" * 70)
        print("\n🔍 How to find Database ID:")
        print("   1. Open the database in Notion (full-page view)")
        print("   2. Click 'Share' -> 'Copy link'")
        print("   3. The ID is in the URL:")
        print("      https://notion.so/[THIS-IS-THE-ID]?v=...")
        print("   4. ID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx\n")
        
        # Get database ID
        print("🗄️  Documentation Database:")
        db_id = self._get_notion_id("database")
        self.config['NOTION_DB'] = db_id
        
        print("\n✅ Database configuration complete!\n")
    
    def _get_notion_id(self, id_type: str) -> str:
        """Get and validate a Notion ID from user.
        
        Args:
            id_type: "page" or "database"
            
        Returns:
            Validated Notion ID
        """
        while True:
            notion_id = input(f"   Enter {id_type} ID: ").strip()
            
            if not notion_id:
                print("   ❌ ID cannot be empty!")
                continue
            
            # Clean the ID (remove dashes, extract from URL)
            cleaned_id = self._clean_notion_id(notion_id)
            
            if not self._validate_notion_id(cleaned_id):
                print("   ❌ Invalid ID format!")
                print(f"   Expected: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
                continue
            
            return cleaned_id
    
    def _clean_notion_id(self, notion_id: str) -> str:
        """Clean and extract Notion ID from various formats.
        
        Args:
            notion_id: Raw ID or URL
            
        Returns:
            Cleaned ID in canonical format
        """
        # If it's a URL, extract the ID
        if 'notion.so/' in notion_id:
            # Extract ID from URL
            match = re.search(r'([a-f0-9]{32}|[a-f0-9-]{36})', notion_id)
            if match:
                notion_id = match.group(1)
        
        # Remove all dashes
        notion_id = notion_id.replace('-', '')
        
        # Add dashes in standard format if missing
        if len(notion_id) == 32 and '-' not in notion_id:
            notion_id = f"{notion_id[:8]}-{notion_id[8:12]}-{notion_id[12:16]}-{notion_id[16:20]}-{notion_id[20:]}"
        
        return notion_id
    
    def _validate_notion_id(self, notion_id: str) -> bool:
        """Validate Notion ID format.
        
        Args:
            notion_id: ID to validate
            
        Returns:
            True if valid format, False otherwise
        """
        # Standard UUID format
        uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
        return bool(re.match(uuid_pattern, notion_id, re.IGNORECASE))
    
    def _validate_config(self) -> bool:
        """Validate configuration by testing Notion API connection.
        
        Returns:
            True if validation successful, False otherwise
        """
        print("\n🔍 VALIDATING CONFIGURATION")
        print("-" * 70)
        
        if not requests:
            print("⚠️  Requests library not available, skipping validation")
            return True
        
        headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        # Test page or database access
        if 'NOTION_PAGE_ID' in self.config:
            resource_type = "page"
            resource_id = self.config['NOTION_PAGE_ID']
        else:
            resource_type = "database"
            resource_id = self.config['NOTION_DB']
        
        print(f"\nTesting {resource_type} access...")
        
        try:
            url = f"https://api.notion.com/v1/{resource_type}s/{resource_id}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ {resource_type.capitalize()} accessible!")
                return True
            elif response.status_code == 401:
                print(f"   ❌ Authentication failed! Check your token.")
                return False
            elif response.status_code == 404:
                print(f"   ❌ {resource_type.capitalize()} not found!")
                print(f"   Make sure the integration has access to the {resource_type}.")
                return False
            else:
                print(f"   ⚠️  Unexpected response: {response.status_code}")
                print(f"   {response.text[:200]}")
                retry = input("\n   Continue anyway? [y/N]: ").strip().lower()
                return retry == 'y'
                
        except Exception as e:
            print(f"   ⚠️  Validation failed: {e}")
            retry = input("\n   Continue anyway? [y/N]: ").strip().lower()
            return retry == 'y'
    
    def _save_config(self):
        """Save configuration to .env file."""
        print("\n💾 SAVING CONFIGURATION")
        print("-" * 70)
        
        env_path = Path.cwd() / '.env'
        
        # Check if .env exists
        if env_path.exists():
            print(f"\n⚠️  .env file already exists at: {env_path}")
            choice = input("   [B]ackup and replace, [M]erge, or [C]ancel? [b/m/C]: ").strip().lower()
            
            if choice == 'c' or not choice:
                print("   ❌ Configuration not saved.")
                return
            elif choice == 'b':
                backup_path = env_path.with_suffix('.env.backup')
                env_path.rename(backup_path)
                print(f"   ✅ Backed up to: {backup_path}")
                self._write_env_file(env_path)
            elif choice == 'm':
                self._merge_env_file(env_path)
        else:
            self._write_env_file(env_path)
        
        print(f"\n✅ Configuration saved to: {env_path}\n")
    
    def _write_env_file(self, path: Path):
        """Write new .env file.
        
        Args:
            path: Path to .env file
        """
        with open(path, 'w') as f:
            f.write("# Notion Scriba Configuration\n")
            f.write("# Generated by setup wizard\n\n")
            f.write("# Notion Integration\n")
            f.write(f"NOTION_TOKEN={self.config['NOTION_TOKEN']}\n")
            
            if 'NOTION_PAGE_ID' in self.config:
                f.write(f"NOTION_PAGE_ID={self.config['NOTION_PAGE_ID']}\n")
            
            if 'NOTION_DB' in self.config:
                f.write(f"NOTION_DB={self.config['NOTION_DB']}\n")
            
            f.write("\n# LLM Provider (default: openai)\n")
            f.write("LLM_PROVIDER=openai\n")
            f.write("# OPENAI_API_KEY=sk-your-key-here\n")
    
    def _merge_env_file(self, path: Path):
        """Merge configuration with existing .env file.
        
        Args:
            path: Path to existing .env file
        """
        # Read existing content
        with open(path, 'r') as f:
            lines = f.readlines()
        
        # Update or append Notion config
        notion_keys = {'NOTION_TOKEN', 'NOTION_PAGE_ID', 'NOTION_DB'}
        updated_keys = set()
        
        with open(path, 'w') as f:
            for line in lines:
                key = line.split('=')[0].strip()
                if key in notion_keys and key in self.config:
                    f.write(f"{key}={self.config[key]}\n")
                    updated_keys.add(key)
                else:
                    f.write(line)
            
            # Append new keys
            for key in notion_keys:
                if key in self.config and key not in updated_keys:
                    f.write(f"{key}={self.config[key]}\n")
    
    def _print_success(self):
        """Print success message with next steps."""
        print("\n" + "=" * 70)
        print("🎉 SETUP COMPLETE!")
        print("=" * 70)
        print("\nYour Notion Scriba is now configured!\n")
        print("Next steps:")
        print("  1. Add your LLM API key to .env:")
        print("     OPENAI_API_KEY=sk-your-key-here")
        print()
        print("  2. Run your first documentation generation:")
        print("     scriba --component myapp --template technical-deep-dive")
        print()
        print("  3. Or use interactive mode:")
        print("     scriba -i")
        print()
        print("For help: scriba --help")
        print("\n" + "=" * 70 + "\n")


def run_setup_wizard():
    """Run the setup wizard (entry point for CLI)."""
    wizard = SetupWizard()
    success = wizard.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    run_setup_wizard()

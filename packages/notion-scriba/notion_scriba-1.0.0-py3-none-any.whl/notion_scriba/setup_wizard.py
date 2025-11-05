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


"""Interactive setup wizard for Notion Docs Synapse configuration."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Tuple
import requests


class NotionSetupWizard:
    """Interactive setup wizard for configuring Notion integration.
    
    Guides users through:
    1. Notion token configuration
    2. Choice between Pages or Database mode
    3. Collection of appropriate IDs
    4. Validation of Notion connection
    5. Saving configuration to .env file
    """
    
    def __init__(self):
        self.config: Dict[str, str] = {}
        self.env_path = Path.cwd() / ".env"
        
    def run(self):
        """Run the interactive setup wizard."""
        self._print_welcome()
        
        try:
            # Step 1: Get Notion token
            self._get_notion_token()
            
            # Step 2: Choose mode (Pages vs Database)
            mode = self._choose_mode()
            
            # Step 3: Get IDs based on mode
            if mode == "pages":
                self._setup_pages_mode()
            else:
                self._setup_database_mode()
            
            # Step 4: Validate connection
            if self._validate_notion_connection():
                # Step 5: Save configuration
                self._save_config()
                self._print_success()
            else:
                self._print_error("Connection validation failed. Please check your credentials.")
                sys.exit(1)
                
        except KeyboardInterrupt:
            print("\n\n❌ Setup cancelled by user.")
            sys.exit(0)
        except Exception as e:
            print(f"\n\n❌ Setup failed: {e}")
            sys.exit(1)
    
    def _print_welcome(self):
        """Print welcome message."""
        print("\n" + "=" * 70)
        print("🏛️  NOTION DOCS SYNAPSE - INTERACTIVE SETUP")
        print("=" * 70)
        print("\nThis wizard will help you configure Notion integration.")
        print("\n📚 You'll need:")
        print("   1. Notion Integration Token")
        print("   2. Either: Page IDs (for direct pages)")
        print("      Or:     Database ID (for organized docs)")
        print("\n💡 Tip: Keep your Notion workspace open to copy IDs easily!")
        print("=" * 70 + "\n")
    
    def _get_notion_token(self):
        """Get Notion integration token from user."""
        print("📝 STEP 1: Notion Integration Token")
        print("-" * 70)
        print("\n🔑 Where to find your token:")
        print("   1. Go to: https://www.notion.so/my-integrations")
        print("   2. Click 'New integration'")
        print("   3. Give it a name (e.g., 'Docs Generator')")
        print("   4. Copy the 'Internal Integration Token'")
        print("   5. In your Notion workspace, share the target page/database")
        print("      with your integration (Share → Invite → Select your integration)")
        print("\n⚠️  Token format: secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n")
        
        while True:
            token = input("📋 Enter your Notion Integration Token: ").strip()
            
            if not token:
                print("❌ Token cannot be empty. Please try again.\n")
                continue
            
            if not token.startswith("secret_"):
                print("⚠️  Warning: Token should start with 'secret_'")
                confirm = input("   Continue anyway? (y/n): ").strip().lower()
                if confirm != 'y':
                    continue
            
            self.config['NOTION_TOKEN'] = token
            print("✅ Token saved!\n")
            break
    
    def _choose_mode(self) -> str:
        """Let user choose between Pages or Database mode.
        
        Returns:
            "pages" or "database"
        """
        print("\n📂 STEP 2: Choose Output Mode")
        print("-" * 70)
        print("\nHow do you want to organize your documentation?")
        print("\n1️⃣  PAGES MODE (Simple)")
        print("   → Documentation saved as standalone Notion pages")
        print("   → Best for: Small projects, simple setups")
        print("   → You need: 2 Page IDs (one for IT, one for EN)")
        print("\n2️⃣  DATABASE MODE (Recommended)")
        print("   → Documentation organized in Notion database(s)")
        print("   → Best for: Multiple components, organized docs")
        print("   → You need: 1 or 2 Database IDs")
        print("   → Features: Filtering, sorting, properties, views")
        print("\n💡 Recommendation: Choose DATABASE mode for better organization\n")
        
        while True:
            choice = input("👉 Enter your choice (1 for Pages, 2 for Database): ").strip()
            
            if choice == "1":
                return "pages"
            elif choice == "2":
                return "database"
            else:
                print("❌ Invalid choice. Please enter 1 or 2.\n")
    
    def _setup_pages_mode(self):
        """Setup configuration for Pages mode."""
        print("\n📄 PAGES MODE CONFIGURATION")
        print("-" * 70)
        print("\n🔍 How to find Page IDs:")
        print("   1. Open the target page in Notion")
        print("   2. Click 'Share' → 'Copy link'")
        print("   3. The ID is in the URL:")
        print("      https://notion.so/Page-Title-[THIS-IS-THE-ID]?v=...")
        print("   4. ID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx\n")
        
        # Get Italian page ID
        print("🇮🇹 Italian Documentation Page:")
        it_page = self._get_notion_id("page", "IT")
        self.config['NOTION_PAGE_IT'] = it_page
        
        # Get English page ID
        print("\n🇬🇧 English Documentation Page:")
        en_page = self._get_notion_id("page", "EN")
        self.config['NOTION_PAGE_EN'] = en_page
        
        print("\n✅ Pages configuration complete!\n")
    
    def _setup_database_mode(self):
        """Setup configuration for Database mode."""
        print("\n🗄️  DATABASE MODE CONFIGURATION")
        print("-" * 70)
        print("\n🔍 How to find Database IDs:")
        print("   1. Open the database in Notion (full-page view)")
        print("   2. Click 'Share' → 'Copy link'")
        print("   3. The ID is in the URL:")
        print("      https://notion.so/[THIS-IS-THE-ID]?v=...")
        print("   4. ID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        print("\n💡 Setup Options:")
        print("   A. Single database (recommended for bilingual docs)")
        print("   B. Separate databases (one for IT, one for EN)\n")
        
        mode_choice = input("👉 Use single database (A) or separate (B)? [A/b]: ").strip().lower()
        
        if mode_choice == "b":
            # Separate databases
            print("\n🇮🇹 Italian Documentation Database:")
            it_db = self._get_notion_id("database", "IT")
            self.config['NOTION_DB_IT'] = it_db
            
            print("\n🇬🇧 English Documentation Database:")
            en_db = self._get_notion_id("database", "EN")
            self.config['NOTION_DB_EN'] = en_db
        else:
            # Single database
            print("\n🌍 Multilingual Documentation Database:")
            db_id = self._get_notion_id("database", "multilingual")
            self.config['NOTION_DB_IT'] = db_id
            self.config['NOTION_DB_EN'] = db_id
            print("   ℹ️  Using same database for both languages")
        
        print("\n✅ Database configuration complete!\n")
    
    def _get_notion_id(self, id_type: str, language: str) -> str:
        """Get and validate a Notion ID from user.
        
        Args:
            id_type: "page" or "database"
            language: Language label (IT, EN, multilingual)
            
        Returns:
            Validated Notion ID
        """
        while True:
            notion_id = input(f"📋 Enter {language} {id_type} ID: ").strip()
            
            if not notion_id:
                print("❌ ID cannot be empty. Please try again.\n")
                continue
            
            # Clean ID (remove dashes if present)
            notion_id = notion_id.replace("-", "")
            
            # Validate format (32 hex characters)
            if len(notion_id) != 32:
                print(f"⚠️  Warning: ID should be 32 characters (got {len(notion_id)})")
                confirm = input("   Continue anyway? (y/n): ").strip().lower()
                if confirm != 'y':
                    continue
            
            # Re-add dashes in standard format
            formatted_id = f"{notion_id[:8]}-{notion_id[8:12]}-{notion_id[12:16]}-{notion_id[16:20]}-{notion_id[20:]}"
            print(f"   ✅ Formatted ID: {formatted_id}")
            return formatted_id
    
    def _validate_notion_connection(self) -> bool:
        """Validate Notion connection with provided credentials.
        
        Returns:
            True if connection successful, False otherwise
        """
        print("\n🔍 STEP 3: Validating Connection")
        print("-" * 70)
        print("\nTesting Notion API connection...")
        
        token = self.config.get('NOTION_TOKEN')
        if not token:
            return False
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        # Test token validity by listing users
        try:
            response = requests.get(
                "https://api.notion.com/v1/users/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Token is valid!")
                user_data = response.json()
                bot_name = user_data.get('name', 'Unknown')
                print(f"   Connected as: {bot_name}")
                return True
            elif response.status_code == 401:
                print("❌ Invalid token. Please check your integration token.")
                return False
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
                print(f"   Message: {response.text}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def _save_config(self):
        """Save configuration to .env file."""
        print("\n💾 STEP 4: Saving Configuration")
        print("-" * 70)
        
        # Check if .env exists
        if self.env_path.exists():
            print(f"\n⚠️  File {self.env_path} already exists.")
            action = input("   (O)verwrite, (M)erge, or (C)ancel? [M/o/c]: ").strip().lower()
            
            if action == 'c':
                print("❌ Configuration not saved.")
                sys.exit(0)
            elif action == 'o':
                self._write_new_env()
            else:  # Merge
                self._merge_env()
        else:
            self._write_new_env()
        
        print(f"\n✅ Configuration saved to: {self.env_path}")
    
    def _write_new_env(self):
        """Write new .env file."""
        with open(self.env_path, 'w') as f:
            f.write("# Notion Docs Synapse Configuration\n")
            f.write("# Generated by setup wizard\n\n")
            
            f.write("# Notion Integration\n")
            f.write(f"NOTION_TOKEN={self.config['NOTION_TOKEN']}\n")
            
            if 'NOTION_PAGE_IT' in self.config:
                f.write(f"NOTION_PAGE_IT={self.config['NOTION_PAGE_IT']}\n")
                f.write(f"NOTION_PAGE_EN={self.config['NOTION_PAGE_EN']}\n")
            
            if 'NOTION_DB_IT' in self.config:
                f.write(f"NOTION_DB_IT={self.config['NOTION_DB_IT']}\n")
                f.write(f"NOTION_DB_EN={self.config['NOTION_DB_EN']}\n")
            
            f.write("\n# LLM Provider (choose one)\n")
            f.write("LLM_PROVIDER=openai\n")
            f.write("# OPENAI_API_KEY=your-key-here\n")
            f.write("# ANTHROPIC_API_KEY=your-key-here\n")
            f.write("# GOOGLE_API_KEY=your-key-here\n")
    
    def _merge_env(self):
        """Merge new config with existing .env file."""
        # Read existing content
        existing_lines = []
        existing_keys = set()
        
        with open(self.env_path, 'r') as f:
            for line in f:
                existing_lines.append(line)
                if '=' in line and not line.strip().startswith('#'):
                    key = line.split('=')[0].strip()
                    existing_keys.add(key)
        
        # Write merged content
        with open(self.env_path, 'w') as f:
            # Write existing lines, replacing Notion keys
            for line in existing_lines:
                if '=' in line and not line.strip().startswith('#'):
                    key = line.split('=')[0].strip()
                    if key in self.config:
                        f.write(f"{key}={self.config[key]}\n")
                        continue
                f.write(line)
            
            # Add new Notion keys if they don't exist
            f.write("\n# Notion Configuration (updated by setup wizard)\n")
            for key, value in self.config.items():
                if key not in existing_keys:
                    f.write(f"{key}={value}\n")
    
    def _print_success(self):
        """Print success message with next steps."""
        print("\n" + "=" * 70)
        print("🎉 SETUP COMPLETE!")
        print("=" * 70)
        print("\n✅ Notion integration configured successfully!")
        print(f"\n📄 Configuration saved to: {self.env_path}")
        print("\n🚀 Next steps:")
        print("   1. Set up your LLM provider (OpenAI, Claude, Gemini, etc.)")
        print("      → Add API key to .env file")
        print("   2. Run your first documentation generation:")
        print("      → notion-docs --component myproject --template technical-deep-dive")
        print("\n📚 Documentation: README.md")
        print("💡 List providers: notion-docs --list-providers")
        print("\n" + "=" * 70 + "\n")
    
    def _print_error(self, message: str):
        """Print error message."""
        print("\n" + "=" * 70)
        print("❌ SETUP FAILED")
        print("=" * 70)
        print(f"\n{message}")
        print("\n💡 Need help?")
        print("   → Check documentation: docs/notion_setup.md")
        print("   → Verify Notion integration: https://www.notion.so/my-integrations")
        print("   → Ensure integration has access to your pages/databases")
        print("\n" + "=" * 70 + "\n")


def run_setup_wizard():
    """Entry point for setup wizard."""
    wizard = NotionSetupWizard()
    wizard.run()


if __name__ == "__main__":
    run_setup_wizard()

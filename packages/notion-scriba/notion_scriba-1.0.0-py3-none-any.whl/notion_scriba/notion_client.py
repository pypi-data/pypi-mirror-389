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


"""Notion API client with support for both Pages and Database modes."""

import os
from typing import Optional, Dict, List, Any
from datetime import datetime
import requests


class NotionClient:
    """Client for interacting with Notion API.
    
    Supports two modes:
    1. Pages Mode: Direct updates to standalone Notion pages
    2. Database Mode: Organized documentation in Notion databases
    
    Features:
    - Automatic page/database detection
    - Safe updates with backup
    - Merge mode for preserving existing content
    - Bilingual support (IT/EN)
    """
    
    def __init__(
        self,
        token: str,
        db_it: Optional[str] = None,
        db_en: Optional[str] = None,
        page_it: Optional[str] = None,
        page_en: Optional[str] = None
    ):
        """Initialize Notion client.
        
        Args:
            token: Notion integration token
            db_it: Italian database ID (for database mode)
            db_en: English database ID (for database mode)
            page_it: Italian page ID (for pages mode)
            page_en: English page ID (for pages mode)
        """
        self.token = token
        self.db_it = db_it or os.getenv('NOTION_DB_IT')
        self.db_en = db_en or os.getenv('NOTION_DB_EN')
        self.page_it = page_it or os.getenv('NOTION_PAGE_IT')
        self.page_en = page_en or os.getenv('NOTION_PAGE_EN')
        
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        # Determine mode
        self.mode = self._detect_mode()
    
    def _detect_mode(self) -> str:
        """Detect whether client is in pages or database mode.
        
        Returns:
            "pages" or "database"
        """
        if self.page_it or self.page_en:
            return "pages"
        elif self.db_it or self.db_en:
            return "database"
        else:
            return "unknown"
    
    def test_connection(self) -> tuple[bool, str]:
        """Test Notion API connection.
        
        Returns:
            Tuple of (success, message)
        """
        if not self.token:
            return False, "Token missing"
        
        try:
            print("[Notion] 🔗 Testing connection...")
            print(f"[Notion] 🔑 Token: {self.token[:10]}...")
            
            response = requests.get(
                f"{self.base_url}/users/me",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                bot_name = user_data.get('name', 'Unknown user')
                print(f"[Notion] ✅ Connected as: {bot_name}")
                return True, f"Connected as {bot_name}"
            else:
                error_msg = f"API error: {response.status_code}"
                print(f"[Notion] ❌ {error_msg}: {response.text}")
                return False, error_msg
                
        except Exception as e:
            print(f"[Notion] ❌ Exception: {e}")
            return False, f"Error: {e}"
    
    def update_page(
        self,
        title: str,
        content: str,
        lang: str = "en",
        create_backup: bool = True,
        merge_mode: bool = False
    ) -> bool:
        """Update or create page in Notion.
        
        Args:
            title: Page title
            content: Markdown content to write
            lang: Language ("en" or "it")
            create_backup: Whether to create backup before overwriting
            merge_mode: Whether to preserve existing content
            
        Returns:
            True if successful, False otherwise
        """
        print(f"\n[Notion] 📝 Updating page: {title} ({lang})")
        print(f"[Notion] 🔑 Token configured: {'✅' if self.token else '❌'}")
        print(f"[Notion] 📄 Content length: {len(content)} characters")
        print(f"[Notion] 📦 Backup: {'✅ Active' if create_backup else '❌ Disabled'}")
        print(f"[Notion] 🔀 Merge mode: {'✅ Active' if merge_mode else '❌ Disabled'}")
        
        try:
            if self.mode == "database":
                return self._update_database_mode(
                    title, content, lang, create_backup, merge_mode
                )
            elif self.mode == "pages":
                return self._update_pages_mode(
                    title, content, lang, create_backup, merge_mode
                )
            else:
                print("[Notion] ❌ No database or page IDs configured")
                return False
                
        except Exception as e:
            print(f"[Notion] ❌ Update error: {e}")
            return False
    
    def _update_database_mode(
        self,
        title: str,
        content: str,
        lang: str,
        create_backup: bool,
        merge_mode: bool
    ) -> bool:
        """Update in database mode."""
        # Select appropriate database
        database_id = self.db_it if lang == "it" else self.db_en
        
        if not database_id:
            print(f"[Notion] ❌ Database ID missing for language: {lang}")
            return False
        
        # Check if page exists
        existing_page = self._find_page_by_title(database_id, title)
        
        if existing_page:
            page_id = existing_page['id']
            print(f"[Notion] 🔄 Updating existing page: {page_id}")
            
            # Handle backup and merge if needed
            if create_backup or merge_mode:
                existing_content = self._get_page_content(page_id)
                
                if create_backup and existing_content.strip():
                    self._create_backup_page(database_id, title, existing_content, lang)
                
                if merge_mode and existing_content.strip():
                    if "Auto-generated" not in existing_content:
                        print("[Notion] 🔀 MERGE: Preserving existing content")
                        content = self._merge_content(title, existing_content, content)
            
            return self._update_page_content(page_id, content, title)
        else:
            print(f"[Notion] 🆕 Creating new page: {title}")
            return self._create_new_page(database_id, title, content, lang)
    
    def _update_pages_mode(
        self,
        title: str,
        content: str,
        lang: str,
        create_backup: bool,
        merge_mode: bool
    ) -> bool:
        """Update in pages mode."""
        # Select appropriate page
        page_id = self.page_it if lang == "it" else self.page_en
        
        if not page_id:
            print(f"[Notion] ❌ Page ID missing for language: {lang}")
            return False
        
        print(f"[Notion] 📄 Updating page: {page_id}")
        
        # Handle backup and merge if needed
        if create_backup or merge_mode:
            existing_content = self._get_page_content(page_id)
            
            if merge_mode and existing_content.strip():
                print("[Notion] 🔀 MERGE: Preserving existing content")
                content = self._merge_content(title, existing_content, content)
        
        return self._update_page_content(page_id, content, title)
    
    def _find_page_by_title(self, database_id: str, title: str) -> Optional[Dict]:
        """Find page by title in database.
        
        Args:
            database_id: Database ID to search
            title: Page title to find
            
        Returns:
            Page object if found, None otherwise
        """
        try:
            payload = {
                "filter": {
                    "property": "title",
                    "title": {
                        "equals": title
                    }
                }
            }
            
            response = requests.post(
                f"{self.base_url}/databases/{database_id}/query",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json().get('results', [])
                return results[0] if results else None
            else:
                print(f"[Notion] ⚠️ Search error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"[Notion] ❌ Search exception: {e}")
            return None
    
    def _get_page_content(self, page_id: str) -> str:
        """Get existing page content.
        
        Args:
            page_id: Page ID to read
            
        Returns:
            Markdown content of the page
        """
        try:
            response = requests.get(
                f"{self.base_url}/blocks/{page_id}/children",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                blocks = response.json().get('results', [])
                return self._extract_text_from_blocks(blocks)
            else:
                return ""
                
        except Exception:
            return ""
    
    def _extract_text_from_blocks(self, blocks: List[Dict]) -> str:
        """Extract text content from Notion blocks.
        
        Args:
            blocks: List of Notion block objects
            
        Returns:
            Extracted markdown text
        """
        content = ""
        
        for block in blocks:
            block_type = block.get('type')
            
            if block_type == 'paragraph':
                text = self._extract_rich_text(
                    block.get('paragraph', {}).get('rich_text', [])
                )
                content += text + "\n\n"
            elif block_type == 'heading_1':
                text = self._extract_rich_text(
                    block.get('heading_1', {}).get('rich_text', [])
                )
                content += f"# {text}\n\n"
            elif block_type == 'heading_2':
                text = self._extract_rich_text(
                    block.get('heading_2', {}).get('rich_text', [])
                )
                content += f"## {text}\n\n"
            elif block_type == 'heading_3':
                text = self._extract_rich_text(
                    block.get('heading_3', {}).get('rich_text', [])
                )
                content += f"### {text}\n\n"
        
        return content.strip()
    
    def _extract_rich_text(self, rich_text_array: List[Dict]) -> str:
        """Extract plain text from Notion rich text array.
        
        Args:
            rich_text_array: Notion rich text array
            
        Returns:
            Plain text string
        """
        text = ""
        for item in rich_text_array:
            text += item.get('text', {}).get('content', '')
        return text
    
    def _merge_content(
        self,
        title: str,
        existing: str,
        new: str
    ) -> str:
        """Merge existing and new content.
        
        Args:
            title: Page title
            existing: Existing content
            new: New content to add
            
        Returns:
            Merged content
        """
        return f"""# {title}

## 📋 Original Documentation
{existing}

---

## 🤖 Auto-Generated Documentation
{new}

---
*Last auto-update: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    
    def _create_backup_page(
        self,
        database_id: str,
        original_title: str,
        content: str,
        lang: str
    ) -> bool:
        """Create backup page in database.
        
        Args:
            database_id: Database ID
            original_title: Original page title
            content: Content to backup
            lang: Language
            
        Returns:
            True if successful
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_title = f"[BACKUP] {original_title} - {timestamp}"
            
            print(f"[Notion] 💾 Creating backup: {backup_title}")
            
            return self._create_new_page(
                database_id,
                backup_title,
                content,
                lang
            )
            
        except Exception as e:
            print(f"[Notion] ⚠️ Backup failed: {e}")
            return False
    
    def _create_new_page(
        self,
        database_id: str,
        title: str,
        content: str,
        lang: str
    ) -> bool:
        """Create new page in database.
        
        Args:
            database_id: Database ID
            title: Page title
            content: Page content
            lang: Language
            
        Returns:
            True if successful
        """
        try:
            # Convert markdown to Notion blocks
            blocks = self._markdown_to_blocks(content)
            
            payload = {
                "parent": {"database_id": database_id},
                "properties": {
                    "title": {
                        "title": [{"text": {"content": title}}]
                    }
                },
                "children": blocks
            }
            
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                page_id = response.json()['id']
                print(f"[Notion] ✅ Page created: {page_id}")
                return True
            else:
                print(f"[Notion] ❌ Create failed: {response.status_code}")
                print(f"[Notion] Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"[Notion] ❌ Create exception: {e}")
            return False
    
    def _update_page_content(
        self,
        page_id: str,
        content: str,
        title: str
    ) -> bool:
        """Update existing page content.
        
        Args:
            page_id: Page ID to update
            content: New content
            title: Page title
            
        Returns:
            True if successful
        """
        try:
            # First, delete existing blocks
            self._delete_page_children(page_id)
            
            # Then append new blocks
            blocks = self._markdown_to_blocks(content)
            
            payload = {"children": blocks}
            
            response = requests.patch(
                f"{self.base_url}/blocks/{page_id}/children",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                print(f"[Notion] ✅ Content updated")
                return True
            else:
                print(f"[Notion] ❌ Update failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[Notion] ❌ Update exception: {e}")
            return False
    
    def _delete_page_children(self, page_id: str):
        """Delete all child blocks of a page.
        
        Args:
            page_id: Page ID
        """
        try:
            response = requests.get(
                f"{self.base_url}/blocks/{page_id}/children",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                blocks = response.json().get('results', [])
                for block in blocks:
                    requests.delete(
                        f"{self.base_url}/blocks/{block['id']}",
                        headers=self.headers,
                        timeout=10
                    )
        except Exception as e:
            print(f"[Notion] ⚠️ Delete children error: {e}")
    
    def _markdown_to_blocks(self, markdown: str) -> List[Dict]:
        """Convert markdown to Notion blocks.
        
        Simple conversion supporting:
        - Paragraphs
        - Headings (# ## ###)
        - Code blocks
        
        Args:
            markdown: Markdown text
            
        Returns:
            List of Notion block objects
        """
        blocks = []
        lines = markdown.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Heading 1
            if line.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"text": {"content": line[2:].strip()}}]
                    }
                })
            # Heading 2
            elif line.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": line[3:].strip()}}]
                    }
                })
            # Heading 3
            elif line.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"text": {"content": line[4:].strip()}}]
                    }
                })
            # Code block
            elif line.startswith('```'):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                
                blocks.append({
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"text": {"content": '\n'.join(code_lines)}}],
                        "language": "python"
                    }
                })
            # Paragraph
            else:
                # Truncate if too long (Notion limit: 2000 chars per text block)
                text = line[:2000]
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": text}}]
                    }
                })
            
            i += 1
        
        return blocks[:100]  # Notion limit: 100 blocks per request

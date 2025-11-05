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
Code Analyzer
-------------
Standalone module for intelligent source code analysis.

Features:
- Recursive directory scanning
- Class, function, and import extraction
- API endpoint identification
- Code statistics and metrics
- Structured summary for LLM context
"""

import os
from typing import Dict, List, Set, Any
from pathlib import Path


class CodeAnalyzer:
    """
    Intelligent source code analyzer for documentation generation.
    
    Supports:
    - Python files (.py)
    - Configuration files (YAML, JSON)
    - Metadata extraction (classes, functions, imports, APIs)
    - Summary generation for LLM context
    """
    
    def __init__(self, max_files: int = 10, max_code_length: int = 8000):
        """
        Initialize analyzer with limits to avoid context overflow.
        
        Args:
            max_files: Maximum number of files to analyze
            max_code_length: Maximum code length in summary (chars)
        """
        self.max_files = max_files
        self.max_code_length = max_code_length
    
    def analyze_directory(self, path: str, recursive: bool = True) -> Dict[str, Any]:
        """
        Analyze a directory and return complete data structure.
        
        Args:
            path: Directory path to analyze
            recursive: If True, analyze subdirectories
        
        Returns:
            Dict with complete analysis:
            {
                "files_analyzed": int,
                "total_lines": int,
                "classes": List[str],
                "functions": List[str],
                "imports": Set[str],
                "apis": List[str],
                "configurations": List[str],
                "summary": str,
                "full_code": str
            }
        """
        print(f"[CodeAnalyzer] 🔍 Analyzing code in: {path}")
        
        if not os.path.exists(path):
            return self._empty_analysis(f"Path not found: {path}")
        
        # Collect files to analyze
        python_files = self._collect_files(path, recursive)
        
        if not python_files:
            return self._empty_analysis(f"No Python files found in {path}")
        
        # Intelligent analysis
        analysis = self._analyze_files(python_files)
        
        # Generate summary
        analysis["summary"] = self._generate_summary(analysis)
        
        print(f"[CodeAnalyzer] ✅ Analysis complete: {analysis['files_analyzed']} files, {analysis['total_lines']} LOC")
        
        return analysis
    
    def analyze_component(self, component_name: str, project_root: str = None) -> Dict[str, Any]:
        """
        Analyze a specific component by name.
        
        Args:
            component_name: Component name (e.g., "api", "core", "services")
            project_root: Project root directory (default: auto-detect)
        
        Returns:
            Dict with component analysis
        """
        if not project_root:
            project_root = self._detect_project_root()
        
        # Try common patterns for component location
        possible_paths = [
            os.path.join(project_root, component_name),
            os.path.join(project_root, "src", component_name),
            os.path.join(project_root, "lib", component_name),
            os.path.join(project_root, component_name.replace("_", "-")),
            os.path.join(project_root, "packages", component_name),
        ]
        
        component_path = None
        for path in possible_paths:
            if os.path.exists(path):
                component_path = path
                break
        
        if not component_path:
            print(f"[CodeAnalyzer] ⚠️ Component not found: {component_name}")
            print(f"[CodeAnalyzer] Searched in: {', '.join(possible_paths)}")
            return self._empty_analysis(f"Component not found: {component_name}")
        
        return self.analyze_directory(component_path)
    
    def extract_classes(self, code: str) -> List[str]:
        """Extract class definitions from code."""
        classes = []
        for line in code.split('\n'):
            stripped = line.strip()
            if stripped.startswith('class '):
                classes.append(stripped)
        return classes
    
    def extract_functions(self, code: str) -> List[str]:
        """Extract function definitions from code."""
        functions = []
        for line in code.split('\n'):
            stripped = line.strip()
            if stripped.startswith('def '):
                functions.append(stripped)
        return functions
    
    def extract_imports(self, code: str) -> Set[str]:
        """Extract import statements from code."""
        imports = set()
        for line in code.split('\n'):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                imports.add(stripped)
        return imports
    
    def extract_apis(self, code: str) -> List[str]:
        """Identify possible API endpoints in code."""
        apis = []
        api_keywords = [
            '@app.', '@router.', '@api', 'api', 'endpoint', 
            '@get', '@post', '@put', '@delete', '@patch',
            'route(', 'api_route', 'add_route'
        ]
        
        for line in code.split('\n'):
            stripped = line.strip().lower()
            if any(keyword in stripped for keyword in api_keywords):
                apis.append(line.strip())
        
        return apis
    
    def _collect_files(self, path: str, recursive: bool) -> List[str]:
        """Collect Python/YAML/JSON files to analyze."""
        files = []
        extensions = ('.py', '.yaml', '.yml', '.json')
        
        if os.path.isfile(path):
            if path.endswith(extensions):
                return [path]
            return []
        
        if recursive:
            for root, dirs, filenames in os.walk(path):
                # Skip common ignored directories
                dirs[:] = [d for d in dirs if d not in [
                    '__pycache__', '.git', 'node_modules', 'venv', '.venv',
                    'env', '.env', 'build', 'dist', '.pytest_cache', '.mypy_cache'
                ]]
                
                for filename in filenames:
                    if filename.endswith(extensions):
                        files.append(os.path.join(root, filename))
                        
                        # Limit number of files
                        if len(files) >= self.max_files:
                            print(f"[CodeAnalyzer] ⚠️ Limit of {self.max_files} files reached")
                            return files
        else:
            for filename in os.listdir(path):
                filepath = os.path.join(path, filename)
                if os.path.isfile(filepath) and filename.endswith(extensions):
                    files.append(filepath)
        
        return files[:self.max_files]
    
    def _analyze_files(self, files: List[str]) -> Dict[str, Any]:
        """Analyze list of files and return aggregated data."""
        analysis = {
            "files_analyzed": len(files),
            "total_lines": 0,
            "classes": [],
            "functions": [],
            "imports": set(),
            "apis": [],
            "configurations": [],
            "full_code": ""
        }
        
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    filename = os.path.basename(file_path)
                    
                    # Add to full_code with separator
                    analysis["full_code"] += f"\n\n{'='*60}\n"
                    analysis["full_code"] += f"FILE: {filename}\n"
                    analysis["full_code"] += f"{'='*60}\n{content}"
                    
                    # Count lines
                    lines = content.split('\n')
                    analysis["total_lines"] += len(lines)
                    
                    # Extract metadata for Python files
                    if file_path.endswith('.py'):
                        analysis["classes"].extend(self.extract_classes(content))
                        analysis["functions"].extend(self.extract_functions(content))
                        analysis["imports"].update(self.extract_imports(content))
                        analysis["apis"].extend(self.extract_apis(content))
                    
                    # Configuration files
                    if file_path.endswith(('.yaml', '.yml', '.json')):
                        analysis["configurations"].append(filename)
                    
            except Exception as e:
                print(f"[CodeAnalyzer] ⚠️ Error reading {file_path}: {e}")
        
        # Limit full_code length for LLM context
        if len(analysis["full_code"]) > self.max_code_length:
            analysis["full_code"] = analysis["full_code"][:self.max_code_length]
            analysis["full_code"] += f"\n\n... (truncated to {self.max_code_length} characters)"
        
        return analysis
    
    def _generate_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate textual summary of analysis for LLM context."""
        summary = f"""
CODE ANALYSIS COMPLETED:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Metrics:
   - Files analyzed: {analysis['files_analyzed']}
   - Total lines: {analysis['total_lines']:,}
   - Classes found: {len(analysis['classes'])}
   - Functions found: {len(analysis['functions'])}
   - Unique imports: {len(analysis['imports'])}
   - API endpoints: {len(analysis['apis'])}
   - Configuration files: {len(analysis['configurations'])}

📦 MAIN CLASSES ({len(analysis['classes'])} total):
{chr(10).join('   • ' + c for c in analysis['classes'][:10])}
{'   ... (' + str(len(analysis['classes']) - 10) + ' more classes)' if len(analysis['classes']) > 10 else ''}

🔧 KEY FUNCTIONS ({len(analysis['functions'])} total):
{chr(10).join('   • ' + f for f in analysis['functions'][:15])}
{'   ... (' + str(len(analysis['functions']) - 15) + ' more functions)' if len(analysis['functions']) > 15 else ''}

📚 MAIN DEPENDENCIES ({len(analysis['imports'])} total):
{chr(10).join('   • ' + i for i in sorted(list(analysis['imports']))[:12])}
{'   ... (' + str(len(analysis['imports']) - 12) + ' more imports)' if len(analysis['imports']) > 12 else ''}

🌐 API ENDPOINTS ({len(analysis['apis'])} found):
{chr(10).join('   • ' + a for a in analysis['apis'][:8])}
{'   ... (' + str(len(analysis['apis']) - 8) + ' more endpoints)' if len(analysis['apis']) > 8 else ''}

⚙️ CONFIGURATION FILES:
{chr(10).join('   • ' + c for c in analysis['configurations'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 COMPLETE SOURCE CODE:
{analysis['full_code']}
        """
        return summary.strip()
    
    def _empty_analysis(self, reason: str) -> Dict[str, Any]:
        """Return empty analysis with message."""
        return {
            "files_analyzed": 0,
            "total_lines": 0,
            "classes": [],
            "functions": [],
            "imports": set(),
            "apis": [],
            "configurations": [],
            "full_code": "",
            "summary": f"(Analysis not available: {reason})"
        }
    
    def _detect_project_root(self) -> str:
        """Auto-detect project root."""
        # Start from current working directory
        current = os.getcwd()
        
        # Walk up until finding .git or marker files
        while current != '/':
            # Check for version control
            if os.path.exists(os.path.join(current, '.git')):
                return current
            
            # Check for common project markers
            markers = ['pyproject.toml', 'setup.py', 'package.json', 'go.mod', 'Cargo.toml']
            if any(os.path.exists(os.path.join(current, marker)) for marker in markers):
                return current
            
            current = os.path.dirname(current)
        
        # Fallback to cwd
        return os.getcwd()


# ============================================================================
# CLI Interface for standalone testing
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("🔍 CODE ANALYZER")
    print("=" * 60)
    
    analyzer = CodeAnalyzer(max_files=15, max_code_length=10000)
    
    if len(sys.argv) > 1:
        # Analyze specific component or path
        target = sys.argv[1]
        
        if os.path.exists(target):
            # Analyze path
            result = analyzer.analyze_directory(target)
        else:
            # Try as component name
            result = analyzer.analyze_component(target)
        
        # Print summary
        print("\n" + result["summary"])
        
        # Save to file if requested
        if len(sys.argv) > 2 and sys.argv[2] == "--save":
            output_file = f"code_analysis_{target.replace('/', '_')}.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(result["summary"])
            print(f"\n💾 Analysis saved to: {output_file}")
    else:
        print("\nUsage:")
        print("  python code_analyzer.py <component_name>")
        print("  python code_analyzer.py <path>")
        print("  python code_analyzer.py <target> --save")
        print("\nExamples:")
        print("  python code_analyzer.py api")
        print("  python code_analyzer.py src/core")
        print("  python code_analyzer.py services --save")

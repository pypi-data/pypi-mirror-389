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
Documentation Templates
-----------------------
Enterprise-grade documentation templates for different audiences.

Templates:
- Investment Grade: For investors, C-level executives
- Technical Deep Dive: For developers, architects
- Business Value: For product managers, stakeholders
- API Documentation: For integration engineers
"""

from typing import Optional


class DocumentationTemplates:
    """
    Collection of professional documentation templates.
    
    Each template is optimized for:
    - Specific target audience
    - Appropriate technical depth
    - Token limits (3500-4000)
    - Temperature tuning (0.2-0.4)
    """
    
    @staticmethod
    def investment_grade(context: str, component: str) -> str:
        """
        Investment-grade documentation template.
        
        Target Audience: Investors, C-level executives, board members
        Focus: Business impact, ROI, competitive advantages
        Temperature: 0.2 (factual, precise)
        Max Tokens: 4000
        
        Args:
            context: Technical context about the component
            component: Component name
            
        Returns:
            Prompt for LLM generation
        """
        return f"""Generate investment-grade documentation for the {component} component.

TARGET AUDIENCE: Investors, C-level executives, board members
TONE: Professional, strategic, business-focused

CONTEXT:
{context}

REQUIRED SECTIONS:

# {component.title()} - Investment Overview

## Executive Summary
- What this component does (in business terms)
- Strategic importance to the platform
- Key differentiators from competitors

## Business Impact
- Revenue impact (direct or indirect)
- Cost savings and operational efficiency
- Market positioning advantages
- Scalability and growth potential

## Technical Moat
- Proprietary algorithms or methodologies
- Technological advantages
- Barriers to entry for competitors
- Intellectual property considerations

## Risk Assessment
- Technical risks and mitigation strategies
- Dependency risks
- Scalability concerns
- Security and compliance considerations

## Future Roadmap
- Planned enhancements
- Strategic integrations
- Long-term vision
- Investment required for growth

Use concrete metrics, business terminology, and strategic language.
Avoid deep technical jargon unless explaining competitive advantages.
"""
    
    @staticmethod
    def technical_deep_dive(context: str, component: str) -> str:
        """
        Technical deep-dive documentation template.
        
        Target Audience: Senior developers, architects, technical leads
        Focus: Architecture, implementation, performance
        Temperature: 0.3 (technical, detailed)
        Max Tokens: 4000
        
        Args:
            context: Technical context about the component
            component: Component name
            
        Returns:
            Prompt for LLM generation
        """
        return f"""Generate technical deep-dive documentation for the {component} component.

TARGET AUDIENCE: Senior developers, architects, technical leads
TONE: Technical, detailed, implementation-focused

CONTEXT:
{context}

REQUIRED SECTIONS:

# {component.title()} - Technical Documentation

## Architecture Overview
- High-level architecture diagram (describe in text)
- Component responsibilities and boundaries
- Integration points with other systems
- Data flow diagrams

## Implementation Details
- Core classes and their responsibilities
- Key algorithms and data structures
- Design patterns used
- Code organization and structure

## API Reference
- Public interfaces and methods
- Input/output specifications
- Error handling and edge cases
- Usage examples with code snippets

## Performance Characteristics
- Time complexity of key operations
- Memory usage patterns
- Throughput and latency metrics
- Scalability considerations

## Technical Decisions
- Why this architecture was chosen
- Trade-offs and alternatives considered
- Known limitations and workarounds
- Future technical improvements

## Development Guide
- Setup and local development
- Testing strategies
- Debugging tips
- Common pitfalls to avoid

Include code examples, architectural diagrams (in text), and technical metrics.
Use precise technical terminology and explain complex concepts clearly.
"""
    
    @staticmethod
    def business_value(context: str, component: str) -> str:
        """
        Business value documentation template.
        
        Target Audience: Product managers, business analysts, stakeholders
        Focus: Use cases, benefits, success metrics
        Temperature: 0.3 (balanced, practical)
        Max Tokens: 3500
        
        Args:
            context: Technical context about the component
            component: Component name
            
        Returns:
            Prompt for LLM generation
        """
        return f"""Generate business value documentation for the {component} component.

TARGET AUDIENCE: Product managers, business analysts, stakeholders
TONE: Clear, practical, user-benefit focused

CONTEXT:
{context}

REQUIRED SECTIONS:

# {component.title()} - Business Value Guide

## What It Does
- Simple explanation (avoid technical jargon)
- Core functionality in user terms
- Problem it solves for end users

## Use Cases
- Primary use case scenarios
- Step-by-step workflows
- User stories and personas
- Real-world applications

## Business Benefits
- Direct value to users
- Time savings and efficiency gains
- Cost reduction or revenue generation
- Quality improvements

## Success Metrics
- Key Performance Indicators (KPIs)
- Measurable outcomes
- Success criteria
- Benchmarks and targets

## User Experience
- How users interact with it
- User interface highlights
- Ease of use considerations
- Accessibility features

## Competitive Advantages
- What makes it unique
- Comparison with alternatives
- Why users should choose this
- Market positioning

Focus on user benefits and practical applications.
Use clear, jargon-free language with concrete examples.
Include metrics and measurable outcomes.
"""
    
    @staticmethod
    def api_documentation(context: str, component: str) -> str:
        """
        API documentation template.
        
        Target Audience: Integration engineers, external developers
        Focus: Endpoints, authentication, examples
        Temperature: 0.2 (precise, structured)
        Max Tokens: 4000
        
        Args:
            context: Technical context about the component
            component: Component name
            
        Returns:
            Prompt for LLM generation
        """
        return f"""Generate API documentation for the {component} component.

TARGET AUDIENCE: Integration engineers, external developers
TONE: Precise, structured, reference-style

CONTEXT:
{context}

REQUIRED SECTIONS:

# {component.title()} - API Reference

## Quick Start
- Authentication setup
- Base URL and versioning
- Required headers
- Rate limits and quotas

## Authentication
- Authentication methods (API keys, OAuth, JWT, etc.)
- How to obtain credentials
- Token management and refresh
- Security best practices

## Endpoints

For each endpoint, document:

### [METHOD] /endpoint/path
**Description:** What this endpoint does

**Authentication:** Required/Optional

**Request:**
- Parameters (path, query, body)
- Example request with headers
- Validation rules

**Response:**
- Success response (200, 201, etc.)
- Error responses (400, 401, 404, 500, etc.)
- Response schema
- Example responses

**Rate Limiting:** X requests per minute

**Code Examples:**
```python
# Python example
```

```javascript
// JavaScript example
```

```curl
# cURL example
```

## Data Models
- Schema definitions
- Data types and formats
- Required vs optional fields
- Validation rules

## Error Handling
- Error response format
- Common error codes
- Troubleshooting guide
- Support contact information

## Webhooks (if applicable)
- Event types
- Payload structure
- Retry logic
- Security verification

## SDKs and Libraries
- Available client libraries
- Installation instructions
- Code examples per language

Structure as a complete API reference guide.
Include working code examples in multiple languages.
Be precise about request/response formats and error codes.
"""
    
    @staticmethod
    def fallback_documentation(component: str, error: Optional[str] = None) -> str:
        """
        Fallback documentation when context is unavailable.
        
        Args:
            component: Component name
            error: Optional error message
            
        Returns:
            Basic documentation template
        """
        error_msg = f"\n(Note: Full context unavailable due to: {error})" if error else ""
        
        return f"""Generate comprehensive documentation for the {component} component.{error_msg}

# {component.title()} - Documentation

## Overview
Describe what the {component} component does, its purpose in the system, and its key features.

## Key Features
- List main features and capabilities
- Highlight unique or important functionality
- Explain what problems it solves

## Architecture
- High-level architecture description
- Main components and their interactions
- Integration points with other systems

## Usage
- How to use this component
- Common workflows and scenarios
- Code examples if applicable

## Configuration
- Configuration options and parameters
- Environment variables
- Default settings

## Best Practices
- Recommended usage patterns
- Performance tips
- Security considerations

## Troubleshooting
- Common issues and solutions
- Debugging strategies
- Support resources

Generate detailed, professional documentation based on general best practices for {component}-type components.
"""
    
    @staticmethod
    def get_template(template_name: str, context: str, component: str) -> str:
        """
        Get template by name.
        
        Args:
            template_name: Template identifier
            context: Technical context
            component: Component name
            
        Returns:
            Template prompt string
            
        Raises:
            ValueError: If template name is unknown
        """
        templates = {
            "investment-grade": DocumentationTemplates.investment_grade,
            "technical-deep-dive": DocumentationTemplates.technical_deep_dive,
            "business-value": DocumentationTemplates.business_value,
            "api-documentation": DocumentationTemplates.api_documentation,
        }
        
        if template_name not in templates:
            available = ", ".join(templates.keys())
            raise ValueError(
                f"Unknown template: '{template_name}'. "
                f"Available templates: {available}"
            )
        
        return templates[template_name](context, component)
    
    @staticmethod
    def list_templates() -> dict:
        """
        List all available templates with descriptions.
        
        Returns:
            Dict mapping template names to descriptions
        """
        return {
            "investment-grade": {
                "name": "Investment Grade",
                "audience": "Investors, C-level executives, board members",
                "focus": "Business impact, ROI, competitive advantages",
                "description": "Strategic documentation for business decision makers"
            },
            "technical-deep-dive": {
                "name": "Technical Deep Dive",
                "audience": "Senior developers, architects, technical leads",
                "focus": "Architecture, implementation, performance",
                "description": "Detailed technical documentation for engineers"
            },
            "business-value": {
                "name": "Business Value",
                "audience": "Product managers, business analysts, stakeholders",
                "focus": "Use cases, benefits, success metrics",
                "description": "Practical guide focused on user benefits"
            },
            "api-documentation": {
                "name": "API Documentation",
                "audience": "Integration engineers, external developers",
                "focus": "Endpoints, authentication, code examples",
                "description": "Complete API reference with examples"
            }
        }


# ============================================================================
# CLI Interface for testing templates
# ============================================================================

if __name__ == "__main__":
    print("📝 DOCUMENTATION TEMPLATES")
    print("=" * 60)
    print("\nAvailable templates:\n")
    
    for template_id, info in DocumentationTemplates.list_templates().items():
        print(f"  • {info['name']} ({template_id})")
        print(f"    Audience: {info['audience']}")
        print(f"    Focus: {info['focus']}")
        print(f"    {info['description']}\n")
    
    print("\nUsage:")
    print("  from templates import DocumentationTemplates")
    print("  prompt = DocumentationTemplates.get_template(")
    print("      'technical-deep-dive',")
    print("      context='...',")
    print("      component='my-api'")
    print("  )")

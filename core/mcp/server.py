#!/usr/bin/env python3
"""
MCP Server for Manager AI - TODO System and CRM Management
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import Counter

import yaml
import re
from difflib import SequenceMatcher
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - use environment variable or current directory
BASE_DIR = Path(os.environ.get('MANAGER_AI_BASE_DIR', Path.cwd()))
TASKS_DIR = BASE_DIR / 'Tasks'

# Ensure directories exist
TASKS_DIR.mkdir(exist_ok=True, parents=True)

# Duplicate detection configuration
DEDUP_CONFIG = {
    "similarity_threshold": 0.6,  # How similar before flagging as potential duplicate
    "check_categories": True,     # Same category increases similarity score
    "check_crm_mentions": True,   # Check for same people/companies in outreach
}

def parse_yaml_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown content"""
    if not content.startswith('---'):
        return {}, content
    
    try:
        parts = content.split('---', 2)[1:]
        if len(parts) >= 1:
            metadata = yaml.safe_load(parts[0])
            body = parts[1] if len(parts) > 1 else ''
            return metadata or {}, body
    except Exception as e:
        logger.error(f"Error parsing YAML: {e}")
        return {}, content

def get_all_tasks() -> List[Dict[str, Any]]:
    """Get all tasks from the Tasks directory"""
    tasks = []
    if not TASKS_DIR.exists():
        return tasks
    
    for task_file in TASKS_DIR.glob('*.md'):
        try:
            with open(task_file, 'r') as f:
                content = f.read()
                metadata, body = parse_yaml_frontmatter(content)
                if metadata:
                    metadata['filename'] = task_file.name
                    metadata['body_content'] = body[:500] if body else ''
                    tasks.append(metadata)
        except Exception as e:
            logger.error(f"Error reading {task_file}: {e}")
    
    return tasks

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two strings (0-1 score)"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def extract_keywords(text: str) -> set:
    """Extract meaningful keywords from text"""
    # Remove common words and extract meaningful terms
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'from', 'up', 'out'}
    words = re.findall(r'\b\w+\b', text.lower())
    return {w for w in words if w not in stop_words and len(w) > 2}

def find_similar_tasks(item: str, existing_tasks: List[Dict[str, Any]], config: dict = DEDUP_CONFIG) -> List[Dict[str, Any]]:
    """Find tasks similar to the given item"""
    similar = []
    item_keywords = extract_keywords(item)
    
    for task in existing_tasks:
        # Skip completed tasks
        if task.get('status') == 'd':
            continue
            
        # Calculate title similarity
        title = task.get('title', '')
        title_similarity = calculate_similarity(item, title)
        
        # Calculate keyword overlap
        task_keywords = extract_keywords(title)
        if item_keywords and task_keywords:
            keyword_overlap = len(item_keywords & task_keywords) / len(item_keywords | task_keywords)
        else:
            keyword_overlap = 0
        
        # Combined score
        similarity_score = (title_similarity * 0.7) + (keyword_overlap * 0.3)
        
        # Check if it's a potential duplicate
        if similarity_score >= config['similarity_threshold']:
            similar.append({
                'title': title,
                'filename': task.get('filename', ''),
                'category': task.get('category', ''),
                'status': task.get('status', ''),
                'similarity_score': round(similarity_score, 2)
            })
    
    # Sort by similarity score
    similar.sort(key=lambda x: x['similarity_score'], reverse=True)
    return similar[:3]  # Return top 3 matches

def is_ambiguous(item: str) -> bool:
    """Check if an item is too vague or ambiguous"""
    vague_patterns = [
        r'^(fix|update|improve|check|review|look at|work on)\s+(the|a|an)?\s*\w+$',  # "fix bug", "update docs"
        r'^\w+\s+(stuff|thing|issue|problem)$',  # "database stuff", "API thing"
        r'^(follow up|reach out|contact|email)$',  # Missing who/what
        r'^(investigate|research|explore)\s*\w{0,20}$',  # Too broad
    ]
    
    item_lower = item.lower().strip()
    
    # Check if too short
    if len(item_lower.split()) <= 2:
        return True
    
    # Check vague patterns
    for pattern in vague_patterns:
        if re.match(pattern, item_lower):
            return True
    
    return False

def generate_clarification_questions(item: str) -> List[str]:
    """Generate clarification questions for ambiguous items"""
    questions = []
    item_lower = item.lower()
    
    # Technical ambiguity
    if any(word in item_lower for word in ['fix', 'bug', 'error', 'issue']):
        questions.append("Which specific bug or error? Can you provide more details or error messages?")
        questions.append("What component or feature is affected?")
    
    # Scope ambiguity
    if any(word in item_lower for word in ['update', 'improve', 'refactor']):
        questions.append("What specific aspects need updating/improvement?")
        questions.append("What's the success criteria for this task?")
    
    # Missing target
    if any(word in item_lower for word in ['email', 'contact', 'reach out', 'follow up']):
        questions.append("Who should be contacted? (Check CRM for existing contacts)")
        questions.append("What's the purpose or goal of this outreach?")
    
    # Missing context
    if any(word in item_lower for word in ['research', 'investigate', 'explore']):
        questions.append("What specific questions need to be answered?")
        questions.append("What decisions will this research inform?")
    
    # Generic catch-all
    if not questions:
        questions.append("Can you provide more specific details about what needs to be done?")
        questions.append("What's the expected outcome or deliverable?")
    
    return questions

def guess_category(item: str) -> str:
    """Guess the category based on item text"""
    item_lower = item.lower()
    
    # Check for category indicators
    if any(word in item_lower for word in ['email', 'contact', 'reach out', 'follow up', 'meeting', 'call']):
        return 'outreach'
    elif any(word in item_lower for word in ['code', 'api', 'database', 'deploy', 'fix', 'bug', 'implement']):
        return 'technical'
    elif any(word in item_lower for word in ['research', 'study', 'learn', 'understand', 'investigate']):
        return 'research'
    elif any(word in item_lower for word in ['write', 'draft', 'document', 'blog', 'article', 'proposal']):
        return 'writing'
    elif any(word in item_lower for word in ['expense', 'invoice', 'schedule', 'calendar', 'organize']):
        return 'admin'
    elif any(word in item_lower for word in ['tweet', 'post', 'linkedin', 'social', 'twitter', 'marketing', 'blog']):
        return 'marketing'
    else:
        return 'other'

def generate_task_content(item: str, category: str) -> str:
    """Generate rich task content based on item and category"""
    
    # Base structure that all tasks get
    base_content = f"""## Overview
{get_task_overview(item, category)}

## Next Actions
{get_next_actions(item, category)}

## Notes & Details
- Task created from backlog processing
- Category: {category}
"""
    
    # Add category-specific sections
    if category == 'outreach':
        base_content += """
## Draft Message
[Draft outreach message here based on context]

## Contact Details
- Check CRM for existing contact information
- LinkedIn profile: [to be added]
- Email: [to be added]
"""
    elif category == 'writing':
        base_content += """
## Key Points
- [Main argument or thesis]
- [Supporting points]
- [Call to action]

## Target Audience
[Define who this is for]

## Resources
- [Related documents or references]
"""
    elif category == 'technical':
        base_content += """
## Technical Requirements
- [Specific technical details]
- [Dependencies or prerequisites]
- [Expected outcome]

## Implementation Notes
- [Technical approach]
- [Testing considerations]
"""
    elif category == 'research':
        base_content += """
## Research Questions
- [What are we trying to learn?]
- [Key hypotheses to test]

## Sources to Explore
- [Relevant resources]
- [People to consult]
"""
    elif category == 'marketing':
        base_content += """
## Content Strategy
- Platform: [Twitter/LinkedIn/Blog/etc]
- Key message: [Core point]
- Engagement goal: [What response do we want?]

## Draft Post
[Initial draft of marketing content]
"""
        
    return base_content

def get_task_overview(item: str, category: str) -> str:
    """Generate a contextual overview based on the task"""
    item_lower = item.lower()
    
    # Provide smarter overviews based on keywords
    if 'proposal' in item_lower:
        return f"Create and submit a comprehensive proposal for {item}. Research requirements, draft content, and prepare supporting materials."
    elif 'review' in item_lower:
        return f"Conduct thorough review of {item}. Provide feedback, suggestions, and actionable improvements."
    elif 'follow up' in item_lower or 'reach out' in item_lower:
        return f"Establish or continue communication regarding {item}. Ensure clear next steps and maintain relationship momentum."
    elif 'post' in item_lower or 'write' in item_lower:
        return f"Create compelling content for {item}. Focus on value delivery and audience engagement."
    elif 'implement' in item_lower or 'build' in item_lower:
        return f"Design and implement solution for {item}. Ensure functionality, testing, and documentation."
    else:
        return f"Complete {item} with focus on quality and timeliness."

def get_next_actions(item: str, category: str) -> str:
    """Generate smart next actions based on task type"""
    actions = []
    
    # Universal first steps
    actions.append("- [ ] Review related context and existing work")
    
    # Category-specific actions
    if category == 'outreach':
        actions.extend([
            "- [ ] Research contact's recent activity/interests",
            "- [ ] Draft personalized message",
            "- [ ] Schedule follow-up reminder"
        ])
    elif category == 'writing':
        actions.extend([
            "- [ ] Create outline with key points",
            "- [ ] Write first draft",
            "- [ ] Review and edit for clarity",
            "- [ ] Prepare for publication/submission"
        ])
    elif category == 'technical':
        actions.extend([
            "- [ ] Define technical requirements",
            "- [ ] Set up development environment",
            "- [ ] Implement core functionality",
            "- [ ] Test and validate solution"
        ])
    elif category == 'research':
        actions.extend([
            "- [ ] Define research questions",
            "- [ ] Gather relevant sources",
            "- [ ] Analyze and synthesize findings",
            "- [ ] Document insights and recommendations"
        ])
    elif category == 'marketing':
        actions.extend([
            "- [ ] Research trending topics/hashtags",
            "- [ ] Draft engaging content",
            "- [ ] Add relevant visuals/links",
            "- [ ] Schedule optimal posting time"
        ])
    else:
        actions.extend([
            "- [ ] Define specific requirements",
            "- [ ] Create action plan",
            "- [ ] Execute plan",
            "- [ ] Verify completion"
        ])
    
    return '\n'.join(actions)

def get_all_contacts() -> List[Dict[str, Any]]:
    """Get all contacts from the CRM directory"""
    contacts = []
    if not CRM_DIR.exists():
        return contacts
    
    for contact_file in CRM_DIR.glob('*.md'):
        try:
            with open(contact_file, 'r') as f:
                content = f.read()
                metadata, body = parse_yaml_frontmatter(content)
                if metadata:
                    metadata['filename'] = contact_file.name
                    metadata['body_content'] = body[:500] if body else ''
                    contacts.append(metadata)
        except Exception as e:
            logger.error(f"Error reading {contact_file}: {e}")
    
    return contacts

def update_file_frontmatter(filepath: Path, updates: dict) -> bool:
    """Update YAML frontmatter in a file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        metadata, body = parse_yaml_frontmatter(content)
        metadata.update(updates)
        
        # Reconstruct file
        yaml_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        new_content = f"---\n{yaml_str}---\n{body}"
        
        with open(filepath, 'w') as f:
            f.write(new_content)
        
        return True
    except Exception as e:
        logger.error(f"Error updating {filepath}: {e}")
        return False

# Create the MCP server
app = Server("manager-ai-mcp")

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List all available tools"""
    return [
        types.Tool(
            name="list_tasks",
            description="List tasks with optional filters (category, priority, status)",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Filter by category (comma-separated)"},
                    "priority": {"type": "string", "description": "Filter by priority (comma-separated, e.g., P0,P1)"},
                    "status": {"type": "string", "description": "Filter by status (n,s,b,d)"},
                    "include_done": {"type": "boolean", "description": "Include completed tasks", "default": False}
                }
            }
        ),
        types.Tool(
            name="create_task",
            description="Create a new task",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "category": {"type": "string", "description": "Task category", "default": "other"},
                    "priority": {"type": "string", "description": "Priority (P0-P3)", "default": "P2"},
                    "estimated_time": {"type": "integer", "description": "Estimated time in minutes", "default": 30},
                    "content": {"type": "string", "description": "Task content/description"}
                },
                "required": ["title"]
            }
        ),
        types.Tool(
            name="update_task_status",
            description="Update task status (n=not started, s=started, b=blocked, d=done)",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_file": {"type": "string", "description": "Task filename"},
                    "status": {"type": "string", "description": "New status (n,s,b,d)"}
                },
                "required": ["task_file", "status"]
            }
        ),
        types.Tool(
            name="get_task_summary",
            description="Get summary statistics for all tasks",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="check_priority_limits",
            description="Check if priority limits are exceeded",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="list_contacts",
            description="List CRM contacts with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Filter by location"},
                    "company": {"type": "string", "description": "Filter by company"},
                    "name": {"type": "string", "description": "Filter by name"}
                }
            }
        ),
        types.Tool(
            name="add_contact",
            description="Add a new contact to CRM",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Contact name"},
                    "email": {"type": "string", "description": "Email address"},
                    "company": {"type": "string", "description": "Company"},
                    "location": {"type": "string", "description": "Location"},
                    "phone": {"type": "string", "description": "Phone number"},
                    "linkedin": {"type": "string", "description": "LinkedIn URL"}
                },
                "required": ["name"]
            }
        ),
        types.Tool(
            name="search_contacts",
            description="Search contacts by query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_system_status",
            description="Get comprehensive system status",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="process_backlog",
            description="Read and return backlog contents",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="clear_backlog",
            description="Clear the backlog after processing",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="prune_completed_tasks",
            description="Delete completed tasks older than specified days",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Days old", "default": 30}
                }
            }
        ),
        types.Tool(
            name="process_backlog_with_dedup",
            description="Process backlog items with duplicate detection and clarification",
            inputSchema={
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of backlog items to process"
                    },
                    "auto_create": {
                        "type": "boolean",
                        "description": "Automatically create non-duplicate tasks",
                        "default": False
                    }
                },
                "required": ["items"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls"""
    
    if name == "list_tasks":
        tasks = get_all_tasks()
        
        # Apply filters
        if arguments:
            if not arguments.get('include_done', False):
                tasks = [t for t in tasks if t.get('status') != 'd']
            
            if arguments.get('category'):
                categories = [c.strip() for c in arguments['category'].split(',')]
                tasks = [t for t in tasks if t.get('category') in categories]
            
            if arguments.get('priority'):
                priorities = [p.strip() for p in arguments['priority'].split(',')]
                tasks = [t for t in tasks if t.get('priority') in priorities]
            
            if arguments.get('status'):
                statuses = [s.strip() for s in arguments['status'].split(',')]
                tasks = [t for t in tasks if t.get('status') in statuses]
        else:
            # Default: exclude done tasks
            tasks = [t for t in tasks if t.get('status') != 'd']
        
        result = {
            "tasks": tasks,
            "count": len(tasks),
            "filters_applied": arguments or {}
        }
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "create_task":
        title = arguments['title']
        category = arguments.get('category', 'other')
        priority = arguments.get('priority', 'P2')
        estimated_time = arguments.get('estimated_time', 30)
        content = arguments.get('content', '')
        
        # Create filename
        filename = title.replace('/', '_').replace('\\', '_') + '.md'
        filepath = TASKS_DIR / filename
        
        # Create task metadata
        metadata = {
            'title': title,
            'category': category,
            'priority': priority,
            'status': 'n',
            'estimated_time': estimated_time
        }
        
        # Create file content
        yaml_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
        file_content = f"---\n{yaml_str}---\n\n# {title}\n\n{content}"
        
        try:
            with open(filepath, 'w') as f:
                f.write(file_content)
            
            result = {
                "success": True,
                "filename": filename,
                "message": f"Task '{title}' created successfully"
            }
        except Exception as e:
            result = {
                "success": False,
                "error": str(e)
            }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "update_task_status":
        task_file = arguments['task_file']
        status = arguments['status']
        
        if not task_file.endswith('.md'):
            task_file += '.md'
        
        filepath = TASKS_DIR / task_file
        if not filepath.exists():
            result = {
                "success": False,
                "error": f"Task file not found: {task_file}"
            }
        else:
            success = update_file_frontmatter(filepath, {'status': status})
            status_names = {'n': 'not started', 's': 'started', 'b': 'blocked', 'd': 'done'}
            result = {
                "success": success,
                "task_file": task_file,
                "new_status": status_names.get(status, status)
            }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "get_task_summary":
        tasks = get_all_tasks()
        active_tasks = [t for t in tasks if t.get('status') != 'd']
        
        by_priority = Counter(t.get('priority', 'P2') for t in active_tasks)
        by_category = Counter(t.get('category', 'other') for t in active_tasks)
        by_status = Counter(t.get('status', 'n') for t in tasks)
        
        # Calculate time estimates
        time_by_priority = {}
        for priority in ['P0', 'P1', 'P2', 'P3']:
            priority_tasks = [t for t in active_tasks if t.get('priority') == priority]
            total_time = sum(t.get('estimated_time', 30) for t in priority_tasks)
            time_by_priority[priority] = {
                'total_minutes': total_time,
                'total_hours': round(total_time / 60, 1)
            }
        
        result = {
            "total_tasks": len(tasks),
            "active_tasks": len(active_tasks),
            "by_priority": dict(by_priority),
            "by_category": dict(by_category),
            "by_status": dict(by_status),
            "time_by_priority": time_by_priority
        }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "check_priority_limits":
        tasks = [t for t in get_all_tasks() if t.get('status') != 'd']
        by_priority = Counter(t.get('priority', 'P2') for t in tasks)
        
        thresholds = {'P0': 3, 'P1': 5, 'P2': 10}
        alerts = []
        
        for priority, threshold in thresholds.items():
            count = by_priority.get(priority, 0)
            if count > threshold:
                alerts.append(f"{priority} has {count} tasks (limit: {threshold})")
        
        result = {
            "priority_counts": dict(by_priority),
            "alerts": alerts,
            "balanced": len(alerts) == 0
        }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "list_contacts":
        contacts = get_all_contacts()
        
        # Apply filters
        if arguments:
            if arguments.get('location'):
                locations = [l.strip().lower() for l in arguments['location'].split(',')]
                contacts = [c for c in contacts if any(loc in (c.get('location') or '').lower() for loc in locations)]
            
            if arguments.get('company'):
                company_lower = arguments['company'].lower()
                contacts = [c for c in contacts if company_lower in (c.get('company') or '').lower()]
            
            if arguments.get('name'):
                name_lower = arguments['name'].lower()
                contacts = [c for c in contacts if name_lower in (c.get('name') or '').lower()]
        
        result = {
            "contacts": contacts,
            "count": len(contacts),
            "filters_applied": arguments or {}
        }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "add_contact":
        name = arguments['name']
        filename = name.replace(' ', '_').replace('/', '_') + '.md'
        filepath = CRM_DIR / filename
        
        if filepath.exists():
            result = {
                "success": False,
                "error": "Contact already exists"
            }
        else:
            # Create contact metadata
            metadata = {
                'name': name,
                'created_date': datetime.now().strftime('%Y-%m-%d'),
                'relationship_strength': 'new'
            }
            
            # Add optional fields
            for field in ['email', 'company', 'location', 'phone', 'linkedin']:
                if arguments.get(field):
                    metadata[field] = arguments[field]
            
            # Create file content
            yaml_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
            file_content = f"---\n{yaml_str}---\n\n# {name}\n\n## Notes\n"
            
            try:
                with open(filepath, 'w') as f:
                    f.write(file_content)
                
                result = {
                    "success": True,
                    "filename": filename,
                    "message": f"Contact '{name}' added successfully"
                }
            except Exception as e:
                result = {
                    "success": False,
                    "error": str(e)
                }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "search_contacts":
        contacts = get_all_contacts()
        query = arguments['query'].lower()
        
        matches = []
        for c in contacts:
            if (query in (c.get('name') or '').lower() or
                query in (c.get('company') or '').lower() or
                query in str(c.get('email') or '').lower() or
                query in (c.get('location') or '').lower() or
                query in (c.get('body_content') or '').lower()):
                matches.append(c)
        
        result = {
            "matches": matches,
            "count": len(matches),
            "query": arguments['query']
        }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "get_system_status":
        all_tasks = get_all_tasks()
        active_tasks = [t for t in all_tasks if t.get('status') != 'd']
        contacts = get_all_contacts()
        
        priority_counts = Counter(task['priority'] for task in active_tasks)
        status_counts = Counter(task['status'] for task in active_tasks)
        category_counts = Counter(task['category'] for task in active_tasks)
        
        # Check backlog
        backlog_items = 0
        backlog_file = BASE_DIR / 'BACKLOG.md'
        if backlog_file.exists():
            with open(backlog_file, 'r') as f:
                content = f.read().strip()
                if content and content != 'all done!':
                    backlog_items = len([l for l in content.split('\n') if l.strip().startswith('-')])
        
        # Time insights
        now = datetime.now()
        hour = now.hour
        day_name = now.strftime('%A')
        
        time_insights = []
        if 9 <= hour < 12:
            time_insights.append("Morning - ideal for outreach tasks")
        elif 14 <= hour < 17:
            time_insights.append("Afternoon - good for deep work")
        elif hour >= 17:
            time_insights.append("End of day - quick admin tasks")
        
        result = {
            "total_active_tasks": len(active_tasks),
            "total_contacts": len(contacts),
            "priority_distribution": dict(priority_counts),
            "status_distribution": dict(status_counts),
            "category_distribution": dict(category_counts),
            "backlog_items": backlog_items,
            "time_insights": time_insights,
            "timestamp": now.isoformat()
        }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "process_backlog":
        backlog_file = BASE_DIR / 'BACKLOG.md'
        
        if not backlog_file.exists():
            result = {
                "success": False,
                "error": "BACKLOG.md not found"
            }
        else:
            with open(backlog_file, 'r') as f:
                content = f.read().strip()
            
            if not content or content == 'all done!':
                result = {
                    "success": True,
                    "content": None,
                    "message": "Backlog is already clear"
                }
            else:
                # Parse items
                lines = content.split('\n')
                items = []
                current_item = None
                
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('- '):
                        if current_item:
                            items.append(current_item)
                        current_item = {
                            'text': stripped[2:],
                            'subitems': []
                        }
                    elif stripped.startswith('  - ') and current_item:
                        current_item['subitems'].append(stripped[4:])
                
                if current_item:
                    items.append(current_item)
                
                result = {
                    "success": True,
                    "content": content,
                    "parsed_items": items,
                    "count": len(items)
                }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "clear_backlog":
        backlog_file = BASE_DIR / 'BACKLOG.md'
        
        try:
            with open(backlog_file, 'w') as f:
                f.write("all done!")
            
            result = {
                "success": True,
                "message": "Backlog cleared successfully"
            }
        except Exception as e:
            result = {
                "success": False,
                "error": str(e)
            }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "prune_completed_tasks":
        days = arguments.get('days', 30) if arguments else 30
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted = []
        
        for task_file in TASKS_DIR.glob('*.md'):
            try:
                mtime = datetime.fromtimestamp(task_file.stat().st_mtime)
                if mtime < cutoff_date:
                    with open(task_file, 'r') as f:
                        content = f.read()
                        metadata, _ = parse_yaml_frontmatter(content)
                        if metadata.get('status') == 'd':
                            task_file.unlink()
                            deleted.append(task_file.name)
            except Exception as e:
                logger.error(f"Error processing {task_file}: {e}")
        
        result = {
            "success": True,
            "deleted_count": len(deleted),
            "deleted_files": deleted,
            "message": f"Deleted {len(deleted)} tasks older than {days} days"
        }
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "process_backlog_with_dedup":
        items = arguments.get('items', [])
        auto_create = arguments.get('auto_create', False)
        
        if not items:
            return [types.TextContent(type="text", text=json.dumps({
                "error": "No items provided to process"
            }, indent=2))]
        
        existing_tasks = get_all_tasks()
        existing_contacts = get_all_contacts()
        
        result = {
            "new_tasks": [],
            "potential_duplicates": [],
            "needs_clarification": [],
            "auto_created": [],
            "summary": {}
        }
        
        for item in items:
            # Check for duplicates
            similar_tasks = find_similar_tasks(item, existing_tasks)
            
            if similar_tasks:
                result["potential_duplicates"].append({
                    "item": item,
                    "similar_tasks": similar_tasks,
                    "recommended_action": "merge" if similar_tasks[0]['similarity_score'] > 0.8 else "review"
                })
            elif is_ambiguous(item):
                result["needs_clarification"].append({
                    "item": item,
                    "questions": generate_clarification_questions(item),
                    "suggestions": [
                        "Add more specific details",
                        "Include success criteria",
                        "Specify scope or boundaries"
                    ]
                })
            else:
                # This is a new, clear task
                result["new_tasks"].append({
                    "item": item,
                    "suggested_category": guess_category(item),
                    "suggested_priority": "P2",  # Default priority
                    "ready_to_create": True
                })
                
                # Auto-create if requested
                if auto_create:
                    # Create the task file
                    safe_filename = re.sub(r'[^\w\s-]', '', item).strip()
                    safe_filename = re.sub(r'[-\s]+', ' ', safe_filename)
                    task_file = TASKS_DIR / f"{safe_filename}.md"
                    
                    metadata = {
                        "title": item,
                        "category": guess_category(item),
                        "priority": "P2",
                        "status": "n",
                        "estimated_time": 60
                    }
                    
                    yaml_str = yaml.dump(metadata, default_flow_style=False, sort_keys=False)
                    
                    # Generate richer task content based on category
                    task_content = generate_task_content(item, metadata['category'])
                    content = f"---\n{yaml_str}---\n\n# {item}\n\n{task_content}"
                    
                    with open(task_file, 'w') as f:
                        f.write(content)
                    
                    result["auto_created"].append(safe_filename + ".md")
        
        # Add summary
        result["summary"] = {
            "total_items": len(items),
            "new_tasks": len(result["new_tasks"]),
            "duplicates_found": len(result["potential_duplicates"]),
            "needs_clarification": len(result["needs_clarification"]),
            "auto_created": len(result["auto_created"]),
            "recommendations": []
        }
        
        # Add recommendations
        if result["potential_duplicates"]:
            result["summary"]["recommendations"].append(
                f"Review {len(result['potential_duplicates'])} potential duplicates before creating tasks"
            )
        
        if result["needs_clarification"]:
            result["summary"]["recommendations"].append(
                f"Clarify {len(result['needs_clarification'])} ambiguous items for better task definition"
            )
        
        if result["new_tasks"] and not auto_create:
            result["summary"]["recommendations"].append(
                f"Ready to create {len(result['new_tasks'])} new tasks - use auto_create=true or create manually"
            )
        
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
    
    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def main():
    """Main entry point for the MCP server"""
    logger.info(f"Starting Manager AI MCP Server")
    logger.info(f"Working directory: {BASE_DIR}")
    logger.info(f"Tasks directory: {TASKS_DIR}")
    logger.info(f"CRM directory: {CRM_DIR}")
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="manager-ai-mcp",
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
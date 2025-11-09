#!/usr/bin/env python3
"""
Setup script for Personal OS task management system
Creates necessary directories and generates personalized GOALS.md through LLM-powered interview
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60 + '\n')

def llm_generate_goals():
    """Use Claude API to interview user and generate GOALS.md"""
    try:
        import anthropic
    except ImportError:
        print("❌ Anthropic SDK not installed. Install with: pip install anthropic")
        return None
    
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("\n⚠️  ANTHROPIC_API_KEY not found in environment variables.")
        print("\nTo use LLM-powered GOALS.md generation:")
        print("1. Get an API key from: https://console.anthropic.com/")
        print("2. Set it: export ANTHROPIC_API_KEY='your-key-here'")
        print("3. Run setup.py again")
        print("\nFalling back to manual interview mode...")
        return None
    
    client = anthropic.Anthropic(api_key=api_key)
    
    current_date = datetime.now().strftime("%B %d, %Y")
    
    system_prompt = f"""You are a thoughtful career coach helping a product manager set up their personal task management system. Your role is to:

1. Have a natural conversation to understand their goals, vision, and priorities
2. Ask follow-up questions to dig deeper when responses are vague
3. Focus on PM/product work context: shipping features, stakeholder communication, user research, analysis, marketing
4. After gathering enough information, generate a comprehensive GOALS.md file

Interview Structure:
- Current role and context
- Professional vision and what they're building toward
- Success criteria (12 months and 5 years)
- Current focus and quarterly objectives
- Skills to develop and relationships to build
- Challenges, opportunities, and top 3 priorities

After 5-7 exchanges, generate the GOALS.md in this EXACT format:

```markdown
# Goals & Strategic Direction

*Last updated: {current_date}*

## Current Context

### Role & Responsibilities
[Their role and company]

### Primary Vision
[Their vision with expanded thoughts]

## Success Criteria

### 12-Month Horizon
[What success looks like]

### 5-Year North Star
[Long-term direction]

## Current Focus Areas

### This Quarter's Objectives
[Quarterly goals]

**Success Metrics:**
[How they'll measure success]

### Skill Development
[Skills to develop]

### Key Relationships & Network Building
[Network to build]

## Strategic Context

### Challenges & Blockers
[Current challenges]

### Opportunities to Explore
[Opportunities]

## Priority Framework

When evaluating new tasks and commitments:

**P0 (Critical/Urgent)** - Must do THIS WEEK:
- Directly advances quarterly objectives
- Time-sensitive opportunities
- Critical stakeholder communication
- Immediate blockers to remove

**P1 (Important)** - This month:
- Builds key skills or expertise
- Advances product strategy
- Significant career development
- High-value learning opportunities

**P2 (Normal)** - Scheduled work:
- Supports broader objectives
- Maintains stakeholder relationships
- Operational efficiency
- General learning and exploration

**P3 (Low)** - Nice to have:
- Administrative tasks
- Speculative projects
- Activities without clear advancement value

## Top 3 Priorities (Right Now)

[Their top 3 priorities]

## Decision Filters

Before saying YES to anything, ask:
1. Does this align with my 12-month vision?
2. Is this the best use of my time vs other opportunities?
3. What would I need to say NO to in order to do this well?
4. Does this build skills, relationships, or credibility I need?

## Weekly Review Questions

Every week, reflect on:
- What moved me closer to my quarterly objectives?
- What held me back or distracted me?
- What needs to change next week?
- Am I focusing on the right priorities?
- Which relationships need attention?

## Monthly Review Questions

Every month, assess:
- Are my quarterly objectives still the right ones?
- What's my velocity toward the 12-month vision?
- What skills gaps are becoming critical?
- Which relationships are bearing fruit?
- What opportunities should I pursue or drop?

## Notes & Reminders

- **Ambition**: Dream 10x, not 10% better
- **Speed**: It's just as hard to dream big as dream small
- **Focus**: Warren Buffett's rule - "The difference between successful people and really successful people is that really successful people say no to almost everything"
- **Momentum**: Small wins compound - ship weekly, not monthly
- **Network**: Your network is your net worth - invest in relationships
- **Learning**: Learn from the best people, not just from books

## Context for AI Agent

When processing my backlog and creating tasks:
- Reference these goals to inform priority levels
- Flag tasks that don't align with stated objectives
- Proactively suggest tasks that advance quarterly goals
- Consider skill development opportunities
- Challenge me on low-leverage activities

---

*Review this document monthly. Update as your situation and vision evolve.*
```

Be conversational, encouraging, and thorough. Signal when you're ready to generate the document by saying "Based on our conversation, here's your personalized GOALS.md:"
"""
    
    print_section("LLM-Powered Goals Setup")
    print("I'll have a conversation with Claude to understand your goals.")
    print("Claude will ask thoughtful questions and generate a comprehensive GOALS.md for you.")
    print("\nRespond naturally - Claude will dig deeper where needed.")
    input("\nPress Enter to start the conversation...\n")
    
    messages = []
    conversation_active = True
    goals_content = None
    
    # Start conversation
    messages.append({
        "role": "user",
        "content": "Hi! I'm setting up my personal task management system and need help defining my goals."
    })
    
    while conversation_active:
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                system=system_prompt,
                messages=messages
            )
            
            assistant_message = response.content[0].text
            messages.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            print(f"\nClaude: {assistant_message}\n")
            
            # Check if Claude has generated the GOALS.md
            if "# Goals & Strategic Direction" in assistant_message:
                # Extract the markdown content
                if "```markdown" in assistant_message:
                    start = assistant_message.find("```markdown") + 11
                    end = assistant_message.find("```", start)
                    goals_content = assistant_message[start:end].strip()
                else:
                    # Claude might have just output the markdown directly
                    start = assistant_message.find("# Goals & Strategic Direction")
                    if start != -1:
                        goals_content = assistant_message[start:].strip()
                
                if goals_content:
                    print("\n✅ GOALS.md generated successfully!")
                    conversation_active = False
                    break
            
            # Get user response
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'done']:
                print("Conversation ended. Falling back to manual mode...")
                return None
            
            if user_input:
                messages.append({
                    "role": "user",
                    "content": user_input
                })
        
        except Exception as e:
            print(f"\n❌ Error during conversation: {e}")
            print("Falling back to manual interview mode...")
            return None
    
    return goals_content

def ask_question(question, examples=None, optional=False):
    """Ask a question with optional examples"""
    if examples:
        print(f"{question}")
        print(f"   Examples: {examples}")
    else:
        print(f"{question}")
    
    suffix = " (press Enter to skip)" if optional else ""
    response = input(f"   → {suffix}: ").strip()
    return response if response else None

def manual_goals_setup():
    """Fallback manual interview to create GOALS.md"""
    
    print_section("Manual Goals Setup")
    print("I'll ask you some questions to understand your goals and priorities.")
    print("This will help your AI agent make smarter decisions about task priorities.")
    print("\nBe honest and specific - this is for you, not anyone else.")
    print("You can always edit GOALS.md later to refine your thinking.")
    
    answers = {}
    
    # Current situation
    print_section("1. Current Situation")
    answers['role'] = ask_question(
        "What's your current role?",
        "Product Manager, Senior Engineer, Founder, VP Product"
    )
    answers['company'] = ask_question(
        "What company or organization?",
        optional=True
    )
    
    # Vision and direction
    print_section("2. Vision & Direction")
    answers['vision'] = ask_question(
        "What's your primary professional vision? What are you building toward?",
        "Become VP Product, Launch a successful product, Build a thriving consultancy"
    )
    
    if answers['vision']:
        print("\nTell me more about that vision...")
        answers['vision_expanded'] = ask_question(
            "What would achieving this enable? Why does it matter to you?",
            optional=True
        )
    
    # Success criteria
    print_section("3. Success Criteria")
    answers['success_12mo'] = ask_question(
        "In 12 months, what would make you think 'this was a successful year'?",
        "Shipped 3 major features, Built a team of 10, Became recognized expert in my field"
    )
    
    answers['success_5yr'] = ask_question(
        "What's your 5-year north star? Where do you want to be?",
        optional=True
    )
    
    # Current focus
    print_section("4. Current Focus")
    answers['current_focus'] = ask_question(
        "What are you actively working on right now?",
        "Product roadmap, Team building, User research initiative"
    )
    
    answers['q1_goals'] = ask_question(
        "What are your objectives for THIS QUARTER (next 90 days)?",
        "Launch new feature, Improve activation by 20%, Build PM practice"
    )
    
    if answers['q1_goals']:
        answers['q1_metrics'] = ask_question(
            "How will you measure success on those quarterly objectives?",
            "User adoption, Revenue, Team satisfaction, Thought leadership metrics",
            optional=True
        )
    
    # Development areas
    print_section("5. Development & Growth")
    answers['skills'] = ask_question(
        "What skills do you need to develop to achieve your vision?",
        "Data analysis, Technical architecture, Strategic communication, AI/ML",
        optional=True
    )
    
    answers['relationships'] = ask_question(
        "What key relationships or network do you need to build?",
        "Engineering leaders, Design partners, Industry experts, Executive stakeholders",
        optional=True
    )
    
    # Challenges and opportunities
    print_section("6. Challenges & Opportunities")
    answers['challenges'] = ask_question(
        "What's currently blocking you or slowing you down?",
        "Time management, Technical knowledge gaps, Cross-functional alignment",
        optional=True
    )
    
    answers['opportunities'] = ask_question(
        "What opportunities are you exploring or considering?",
        "Speaking engagements, Product launches, Team expansion, Strategic partnerships",
        optional=True
    )
    
    # Priorities
    print_section("7. Priority Setting")
    print("Finally, let's get crystal clear on priorities...")
    answers['priorities'] = ask_question(
        "What are your TOP 3 PRIORITIES right now? (Be brutally honest)",
        "1. Ship Q1 roadmap, 2. Build thought leadership, 3. Develop AI product skills"
    )
    
    print_section("Processing Your Responses")
    print("Generating your personalized GOALS.md...")
    
    # Generate content
    current_date = datetime.now().strftime("%B %d, %Y")
    
    role_section = answers.get('role', '[Your current role]')
    company_section = answers.get('company', '[Your company]')
    
    vision_section = answers.get('vision', '[Your long-term vision]')
    if answers.get('vision_expanded'):
        vision_section += f"\n\n{answers['vision_expanded']}"
    
    success_12mo = answers.get('success_12mo', '[What success looks like in 12 months]')
    success_5yr = answers.get('success_5yr', '[Your 5-year north star]')
    
    skills = answers.get('skills', '[Skills to develop]')
    relationships = answers.get('relationships', '[Key relationships to build]')
    
    q1_goals = answers.get('q1_goals', '[This quarter\'s objectives]')
    q1_metrics = answers.get('q1_metrics', '[How you\'ll measure success]')
    
    challenges = answers.get('challenges', '[Current blockers or challenges]')
    opportunities = answers.get('opportunities', '[Opportunities you\'re exploring]')
    
    priorities = answers.get('priorities', '[Your top 3 priorities]')
    
    content = f"""# Goals & Strategic Direction

*Last updated: {current_date}*

## Current Context

### Role & Responsibilities
{role_section} at {company_section}

### Primary Vision
{vision_section}

## Success Criteria

### 12-Month Horizon
{success_12mo}

### 5-Year North Star  
{success_5yr}

## Current Focus Areas

### This Quarter's Objectives
{q1_goals}

**Success Metrics:**
{q1_metrics}

### Skill Development
{skills}

### Key Relationships & Network Building
{relationships}

## Strategic Context

### Challenges & Blockers
{challenges}

### Opportunities to Explore
{opportunities}

## Priority Framework

When evaluating new tasks and commitments:

**P0 (Critical/Urgent)** - Must do THIS WEEK:
- Directly advances quarterly objectives
- Time-sensitive opportunities
- Critical stakeholder communication
- Immediate blockers to remove

**P1 (Important)** - This month:
- Builds key skills or expertise
- Advances product strategy
- Significant career development
- High-value learning opportunities

**P2 (Normal)** - Scheduled work:
- Supports broader objectives
- Maintains stakeholder relationships
- Operational efficiency
- General learning and exploration

**P3 (Low)** - Nice to have:
- Administrative tasks
- Speculative projects
- Activities without clear advancement value

## Top 3 Priorities (Right Now)

{priorities}

## Decision Filters

Before saying YES to anything, ask:
1. Does this align with my 12-month vision?
2. Is this the best use of my time vs other opportunities?
3. What would I need to say NO to in order to do this well?
4. Does this build skills, relationships, or credibility I need?

## Weekly Review Questions

Every week, reflect on:
- What moved me closer to my quarterly objectives?
- What held me back or distracted me?
- What needs to change next week?
- Am I focusing on the right priorities?
- Which relationships need attention?

## Monthly Review Questions

Every month, assess:
- Are my quarterly objectives still the right ones?
- What's my velocity toward the 12-month vision?
- What skills gaps are becoming critical?
- Which relationships are bearing fruit?
- What opportunities should I pursue or drop?

## Notes & Reminders

- **Ambition**: Dream 10x, not 10% better
- **Speed**: It's just as hard to dream big as dream small
- **Focus**: Warren Buffett's rule - "The difference between successful people and really successful people is that really successful people say no to almost everything"
- **Momentum**: Small wins compound - ship weekly, not monthly
- **Network**: Your network is your net worth - invest in relationships
- **Learning**: Learn from the best people, not just from books

## Context for AI Agent

When processing my backlog and creating tasks:
- Reference these goals to inform priority levels
- Flag tasks that don't align with stated objectives
- Proactively suggest tasks that advance quarterly goals
- Consider skill development opportunities
- Challenge me on low-leverage activities

---

*Review this document monthly. Update as your situation and vision evolve.*
"""
    
    return content

def setup():
    """Setup the task management system"""
    print("🚀 Setting up Personal OS Task Management System...")
    
    base_dir = Path.cwd()
    
    # Create directories
    directories = ['Tasks', 'Knowledge', 'Resources']
    for dir_name in directories:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True)
            print(f"✅ Created directory: {dir_name}/")
        else:
            print(f"📁 Directory exists: {dir_name}/")
    
    # Check if this is first-time setup
    goals_path = base_dir / 'GOALS.md'
    is_first_time = not goals_path.exists()
    
    # Copy template files ONLY if they don't exist
    templates = {
        'core/templates/CLAUDE.md': 'CLAUDE.md',
        'core/templates/gitignore': '.gitignore',
    }
    
    for source, dest in templates.items():
        source_path = base_dir / source
        dest_path = base_dir / dest
        
        if source_path.exists():
            if not dest_path.exists():
                import shutil
                shutil.copy2(source_path, dest_path)
                print(f"✅ Copied: {source} → {dest}")
            else:
                print(f"📁 File exists: {dest} (preserving your version)")
        else:
            print(f"❌ Template not found: {source}")
    
    # GOALS.md generation
    if is_first_time:
        print("\n" + "="*60)
        print("  TIME TO BUILD YOUR PERSONALIZED GOALS")
        print("="*60)
        print("\nThis is the heart of your Personal OS.")
        print("Your AI agent will use this to understand what matters to you")
        print("and help prioritize your work accordingly.")
        print("\nReady? Let's dive in...")
        input("\nPress Enter to start...\n")
        
        # Try LLM-powered generation first
        goals_content = llm_generate_goals()
        
        # Fall back to manual if LLM fails
        if not goals_content:
            goals_content = manual_goals_setup()
        
        goals_path.write_text(goals_content)
        print("\n✅ Created personalized GOALS.md")
    else:
        if goals_path.exists():
            print("📁 GOALS.md already exists")
            recreate = input("   Would you like to recreate it? (y/n): ")
            if recreate.lower() == 'y':
                # Try LLM-powered generation first
                goals_content = llm_generate_goals()
                
                # Fall back to manual if LLM fails
                if not goals_content:
                    goals_content = manual_goals_setup()
                
                goals_path.write_text(goals_content)
                print("\n✅ Recreated GOALS.md")
        else:
            print("⚠️  GOALS.md not found - creating it now...")
            goals_content = llm_generate_goals()
            
            if not goals_content:
                goals_content = manual_goals_setup()
            
            goals_path.write_text(goals_content)
            print("\n✅ Created GOALS.md")
    
    # Create BACKLOG.md if it doesn't exist
    backlog_path = base_dir / 'BACKLOG.md'
    if not backlog_path.exists():
        backlog_path.write_text("# Backlog\n\nDrop raw notes or todos here. Say `process my backlog` when you're ready for triage.\n")
        print("✅ Created: BACKLOG.md")
    else:
        print("📁 File exists: BACKLOG.md")
    
    print_section("Setup Complete!")
    print("Your Personal OS is ready to use.")
    print("\n📋 Next Steps:")
    print("1. Review GOALS.md and refine as needed")
    print("2. Read CLAUDE.md to understand how your AI agent works")
    print("3. Start adding tasks or notes to BACKLOG.md")
    print("4. Tell your AI: 'Read CLAUDE.md and help me process my backlog'")
    print("\n💡 Pro Tips:")
    print("• Update GOALS.md monthly as your situation evolves")
    print("• Use BACKLOG.md as a brain dump - clear it weekly")
    print("• Review your Tasks/ folder daily to stay on track")
    print("\n🎯 You're all set! Time to get organized and ship great work.")

if __name__ == "__main__":
    setup()

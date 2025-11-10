#!/usr/bin/env bash

# Personal OS Setup Script
# Creates directories, copies templates, and guides you through goals creation

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo ""
    echo "============================================================"
    echo "  $1"
    echo "============================================================"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

ask_question() {
    local prompt="$1"
    local example="$2"
    local response=""

    echo ""
    echo "$prompt"
    if [ -n "$example" ]; then
        echo -e "${BLUE}$example${NC}"
    fi
    read -r response
    echo "$response"
}

ask_multiline() {
    local prompt="$1"
    local response=""

    echo ""
    echo "$prompt"
    echo "(Type your answer, then press Ctrl+D when done)"
    echo ""
    response=$(cat)
    echo "$response"
}

# Start setup
clear
print_header "Welcome to Personal OS Setup"

echo "This setup will help you:"
echo "  1. Create your workspace structure"
echo "  2. Define your goals and priorities"
echo "  3. Configure your AI assistant"
echo ""
echo "Takes about 5-10 minutes. Be honest and specific."
echo ""
read -p "Press Enter to begin..."

# Create directories
print_header "Creating Workspace"

for dir in "Tasks" "Knowledge"; do
    if [ -d "$dir" ]; then
        print_info "Directory exists: $dir/"
    else
        mkdir -p "$dir"
        print_success "Created: $dir/"
    fi
done

# Copy template files
print_header "Setting Up Templates"

if [ ! -f "CLAUDE.md" ] && [ -f "core/templates/CLAUDE.md" ]; then
    cp "core/templates/CLAUDE.md" "CLAUDE.md"
    print_success "Copied: CLAUDE.md"
else
    print_info "File exists: CLAUDE.md (preserving your version)"
fi

if [ ! -f ".gitignore" ] && [ -f "core/templates/gitignore" ]; then
    cp "core/templates/gitignore" ".gitignore"
    print_success "Copied: .gitignore"
else
    print_info "File exists: .gitignore (preserving your version)"
fi

# Create BACKLOG.md
if [ ! -f "BACKLOG.md" ]; then
    cat > "BACKLOG.md" << 'EOF'
# Backlog

Drop raw notes or todos here. Say `process my backlog` when you're ready for triage.
EOF
    print_success "Created: BACKLOG.md"
else
    print_info "File exists: BACKLOG.md"
fi

# Goals creation
print_header "Building Your Personal Goals"

echo "Now let's create your GOALS.md - the heart of your Personal OS."
echo ""
echo "I'll ask you about your goals and priorities."
echo "This helps your AI agent make smarter decisions about task priorities."
echo ""
echo "Be honest and specific - this is for you, not anyone else."
echo "You can always edit GOALS.md later to refine your thinking."
echo ""
read -p "Ready to dive in? Press Enter to start..."

# Collect answers (using individual variables for bash 3.2 compatibility)

# Section 1: Current Situation
print_header "1. Current Situation"

ans_role=$(ask_question \
    "What's your current role?" \
    "Product Manager, Senior Engineer, Founder, VP Product")

ans_company=$(ask_question \
    "What company or organization? (optional)" \
    "")

# Section 2: Vision & Direction
print_header "2. Vision & Direction"

ans_vision=$(ask_question \
    "What's your primary professional vision? What are you building toward?" \
    "Become VP Product, Launch a successful product, Build a thriving consultancy")

if [ -n "$ans_vision" ]; then
    echo ""
    echo "Tell me more about that vision..."
    ans_vision_why=$(ask_question \
        "What would achieving this enable? Why does it matter to you?" \
        "")
fi

# Section 3: Success Criteria
print_header "3. Success Criteria"

ans_success_12mo=$(ask_question \
    "In 12 months, what would make you think 'this was a successful year'?" \
    "Shipped 3 major features, Built a team of 10, Became recognized expert in my field")

ans_success_5yr=$(ask_question \
    "What's your 5-year north star? Where do you want to be?" \
    "")

# Section 4: Current Focus
print_header "4. Current Focus"

ans_current_focus=$(ask_question \
    "What are you actively working on right now?" \
    "Product roadmap, Team building, User research initiative")

ans_q1_goals=$(ask_question \
    "What are your objectives for THIS QUARTER (next 90 days)?" \
    "Launch new feature, Improve activation by 20%, Build PM practice")

if [ -n "$ans_q1_goals" ]; then
    ans_q1_metrics=$(ask_question \
        "How will you measure success on those quarterly objectives?" \
        "User adoption, Revenue, Team satisfaction")
fi

# Section 5: Development & Growth
print_header "5. Development & Growth"

ans_skills=$(ask_question \
    "What skills do you need to develop to achieve your vision?" \
    "Data analysis, Technical architecture, Strategic communication")

ans_relationships=$(ask_question \
    "What key relationships or network do you need to build?" \
    "Engineering leaders, Design partners, Industry experts")

# Section 6: Challenges & Opportunities
print_header "6. Challenges & Opportunities"

ans_challenges=$(ask_question \
    "What's currently blocking you or slowing you down?" \
    "Time management, Technical knowledge gaps, Cross-functional alignment")

ans_opportunities=$(ask_question \
    "What opportunities are you exploring or considering?" \
    "Speaking engagements, Product launches, Team expansion")

# Section 7: Priority Setting
print_header "7. Priority Setting"
echo "Finally, let's get crystal clear on priorities..."

ans_top3=$(ask_question \
    "What are your TOP 3 PRIORITIES right now? (Be brutally honest)" \
    "1. Ship Q1 roadmap, 2. Build thought leadership, 3. Develop AI product skills")

# Generate GOALS.md
print_header "Generating Your GOALS.md"

CURRENT_DATE=$(date +"%B %d, %Y")

cat > "GOALS.md" << EOF
# Goals & Strategic Direction

*Last updated: ${CURRENT_DATE}*

## Current Context

### Role & Responsibilities
${ans_role}${ans_company:+ at }${ans_company}

### Primary Vision
${ans_vision}

${ans_vision_why:+${ans_vision_why}}

## Success Criteria

### 12-Month Horizon
${ans_success_12mo}

### 5-Year North Star
${ans_success_5yr}

## Current Focus Areas

### What I'm Working On
${ans_current_focus}

### This Quarter's Objectives
${ans_q1_goals}

${ans_q1_metrics:+**Success Metrics:**
${ans_q1_metrics}}

### Skill Development
${ans_skills}

### Key Relationships & Network Building
${ans_relationships}

## Strategic Context

### Challenges & Blockers
${ans_challenges}

### Opportunities to Explore
${ans_opportunities}

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

${ans_top3}

---

**Your AI assistant uses this document to prioritize tasks and suggest what to work on each day.**

*Review and update this weekly as your priorities shift.*

EOF

print_success "Created: GOALS.md"

# Final summary
print_header "Setup Complete!"

echo "Your Personal OS is ready to use."
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Review GOALS.md and refine as needed"
echo "2. Read CLAUDE.md to understand how your AI agent works"
echo "3. Start adding tasks or notes to BACKLOG.md"
echo "4. Tell your AI: 'Read CLAUDE.md and help me process my backlog'"
echo ""
print_success "Happy organizing!"
echo ""

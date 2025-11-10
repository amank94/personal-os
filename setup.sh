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

    # Print prompt to terminal (stderr so it's not captured)
    echo "" >&2
    echo "$prompt" >&2
    if [ -n "$example" ]; then
        echo -e "${BLUE}$example${NC}" >&2
    fi
    read -r response
    # Return answer to stdout (gets captured)
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
echo "Takes about 2 minutes. Be honest and specific."
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

# Collect answers (keeping it short - 5 essential questions)

# Section 1: Current Situation
print_header "1. Current Situation"

ans_role=$(ask_question \
    "What's your current role?" \
    "Product Manager, Senior Engineer, Founder, VP Product")

# Section 2: Vision
print_header "2. Your Vision"

ans_vision=$(ask_question \
    "What's your primary professional vision? What are you building toward?" \
    "Become VP Product, Launch a successful product, Build a thriving consultancy")

# Section 3: Success This Year
print_header "3. Success This Year"

ans_success_12mo=$(ask_question \
    "In 12 months, what would make you think 'this was a successful year'?" \
    "Shipped 3 major features, Built a team of 10, Became recognized expert in my field")

# Section 4: This Quarter
print_header "4. This Quarter"

ans_q1_goals=$(ask_question \
    "What are your objectives for THIS QUARTER (next 90 days)?" \
    "Launch new feature, Improve activation by 20%, Build PM practice")

# Section 5: Top Priorities
print_header "5. Top Priorities"

ans_top3=$(ask_question \
    "What are your top 3 priorities right now? (Be brutally honest)" \
    "1. Ship Q1 roadmap, 2. Build thought leadership, 3. Develop AI product skills")

# Set empty placeholders for sections user can fill in later
ans_company=""
ans_vision_why=""
ans_success_5yr=""
ans_current_focus=""
ans_q1_metrics=""
ans_skills=""
ans_relationships=""
ans_challenges=""
ans_opportunities=""

# Generate GOALS.md
print_header "Generating Your GOALS.md"

CURRENT_DATE=$(date +"%B %d, %Y")

cat > "GOALS.md" << EOF
# Goals & Strategic Direction

*Last updated: ${CURRENT_DATE}*

## Current Context

### What's your current role?
${ans_role}${ans_company:+ at }${ans_company}

### What's your primary professional vision? What are you building toward?
${ans_vision}

${ans_vision_why:+**Why this matters:**
${ans_vision_why}}

## Success Criteria

### In 12 months, what would make you think 'this was a successful year'?
${ans_success_12mo}

### What's your 5-year north star? Where do you want to be?
${ans_success_5yr}

## Current Focus Areas

### What are you actively working on right now?
${ans_current_focus}

### What are your objectives for THIS QUARTER (next 90 days)?
${ans_q1_goals}

${ans_q1_metrics:+**How will you measure success on those quarterly objectives?**
${ans_q1_metrics}}

### What skills do you need to develop to achieve your vision?
${ans_skills}

### What key relationships or network do you need to build?
${ans_relationships}

## Strategic Context

### What's currently blocking you or slowing you down?
${ans_challenges}

### What opportunities are you exploring or considering?
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

## What are your top 3 priorities right now?

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

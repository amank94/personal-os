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

    echo "" >&2
    echo "$prompt" >&2
    if [ -n "$example" ]; then
        echo -e "${BLUE}Examples: $example${NC}" >&2
    fi
    echo -n "> " >&2
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
echo "  2. Define your goals using a work-life harmony approach"
echo "  3. Configure your AI assistant"
echo ""
echo "This takes about 5-10 minutes. Take your time and be thoughtful."
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
echo "We'll use a 'Designing Your Life' approach to help you:"
echo "  • Identify what energizes vs. drains you"
echo "  • Align your work with your values"
echo "  • Balance different areas of your life"
echo "  • Set meaningful priorities"
echo ""
echo "Your AI assistant will use these goals to:"
echo "  • Suggest what to work on each day"
echo "  • Prioritize tasks automatically"
echo "  • Flag when you're drifting from what matters"
echo ""
read -p "Ready to dive in? Press Enter to start..."

# Collect answers (using individual variables for bash 3.2 compatibility)

# Section 1: Current Context
print_header "1. Your Current Context"

ans_role=$(ask_question \
    "What's your current role or primary work?" \
    "Product Manager, Software Engineer, Founder, Consultant")

ans_time_split=$(ask_question \
    "How do you currently split your time? (rough %)" \
    "40% product work, 30% stakeholder mgmt, 20% team, 10% learning")

# Section 2: Energy & Engagement
print_header "2. What Energizes You?"

echo ""
echo "Think about your last few weeks of work..."
echo ""

ans_energizing=$(ask_question \
    "What activities or tasks make you feel most alive and engaged?" \
    "Solving tough problems, mentoring others, writing specs, user research")

ans_draining=$(ask_question \
    "What drains your energy or feels like a slog?" \
    "Status meetings, repetitive tasks, office politics, interruptions")

# Section 3: Core Values
print_header "3. Your Core Values"

ans_values=$(ask_question \
    "What 3-5 values guide your work and life decisions?" \
    "Growth, Impact, Autonomy, Creativity, Balance")

ans_why_matter=$(ask_question \
    "Why do these values matter to you? What do they enable?" \
    "They help me do meaningful work while staying sane")

# Section 4: Life Areas
print_header "4. Life Balance"

echo ""
echo "Rate these areas on a scale of 1-10 (current satisfaction):"
echo ""

ans_health=$(ask_question "Health & Well-being (exercise, sleep, energy):" "")
ans_work=$(ask_question "Work & Career (growth, impact, enjoyment):" "")
ans_relationships=$(ask_question "Relationships (family, friends, network):" "")
ans_learning=$(ask_question "Learning & Growth (skills, knowledge, curiosity):" "")

echo ""
echo "Which ONE area needs the most attention right now?"
echo -n "> "
read -r ans_focus_area

# Section 5: Vision & Direction
print_header "5. Your Vision"

ans_vision_12mo=$(ask_question \
    "12 months from now, what would make you think 'this was a great year'?" \
    "Shipped 3 major features, got promoted, launched side project, ran a marathon")

ans_vision_3yr=$(ask_question \
    "In 3 years, where do you want to be professionally?" \
    "VP Product, Running my own consultancy, Leading a team of 10")

ans_avoid=$(ask_question \
    "What do you want to AVOID or say NO to?" \
    "Burnout, meaningless work, toxic environments, over-commitment")

# Section 6: Current Focus
print_header "6. Current Priorities"

ans_top_priorities=$(ask_question \
    "What are your top 3 priorities RIGHT NOW?" \
    "1) Launch feature X, 2) Hire 2 engineers, 3) Build exec presence")

ans_projects=$(ask_question \
    "What specific projects or initiatives are you driving?" \
    "Q1 Roadmap, New analytics platform, Team restructuring")

# Section 7: Outcomes
print_header "7. What Success Looks Like"

ans_outcomes_this_quarter=$(ask_question \
    "By end of this quarter, what outcomes would you celebrate?" \
    "Feature shipped to 10k users, Team velocity increased 30%, New skill learned")

ans_how_measure=$(ask_question \
    "How will you measure progress? What signals matter?" \
    "User adoption metrics, Team feedback, Stakeholder satisfaction, Personal energy")

# Generate GOALS.md
print_header "Generating Your GOALS.md"

CURRENT_DATE=$(date +"%B %d, %Y")

cat > "GOALS.md" << EOF
# Personal Goals & Priorities

*Last updated: ${CURRENT_DATE}*

## Who I Am

**Current Role:** ${ans_role}

**Time Distribution:** ${ans_time_split}

## What Energizes Me

**Tasks that give me energy:**
${ans_energizing}

**Things that drain me:**
${ans_draining}

## Core Values

${ans_values}

**Why these matter:**
${ans_why_matter}

## Life Balance Dashboard

Current satisfaction (1-10 scale):
- **Health & Well-being:** ${ans_health}/10
- **Work & Career:** ${ans_work}/10
- **Relationships:** ${ans_relationships}/10
- **Learning & Growth:** ${ans_learning}/10

**Needs attention:** ${ans_focus_area}

## Vision & Direction

### 12-Month Vision
${ans_vision_12mo}

### 3-Year North Star
${ans_vision_3yr}

### What I'm Saying NO To
${ans_avoid}

## Current Focus

### Top 3 Priorities
${ans_top_priorities}

### Active Projects
${ans_projects}

### This Quarter's Outcomes
${ans_outcomes_this_quarter}

### How I Measure Progress
${ans_how_measure}

---

## Using This Document

Your AI assistant uses this to:
- **Prioritize tasks** based on what aligns with your values and vision
- **Suggest daily work** that energizes rather than drains you
- **Flag imbalances** when one life area is getting neglected
- **Remind you** what you're saying NO to when new requests come in

**Review this weekly** and update as your priorities shift.

EOF

print_success "Created: GOALS.md"

# Final summary
print_header "Setup Complete!"

echo "Your Personal OS is ready to use."
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Review and refine GOALS.md"
echo "   - Edit any answers that need more thought"
echo "   - Add specifics as they become clear"
echo ""
echo "2. Start capturing in BACKLOG.md"
echo "   - Brain dump tasks, ideas, notes"
echo "   - No structure needed yet"
echo ""
echo "3. Tell your AI assistant:"
echo "   'Read CLAUDE.md and help me process my backlog'"
echo ""
echo "Your AI will use GOALS.md to prioritize work that aligns with"
echo "your values and keeps you balanced across life areas."
echo ""
print_success "Happy organizing!"
echo ""

#!/bin/bash

# Pre-Docker Build Validation Script
# This script runs all the checks that Docker build will perform
# Run this before "docker build" to catch issues early

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Project directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOJO_DIR="${PROJECT_ROOT}/apps/dojo"

echo -e "${BOLD}${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║         Pre-Docker Build Validation Script               ║${NC}"
echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d "$DOJO_DIR" ]; then
    echo -e "${RED}❌ Error: apps/dojo directory not found!${NC}"
    echo -e "Current directory: $PROJECT_ROOT"
    exit 1
fi

cd "$DOJO_DIR"
echo -e "${BLUE}📂 Working directory: $DOJO_DIR${NC}"
echo ""

# Function to print step header
print_step() {
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${BLUE}▶ $1${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Track overall status
OVERALL_STATUS=0
WARNINGS_COUNT=0

# Step 1: Check if dependencies are installed
print_step "Step 1/4: Checking Dependencies"
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  node_modules not found. Installing dependencies...${NC}"
    pnpm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install dependencies!${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi
echo ""

# Step 2: TypeScript Type Checking
print_step "Step 2/4: TypeScript Type Checking"
echo -e "${BLUE}Running: pnpm exec tsc --noEmit${NC}"
echo ""

if pnpm exec tsc --noEmit 2>&1 | tee /tmp/tsc-output.log; then
    echo ""
    echo -e "${GREEN}✅ TypeScript type checking passed!${NC}"
else
    echo ""
    echo -e "${RED}❌ TypeScript type checking failed!${NC}"
    echo -e "${YELLOW}Fix the errors above before proceeding.${NC}"
    OVERALL_STATUS=1
fi
echo ""

# Step 3: ESLint
print_step "Step 3/4: ESLint Checking"
echo -e "${BLUE}Running: pnpm run lint${NC}"
echo ""

LINT_OUTPUT=$(pnpm run lint 2>&1)
LINT_EXIT_CODE=$?

echo "$LINT_OUTPUT"

# Check for warnings vs errors
if echo "$LINT_OUTPUT" | grep -q "Warning:"; then
    WARNINGS_COUNT=$(echo "$LINT_OUTPUT" | grep -c "Warning:" || echo "0")
    echo ""
    echo -e "${YELLOW}⚠️  Found $WARNINGS_COUNT ESLint warnings (non-blocking)${NC}"
fi

if [ $LINT_EXIT_CODE -ne 0 ]; then
    if echo "$LINT_OUTPUT" | grep -q "Error:"; then
        echo ""
        echo -e "${RED}❌ ESLint found blocking errors!${NC}"
        OVERALL_STATUS=1
    else
        echo ""
        echo -e "${GREEN}✅ ESLint passed (warnings only)${NC}"
    fi
else
    echo ""
    echo -e "${GREEN}✅ ESLint passed!${NC}"
fi
echo ""

# Step 4: Next.js Build
print_step "Step 4/4: Next.js Production Build"
echo -e "${BLUE}Running: pnpm run build${NC}"
echo -e "${YELLOW}This may take 1-3 minutes...${NC}"
echo ""

if pnpm run build; then
    echo ""
    echo -e "${GREEN}✅ Next.js build completed successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Next.js build failed!${NC}"
    echo -e "${YELLOW}Check the errors above for details.${NC}"
    OVERALL_STATUS=1
fi
echo ""

# Final Summary
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${BLUE}                    FINAL SUMMARY${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ ALL CHECKS PASSED!${NC}"
    echo ""
    echo -e "${GREEN}Your code is ready for Docker build:${NC}"
    echo -e "${BLUE}  docker build -t your-image-name .${NC}"
    
    if [ $WARNINGS_COUNT -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}Note: $WARNINGS_COUNT warnings found (non-blocking)${NC}"
    fi
else
    echo -e "${RED}${BOLD}❌ CHECKS FAILED!${NC}"
    echo ""
    echo -e "${RED}Please fix the errors above before running Docker build.${NC}"
    echo -e "${YELLOW}Common fixes:${NC}"
    echo -e "  • Check TypeScript types"
    echo -e "  • Fix ESLint errors"
    echo -e "  • Review build output for specific errors"
fi

echo ""
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

exit $OVERALL_STATUS


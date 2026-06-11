#!/usr/bin/env bash

# Release script for ALIAS 2.0
# Automates checks, building the production bundle, tagging, and pushing to GitHub.

# Styling helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}       ALIAS - GITHUB RELEASE AUTOMATOR          ${NC}"
echo -e "${BLUE}==================================================${NC}"

# 1. Verification checks
echo -e "\n${YELLOW}[1/6] Running system & git checks...${NC}"

if ! command -v git &> /dev/null; then
    echo -e "${RED}[-] Error: Git is not installed or not in PATH.${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}[-] Error: Node.js / npm is not installed or not in PATH.${NC}"
    exit 1
fi

if [ ! -d ".git" ]; then
    echo -e "${RED}[-] Error: Not in a git repository root.${NC}"
    exit 1
fi

# Check git status
GIT_STATUS=$(git status --porcelain)
if [ ! -z "$GIT_STATUS" ]; then
    echo -e "${YELLOW}[!] Warning: You have uncommitted changes in your working directory:${NC}"
    echo "$GIT_STATUS"
    read -p "Do you want to proceed anyway? (y/n): " proceed
    if [[ ! $proceed =~ ^[Yy]$ ]]; then
        echo -e "${RED}[-] Release aborted.${NC}"
        exit 1
    fi
fi

# 2. Get new version tag
echo -e "\n${YELLOW}[2/6] Version Setup...${NC}"
# Read current version
CURRENT_VERSION=$(node -e "console.log(require('./frontend/package.json').version)")
echo -e "Current frontend version is: ${GREEN}$CURRENT_VERSION${NC}"

read -p "Enter new release version (e.g. 2.0.0): " VERSION
if [ -z "$VERSION" ]; then
    echo -e "${RED}[-] Error: Version cannot be empty.${NC}"
    exit 1
fi

# Strip 'v' prefix if user typed it (we tag with v$VERSION)
VERSION=${VERSION#v}

# 3. Update package.json version
echo -e "\n${YELLOW}[3/6] Updating package.json version to $VERSION...${NC}"
node -e "
const fs = require('fs');
const path = './frontend/package.json';
const pkg = JSON.parse(fs.readFileSync(path, 'utf8'));
pkg.version = '$VERSION';
fs.writeFileSync(path, JSON.stringify(pkg, null, 2) + '\n');
"
echo -e "${GREEN}[+] package.json updated successfully.${NC}"

# Commit the version bump
git add frontend/package.json
git commit -m "bump: version to $VERSION for release" &> /dev/null || true

# 4. Build frontend and Electron production app
echo -e "\n${YELLOW}[4/6] Building production Electron application...${NC}"
echo -e "Installing dependencies..."
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo -e "${RED}[-] Error: npm install failed.${NC}"
    exit 1
fi

echo -e "Compiling and packaging binary..."
npm run electron:build
if [ $? -ne 0 ]; then
    echo -e "${RED}[-] Error: Electron build failed.${NC}"
    exit 1
fi
cd ..

# 5. Create Git Tag
echo -e "\n${YELLOW}[5/6] Creating git tag v$VERSION...${NC}"
git tag -a "v$VERSION" -m "Release version v$VERSION"
if [ $? -ne 0 ]; then
    echo -e "${RED}[-] Error: Failed to create git tag.${NC}"
    exit 1
fi
echo -e "${GREEN}[+] Tag v$VERSION created successfully.${NC}"

# 6. Push to GitHub
echo -e "\n${YELLOW}[6/6] Pushing code and tags to GitHub...${NC}"
echo -e "Pushing commits..."
git push origin main
if [ $? -ne 0 ]; then
    echo -e "${RED}[-] Warning: Failed to push to remote 'main' branch.${NC}"
fi

echo -e "Pushing tags..."
git push origin --tags
if [ $? -ne 0 ]; then
    echo -e "${RED}[-] Error: Failed to push tags.${NC}"
    exit 1
fi

echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}  SUCCESS: ALIAS v$VERSION RELEASED SUCCESSFULLY!  ${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "The code and tag v$VERSION have been pushed to GitHub."
echo -e "You can draft a release page on GitHub using the tag."

# Git CLI Tutorial - Complete Guide

A comprehensive guide for managing the Modular MCP repository using Git command line interface.

## 📚 Table of Contents

1. [Initial Setup](#initial-setup)
2. [Creating New Repository](#creating-new-repository)
3. [Cloning Repository](#cloning-repository)
4. [Branch Management](#branch-management)
5. [Making Changes](#making-changes)
6. [Pushing Changes](#pushing-changes)
7. [Pulling Updates](#pulling-updates)
8. [Advanced Operations](#advanced-operations)
9. [Troubleshooting](#troubleshooting)

## 🚀 Initial Setup

### Configure Git (First Time Only)
```bash
# Set your name and email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Set default branch name
git config --global init.defaultBranch main

# Optional: Set default editor
git config --global core.editor "nano"

# Verify configuration
git config --list
```

### Authentication Setup
```bash
# For HTTPS (recommended for personal access tokens)
git config --global credential.helper store

# When prompted, use your GitHub username and Personal Access Token as password
```

## 📦 Creating New Repository

### Method 1: GitHub Web Interface + Local
```bash
# 1. Create repository on GitHub.com
# 2. Clone the empty repository
git clone https://github.com/alwazw/repository-name.git
cd repository-name

# 3. Add files and make initial commit
echo "# Repository Name" >> README.md
git add README.md
git commit -m "Initial commit"
git push -u origin main
```

### Method 2: Local First + GitHub
```bash
# 1. Initialize local repository
mkdir my-project
cd my-project
git init

# 2. Add files and commit
echo "# My Project" >> README.md
git add .
git commit -m "Initial commit"

# 3. Create repository on GitHub, then add remote
git remote add origin https://github.com/alwazw/my-project.git
git branch -M main
git push -u origin main
```

### Method 3: Using GitHub CLI
```bash
# Install GitHub CLI first: https://cli.github.com/
gh repo create my-project --public --clone
cd my-project
# Add files and commit as usual
```

## 📥 Cloning Repository

### Basic Clone
```bash
# Clone the modular_mcp repository
git clone https://github.com/alwazw/modular_mcp.git
cd modular_mcp
```

### Clone Specific Branch
```bash
# Clone only a specific branch
git clone -b branch-name https://github.com/alwazw/modular_mcp.git
```

### Shallow Clone (Faster)
```bash
# Clone only recent history (faster for large repos)
git clone --depth 1 https://github.com/alwazw/modular_mcp.git
```

## 🌿 Branch Management

### Creating Branches
```bash
# Create and switch to new branch
git checkout -b feature/new-agent
# or
git switch -c feature/new-agent

# Create branch from specific commit
git checkout -b hotfix/bug-fix abc1234
```

### Switching Branches
```bash
# Switch to existing branch
git checkout main
git checkout feature/new-agent
# or
git switch main
git switch feature/new-agent
```

### Listing Branches
```bash
# List local branches
git branch

# List all branches (local + remote)
git branch -a

# List remote branches only
git branch -r
```

### Deleting Branches
```bash
# Delete local branch (safe - prevents deletion if unmerged)
git branch -d feature/completed-feature

# Force delete local branch
git branch -D feature/abandoned-feature

# Delete remote branch
git push origin --delete feature/old-branch
```

## ✏️ Making Changes

### Checking Status
```bash
# Check current status
git status

# Check differences
git diff                    # Unstaged changes
git diff --staged          # Staged changes
git diff HEAD              # All changes
```

### Staging Changes
```bash
# Stage specific files
git add file1.py file2.js

# Stage all changes
git add .
git add -A

# Stage parts of a file interactively
git add -p filename.py

# Unstage files
git reset HEAD filename.py
git restore --staged filename.py
```

### Committing Changes
```bash
# Commit with message
git commit -m "Add new agent functionality"

# Commit with detailed message
git commit -m "Add new agent functionality

- Implement web scraping capabilities
- Add error handling for network timeouts
- Update documentation"

# Commit all tracked changes (skip staging)
git commit -am "Quick fix for bug"

# Amend last commit
git commit --amend -m "Updated commit message"
```

## 📤 Pushing Changes

### Push to Remote
```bash
# Push current branch to origin
git push

# Push and set upstream (first time)
git push -u origin feature/new-branch

# Push specific branch
git push origin main
git push origin feature/new-branch

# Push all branches
git push --all origin

# Push tags
git push --tags
```

### Force Push (Use Carefully!)
```bash
# Force push (overwrites remote history)
git push --force origin main

# Safer force push (fails if someone else pushed)
git push --force-with-lease origin main
```

## 📥 Pulling Updates

### Basic Pull Operations
```bash
# Pull latest changes from current branch
git pull

# Pull from specific remote/branch
git pull origin main

# Pull and rebase instead of merge
git pull --rebase origin main
```

### Fetch vs Pull
```bash
# Fetch updates without merging
git fetch origin

# See what's new
git log HEAD..origin/main

# Then merge manually
git merge origin/main
```

### Pull Specific Files Only
```bash
# This isn't directly possible, but you can:
# 1. Fetch updates
git fetch origin

# 2. Checkout specific files from remote
git checkout origin/main -- path/to/specific/file.py
```

## 🔄 Advanced Operations

### Moving Main to Branch / Creating Fork

#### Save Current Main as Branch
```bash
# Create branch from current main
git checkout main
git checkout -b backup/old-main
git push -u origin backup/old-main

# Reset main to clean state
git checkout main
git reset --hard origin/main
```

#### Copy Main to New Branch
```bash
# Create new branch from main
git checkout main
git checkout -b development
git push -u origin development

# Now you have main and development with same content
```

#### Clear Main for New Content
```bash
# Create orphan branch (no history)
git checkout --orphan new-main
git rm -rf .
echo "# New Clean Start" > README.md
git add README.md
git commit -m "Fresh start"

# Replace old main
git branch -D main
git branch -m new-main main
git push -f origin main
```

### Merging and Rebasing
```bash
# Merge branch into current branch
git merge feature/new-agent

# Rebase current branch onto main
git rebase main

# Interactive rebase (squash/edit commits)
git rebase -i HEAD~3
```

### Stashing Changes
```bash
# Stash current changes
git stash
git stash push -m "Work in progress"

# List stashes
git stash list

# Apply stash
git stash apply
git stash apply stash@{1}

# Pop stash (apply and remove)
git stash pop

# Drop stash
git stash drop stash@{1}
```

### Cherry-picking
```bash
# Apply specific commit to current branch
git cherry-pick abc1234

# Cherry-pick multiple commits
git cherry-pick abc1234 def5678

# Cherry-pick without committing
git cherry-pick --no-commit abc1234
```

## 🔍 Viewing History

### Log Commands
```bash
# Basic log
git log

# One line per commit
git log --oneline

# Graphical representation
git log --graph --oneline --all

# Show changes in commits
git log -p

# Show specific number of commits
git log -n 5

# Show commits by author
git log --author="alwazw"

# Show commits in date range
git log --since="2024-01-01" --until="2024-12-31"
```

### Blame and Show
```bash
# Show who changed each line
git blame filename.py

# Show specific commit details
git show abc1234

# Show changes in specific commit
git show abc1234 --name-only
```

## 🏷️ Tags

### Creating Tags
```bash
# Lightweight tag
git tag v1.0.0

# Annotated tag (recommended)
git tag -a v1.0.0 -m "Version 1.0.0 release"

# Tag specific commit
git tag -a v1.0.0 abc1234 -m "Version 1.0.0"
```

### Managing Tags
```bash
# List tags
git tag
git tag -l "v1.*"

# Push tags
git push origin v1.0.0
git push --tags

# Delete tag
git tag -d v1.0.0
git push origin --delete v1.0.0
```

## 🔧 Configuration

### Repository-specific Config
```bash
# Set config for current repository only
git config user.name "Project Specific Name"
git config user.email "project@email.com"

# View repository config
git config --list --local
```

### Useful Aliases
```bash
# Create shortcuts
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'
git config --global alias.visual '!gitk'

# Now you can use: git st, git co, git br, etc.
```

## 🚨 Troubleshooting

### Common Issues and Solutions

#### Merge Conflicts
```bash
# When merge conflict occurs:
# 1. Edit conflicted files manually
# 2. Stage resolved files
git add conflicted-file.py

# 3. Complete merge
git commit
```

#### Undo Changes
```bash
# Undo unstaged changes
git checkout -- filename.py
git restore filename.py

# Undo staged changes
git reset HEAD filename.py
git restore --staged filename.py

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Undo specific commit (creates new commit)
git revert abc1234
```

#### Authentication Issues
```bash
# Update stored credentials
git config --global credential.helper store
# Then push/pull to re-enter credentials

# Use token authentication
# Username: your-github-username
# Password: your-personal-access-token
```

#### Large File Issues
```bash
# Remove large file from history
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch large-file.zip' \
--prune-empty --tag-name-filter cat -- --all

# Force push to update remote
git push --force --all origin
```

## 📋 Quick Reference Commands

### Daily Workflow
```bash
# Start work
git pull origin main
git checkout -b feature/my-feature

# Make changes
git add .
git commit -m "Implement feature"

# Push work
git push -u origin feature/my-feature

# Update from main
git checkout main
git pull origin main
git checkout feature/my-feature
git merge main

# Finish feature
git checkout main
git merge feature/my-feature
git push origin main
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```

### Emergency Commands
```bash
# Abort merge
git merge --abort

# Abort rebase
git rebase --abort

# Abort cherry-pick
git cherry-pick --abort

# Reset to remote state
git reset --hard origin/main

# Clean untracked files
git clean -fd
```

## 🎯 Best Practices

### Commit Messages
```bash
# Good commit message format:
# <type>(<scope>): <subject>
#
# <body>
#
# <footer>

# Examples:
git commit -m "feat(agent): add web scraping functionality"
git commit -m "fix(docker): resolve container startup issue"
git commit -m "docs(readme): update installation instructions"
```

### Branch Naming
```bash
# Use descriptive names
feature/user-authentication
bugfix/memory-leak-fix
hotfix/security-patch
docs/api-documentation
refactor/database-layer
```

### Workflow Tips
- Always pull before starting new work
- Use branches for features and fixes
- Write descriptive commit messages
- Test before pushing
- Review changes before committing
- Keep commits focused and atomic
- Use `.gitignore` for unwanted files

---

## 📞 Need Help?

- **Git Documentation**: https://git-scm.com/doc
- **GitHub Guides**: https://guides.github.com/
- **Interactive Git Tutorial**: https://learngitbranching.js.org/
- **Git Cheat Sheet**: https://education.github.com/git-cheat-sheet-education.pdf

**Remember**: Git is powerful but can be complex. When in doubt, make a backup branch before trying advanced operations!


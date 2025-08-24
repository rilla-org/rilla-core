# Contributing to Rilla

First off, thank you for considering contributing to Rilla! It’s people like you that make open source great. This document will guide you through setting up your development environment and making your first contribution.

## 1. Prerequisites

Before you begin, please make sure you have the following software installed:
- [Git](https://git-scm.com/)
- [Python 3.10+](https://www.python.org/)
- [Visual Studio Code](https://code.visualstudio.com/) (Recommended)
- A [GitHub Account](https://github.com/)

## 2. Initial Setup: Fork, Clone, and Configure

To work on Rilla, you will need your own copy of the repository.

### Step 2.1: Fork the Repository
Fork the `rilla-org/rilla-core` repository by clicking the "Fork" button in the top-right corner of the GitHub page. This creates a copy of the project under your own GitHub account.

### Step 2.2: Clone Your Fork
Clone your fork to your local machine. We strongly recommend using SSH for cloning.
- [Configuring an SSH key for GitHub](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)
```bash
git clone git@github.com:YOUR-USERNAME/rilla-core.git
cd rilla-core
```

### Step 2.3: Set up GPG for Signed Commits
Our project requires all commits to be cryptographically signed to verify their origin.
- [Generating a new GPG key](https://docs.github.com/en/authentication/managing-commit-signature-verification/generating-a-new-gpg-key)
- [Adding the GPG key to your GitHub account](https://docs.github.com/en/authentication/managing-commit-signature-verification/adding-a-new-gpg-key-to-your-github-account)
- [Telling Git about your signing key](https://docs.github.com/en/authentication/managing-commit-signature-verification/telling-git-about-your-signing-key)

### Step 2.4: Configure your Git Email
To avoid privacy errors when pushing, configure your local Git to use your GitHub-provided `noreply` email. You can find this in your [GitHub email settings](https://github.com/settings/emails).
```bash
git config --global user.email "ID+username@users.noreply.github.com"
##3. Setting Up the Python Environment
We use a virtual environment to manage project dependencies.

```Bash
# Create the virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate

# Activate it (macOS/Linux)
source venv/bin/activate

# Install the required libraries
pip install PySide6
```
## 4. Running the Application
Once set up, you can run the application from the root directory of the project:
code
```Bash
python src/main.py
```
## 5. The Development Workflow
All changes must be made through branches and pull requests.
1. Create a Branch: Create a new branch for your feature or bugfix.
2. Commit Your Changes: Make your changes and commit them with a clear message.
3. Push Your Branch: Push the branch to your fork on GitHub.
4. Open a Pull Request: From your fork on GitHub, open a pull request to the main branch of `rilla-org/rilla-core.`
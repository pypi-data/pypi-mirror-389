# Stiggy

A Python framework for scalable, structured software engineering.

## Setup on development machine

```bash


mkdir -p ~/projects/public/exida-oss/stiggy
cd ~/projects/public/exida-oss/stiggy
git clone git@gitlab.com:exida-oss/stiggy/stiggy.git
cd stiggy/scripts


./setup.sh
./build.sh
```


## Set up pycharm

1. In pycharm, open ~/projects/public/exida-oss/stiggy/stiggy/
2. When asked about poetry executable, select the proposed one (in .local folder). Note: we do not select python executable nor .venv.
3. In Pycharm console, cd scripts and ./build.sh
4. Create a new branch, push your changes, create merge request.


## 7. A shorthand to run all during development

```bash
poetry lock && poetry install && poetry run pytest && poetry run stiggy export config/PTH_safety_analyses/DCDCSW_cluster_safety_analysis.yaml

```



## 🚀 Connecting existing project to new GitLab project - instructions for new project creation from template

```bash

# Step 1: Rename 'master' to 'main' (if not already done)
git branch -m master main

# Step 2: Add GitLab remote (adjust if not yet added)
git remote add origin git@gitlab.com:exida/STIG/stiggy.git

# Step 3: Pull remote main branch with rebase
git fetch origin
git pull --rebase origin main

# Step 4: Push your rebased local 'main' to GitLab and set tracking
git push -u origin main

```

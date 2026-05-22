# GitHub repository

**Remote:** https://github.com/kirtquist/service-app  
**Default branch:** `main`

The repository is live. Use this doc for clone, push, and branch workflow.

## Clone

```bash
git clone https://github.com/kirtquist/service-app.git
cd service-app
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env
# Set OPENROUTER_API_KEY in .env
```

## Push changes to `main`

From the repo root:

```bash
git status
git add -A
git commit -m "Your message"
git push origin main
```

For now, work may land directly on `main`. Once active development starts, prefer a `dev` branch and PRs into `main`.

## Create a `dev` branch (when ready)

```bash
git checkout -b dev
git push -u origin dev
```

## GitHub CLI (optional)

If `gh` is not installed (Debian/Ubuntu):

```bash
type -p curl >/dev/null || sudo apt install curl -y
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh -y
gh auth login
```

## CI secrets

When you add GitHub Actions, configure repository secrets (e.g. `OPENROUTER_API_KEY`). See [`API_KEYS.md`](API_KEYS.md).

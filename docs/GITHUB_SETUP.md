# Create the GitHub repository

The project is initialized on branch **`main`** with an initial commit. `gh` is not available in this environment, so finish setup locally:

## 1. Install the GitHub CLI (WSL / Debian/Ubuntu)

```bash
type -p curl >/dev/null || sudo apt install curl -y
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh -y
```

## 2. Authenticate

```bash
gh auth login
```

## 3. Create and push `kirtquist/service-app`

From the repo root (`service-app/`):

```bash
gh repo create kirtquist/service-app --public --source=. --remote=origin --push
```

If the remote already exists (e.g. you ran `git remote add`), use instead:

```bash
git remote add origin https://github.com/kirtquist/service-app.git   # omit if gh added it
git push -u origin main
```

## Alternative (no CLI)

Create an empty **`kirtquist/service-app`** repo in the GitHub UI, then:

```bash
git remote add origin https://github.com/kirtquist/service-app.git
git push -u origin main
```

Remember to **configure repository secrets** (e.g. `OPENROUTER_API_KEY`) for CI when you add workflows.

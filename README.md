# Auto-Deploy GitHub Webhook Server

Automatically update and restart your Python-hosted static website every time you push to GitHub.

---

## How It Works

```
Your PC          GitHub            Your Server
  │                │                    │
  │── git push ──▶│                    │
  │                │── POST /webhook ─▶│
  │                │                    │── git fetch + reset
  │                │                    │── server restarts
  │                │                    │── new site is live ✓
```

Three components work together:

| File | Location on Server | Purpose |
|---|---|---|
| `server.py` | Inside your repo | Serves your website + handles webhook |
| `launcher.py` | Outside your repo | Restarts server.py after every update |
| `gitdeploy.service` | `/etc/systemd/system/` | Runs everything on boot |

The trick is that `launcher.py` lives **outside** your repo so it never gets overwritten by `git pull`. It watches `server.py` and restarts it whenever it exits — which `server.py` does automatically after a successful git pull.

---

## Requirements

- Ubuntu / Debian Linux server
- Python 3
- Git installed (`sudo apt install git`)
- A GitHub repository with your website files and `server.py` included
- A Cloudflare Tunnel (or open port) pointing to port 5000

---

## Setup

### 1. Clone Your Repo

```bash
sudo mkdir -p /var/www
sudo git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git /var/www/YOUR_REPO
sudo chown -R $USER:$USER /var/www
```

### 2. Place `launcher.py` Outside the Repo

```bash
cp launcher.py /var/www/launcher.py
```

Then open it and set the path to your repo:

```python
REPO_DIR = "/var/www/YOUR_REPO"
SERVER_SCRIPT = "/var/www/YOUR_REPO/server.py"
```

### 3. Generate a Webhook Secret

Run this on your server to generate a secure random secret:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output — you'll need it in the next two steps.

### 4. Create the `.env` File

This keeps your secret outside the repo so it never gets overwritten by git:

```bash
nano /var/www/.env
```

Add this line:

```
WEBHOOK_SECRET=your_generated_secret_here
```

Save with `Ctrl+X`, `Y`, `Enter`.

### 5. Add `server.py` to Your Repo

Copy `server.py` into your website repo and push it to GitHub:

```bash
cp server.py /var/www/YOUR_REPO/
cd /var/www/YOUR_REPO
git add server.py
git commit -m "add auto-deploy server"
git push
```

### 5.1. Update the Repository Directory in `server.py`

Now you need to configure `server.py` with your repository's directory. Edit the file you just copied:

```bash
nano /var/www/YOUR_REPO/server.py
```

Find this line near the top:

```python
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
```

If you want to use the default behavior (serves from the repo root), you can leave it as is. However, if you need to customize it, change it to your repo's directory:

```python
REPO_DIR = "/var/www/YOUR_REPO"
```

Save with `Ctrl+X`, `Y`, `Enter`. Then commit and push this change:

```bash
git add server.py
git commit -m "configure repo directory"
git push
```

### 6. Add `.env` to `.gitignore`

Make sure your secret never gets accidentally committed:

```bash
echo ".env" >> /var/www/YOUR_REPO/.gitignore
git add .gitignore
git commit -m "ignore .env"
git push
```

### 7. Install the Systemd Service

Copy the service file to systemd:

```bash
sudo cp gitdeploy.service /etc/systemd/system/gitdeploy.service
```

Then enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable gitdeploy
sudo systemctl start gitdeploy
```

Check it's running:

```bash
sudo systemctl status gitdeploy
```

You should see `active (running)`.

### 8. Set Up the GitHub Webhook

1. Go to your repo on GitHub → **Settings → Webhooks → Add webhook**
2. Fill in:
   - **Payload URL:** `https://yourdomain.com/webhook`
   - **Content type:** `application/json`
   - **Secret:** the secret you generated in step 3
   - **Events:** Just the push event
3. Click **Add webhook**

GitHub will send a test ping. Check **Recent Deliveries** on the webhook page — it should show a green checkmark.

---

## Customization

### Change the Port

In `server.py`, change:

```python
PORT = 5000
```

### Change the Branch

By default only pushes to `main` trigger a deploy. To use a different branch, edit `server.py`:

```python
if branch != "refs/heads/main":
```

### Serve From a Subdirectory

By default `server.py` serves from the root of your repo. To serve from a subfolder like `public/`:

```python
REPO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
```

---

## Monitoring & Logs

Watch live logs:

```bash
sudo journalctl -fu gitdeploy
```

Restart manually:

```bash
sudo systemctl restart gitdeploy
```

Stop the server:

```bash
sudo systemctl stop gitdeploy
```

---

## Troubleshooting

**404 on the website**
Run `sudo journalctl -fu gitdeploy` and check the `[server] Serving from` line — it should point to your repo folder. If not, check the `REPO_DIR` path in `server.py`.

**Webhook returns 403**
Your secret in `/var/www/.env` doesn't match what you entered on GitHub. Double-check both are identical with no extra spaces.

**Git pull fails with "local changes would be overwritten"**
The server uses `git reset --hard origin/main` to force-overwrite local changes. If it's still failing, run manually:
```bash
cd /var/www/YOUR_REPO
git fetch --all
git reset --hard origin/main
```

**Service won't start**
Check the `EnvironmentFile` path in `gitdeploy.service` points to `/var/www/.env` and that file exists.

---

## File Structure

```
/var/www/
├── .env                  ← your webhook secret (never commit this)
├── launcher.py           ← restarts server on update (never in repo)
└── YOUR_REPO/
    ├── .gitignore        ← includes .env
    ├── server.py         ← web server + webhook handler
    ├── index.html
    └── ...               ← rest of your website files
```

---

## License

MIT — use it however you want.

# GitHub Actions daily job (6 AM Pacific)

Runs the same pipeline as `apex_daily_manual.sh`:

1. `python3 apex_dashboard_builder.py`
2. Commit + push `apex_dashboard_data.json`
3. `python3 apex_last_night_pdf_email.py` (PDF + SMTP email)

Works when your Mac is off. Schedule: **6:00 AM America/Los_Angeles**.

## One-time setup

### 1. Push this repo (including `client_lists/` and `.github/workflows/apex_daily.yml`)

The builder reads:

- `client_lists/Client List - 04-15-26.xlsx`
- `client_lists/AmateurList.xlsx`
- `client_lists/HSList.xlsx`

Optional Desktop tracker workbooks are skipped in CI if missing.

### 2. Add **repository** secrets (required for email)

**Settings → Secrets and variables → Actions → Repository secrets → New repository secret**

Use **Actions** tab secrets on `colbymorris08/apexstats-dashboard`, not Dependabot or Codespaces.  
Your Mac file `~/.apexstats_morning_email.env` is **not** read by GitHub — copy the same values into secrets below.

| Secret | Example |
|--------|---------|
| `APEX_SMTP_HOST` | `smtp.gmail.com` |
| `APEX_SMTP_PORT` | `587` |
| `APEX_SMTP_USER` | your Gmail |
| `APEX_SMTP_PASSWORD` | 16-char Gmail App Password |
| `APEX_PDF_EMAIL_FROM` | same as SMTP user |
| `APEX_PDF_EMAIL_TO` | `you@example.com,other@example.com` |
| `APEX_SMTP_USE_SSL` | `1` only if using port 465 |

If email secrets are missing, the workflow still updates the site JSON; the email step is marked `continue-on-error`.

### 3. Enable Actions

**Settings → Actions → General** → allow Actions for this repository.

### 4. Test manually

**Actions → Apex daily → Run workflow**

## Logs

Open the workflow run in the **Actions** tab for build errors (NCAA timeouts, missing files, etc.).

## Mac LaunchAgent

You can keep the local 6 AM job as a backup or disable it after Actions is stable:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.colbymorris.apexdashboard.morning.plist
```

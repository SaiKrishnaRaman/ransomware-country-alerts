# Ransomware Country Alerts

Emails you when a ransomware group claims a new victim in your country, using
the free ransomware.live API. Runs on GitHub Actions, so you don't need a server.

## Setup
1. Click **Use this template → Create a new repository** and make it **private**.
2. In your copy, open Settings → Secrets and variables → Actions → **Secrets** and add:
   - `SMTP_USER`: sending email address
   - `SMTP_PASS`: an app password, not your normal password
   - `ALERT_TO`: recipients, comma-separated
3. Under the **Variables** tab, add:
   - `COUNTRY`: ISO-2 code, e.g. `AE`, `US`, `GB`
   - `SMTP_HOST`: e.g. `smtp.gmail.com` (default) or `smtppro.zoho.com`
4. Open the Actions tab, enable workflows, and run the workflow once.
   The first run silently records existing victims. Alerts start after that.

## Notes
- The free API is for personal, non-commercial use. Organisations should use the ransomware.live Pro API.
- Data and screenshots come from ransomware.live.
- GitHub pauses scheduled workflows after 60 days without repo activity.
- Never commit credentials. Use Secrets only.

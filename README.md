
# 🛡️ Ransomware Country Alerts

**Get an email the moment a ransomware group claims a victim in your country.**

Serverless, free to run, and set up in about five minutes.

---

## ✨ What it does

Ransomware groups publish stolen-data claims on leak sites. [ransomware.live](https://www.ransomware.live) tracks them and exposes a free API. This project polls that API every 30 minutes, filters by **your country**, and emails you about each **new** claim.

Each alert includes:

- 🏢 Victim name and website
- 👤 Ransomware group behind the claim
- 📅 Published and discovery dates
- 🏭 Sector, where known
- 📝 The group's own description of the claim
- 🖼️ A screenshot of the leak-site post, embedded in the email

## 🧩 How it works

```
GitHub Actions (every 30 min)
        │
        ▼
ransomware.live API ──► filter by COUNTRY ──► compare with seen_victims.json
                                                        │
                                          new claims? ──┤
                                                        ▼
                                          HTML email via your SMTP account
                                                        │
                                                        ▼
                                  seen_victims.json committed back to the repo
```

- **No server needed.** GitHub runs everything for you.
- **No duplicate alerts.** Each claim is recorded once it has been emailed.
- **No lost alerts.** If your mail server is down, the claim is retried on the next run instead of being skipped.
- **No flood on day one.** The first run silently records existing victims, and alerts start from then on.

## 🚀 Quick start

### 1. Create your own copy

Click **Use this template → Create a new repository**, and set it to **Private**.

### 2. Add your secrets

In your copy, go to **Settings → Secrets and variables → Actions → Secrets** and add:

| Secret | Value |
|---|---|
| `SMTP_USER` | The email address alerts are sent from |
| `SMTP_PASS` | An **app password** (not your normal password) |
| `ALERT_TO` | Who receives alerts. Separate several addresses with commas |

### 3. Add your variables

On the **Variables** tab in the same page, add:

| Variable | Value |
|---|---|
| `COUNTRY` | Two-letter country code, e.g. `AE`, `US`, `GB`, `IN` |
| `SMTP_HOST` | Your mail server (see the table below). Defaults to Gmail if unset |

### 4. Run it

Open the **Actions** tab, enable workflows, select **Ransomware Alert Monitor**, and click **Run workflow**.

The first run records the current victims without sending any email. From then on, you'll be alerted about new claims.

## 📬 Email provider settings

You can use any email provider that offers **SMTP over SSL on port 465**, which the script uses.

| Provider | `SMTP_HOST` | Notes |
|---|---|---|
| Gmail (default) | `smtp.gmail.com` | Needs 2-Step Verification and an [app password](https://myaccount.google.com/apppasswords) |
| Yahoo | `smtp.mail.yahoo.com` | Needs an app password from your account security settings |
| Your own domain or another provider | your provider's SMTP hostname | Look for "SMTP server" in your provider's help pages |

Tips for any provider:

- Enter the hostname only, such as `smtp.example.com`, with no `https://` and no port.
- Use an **app password** if your provider offers them, rather than your main password.
- `SMTP_USER` is normally your full email address.
- Some providers only offer port 587 (STARTTLS) and not 465. Those aren't supported without a small code change.

## ⚙️ Configuration

| Name | Type | Required | Default | Purpose |
|---|---|---|---|---|
| `SMTP_USER` | Secret | ✅ | none | Login and sender address |
| `SMTP_PASS` | Secret | ✅ | none | App password |
| `ALERT_TO` | Secret | ✅ | `SMTP_USER` | Comma-separated recipients |
| `COUNTRY` | Variable | ➖ | `AE` | ISO-2 country code to monitor |
| `SMTP_HOST` | Variable | ➖ | `smtp.gmail.com` | SMTP server hostname |

To change how often it runs, edit the `cron` line in `.github/workflows/alert.yml`. Every 30 minutes is a safe default.

## 🧪 Testing your setup

1. Run the workflow once to create the baseline. This creates `seen_victims.json`.
2. Open `seen_victims.json`, click the pencil icon, and delete one whole line from the **middle** of the list, including its comma. Commit the change.
3. Run the workflow again. That claim now looks new, so you should receive an alert.

## 🔧 Troubleshooting

Open the run in the **Actions** tab, click the job, then expand **Run monitor**. A green tick doesn't guarantee an email was sent, so read the last lines of that log.

| Log message | Likely cause and fix |
|---|---|
| `Email sent: ...` | Delivered. Check spam, and make sure your domain has SPF and DKIM set up |
| `535 Authentication Failed` | Wrong app password, wrong `SMTP_USER`, or wrong SMTP host for your account type or region |
| `Name or service not known` | `SMTP_HOST` is mistyped. Use the hostname only, with no `https://` and no port |
| `SMTP_USER / SMTP_PASS secrets are not set` | A secret is missing or misspelled |
| `Rate limited ... (429)` | The free API allows one request per minute. The next scheduled run retries automatically |
| `Run complete. 0 new victim(s)` | Nothing new since the last run |

## 🔒 Security notes

- Keep your copy **private** and store credentials only in **GitHub Secrets**. Never commit passwords.
- Use an **app password** rather than your main account password, and revoke it if it's ever exposed.
- Leak-post URLs point to `.onion` addresses. They're shown as plain text in the email on purpose so nobody opens one by accident.
- Screenshots are loaded from `images.ransomware.live` when you open the email.

## ❓ FAQ

**Is it free?**
Yes. GitHub Actions includes free minutes for private repos, and this job takes only a few seconds per run.

**Can several people get the alerts?**
Yes. Put every address in `ALERT_TO`, separated by commas.

**Can I monitor more than one country?**
Not out of the box. The simplest way is to create one copy of the template per country.

**Why did my alerts stop after a few months?**
GitHub pauses scheduled workflows on repos with no activity for 60 days. Re-enable the workflow in the Actions tab. The state file commits usually keep the repo active.

## ⚖️ Data source and disclaimer

All data and screenshots come from [ransomware.live](https://www.ransomware.live). Please respect their [terms](https://www.ransomware.live/t&c):

- The free API is intended for **personal, non-commercial use**. Organisations should use their Pro API.
- This project does not access, download, or host any stolen data. It reads only the public listings and metadata that ransomware.live publishes.
- Alerts are provided for awareness and defensive purposes. A claim by a ransomware group is **not** confirmation that a breach occurred.

## 🤝 Contributing

Ideas and pull requests are welcome, for example Slack or Telegram delivery, multi-country support, or sector filters. Please open an issue first for larger changes.

## 📄 License

Released under the [MIT License](LICENSE).

---

# Unattended daily delivery on Windows

The `workflow run-scheduled` command generates one personalized newsletter for every enabled subscriber, automatically approves it, and sends it through SMTP. Premium LLM failures use the deterministic fallback. A failure for one subscriber does not stop delivery to the others.

This deliberately requires two private settings in the Git-ignored `.env`:

```dotenv
VORTENIX_EMAIL_PROVIDER=smtp
VORTENIX_ALLOW_AUTOMATIC_SEND=true
```

Keep the SMTP username and app password in that same `.env`. Do not put secrets in the PowerShell script or Task Scheduler arguments.

## Create the 8:00 AM task

Open **Task Scheduler**, select **Create Task**, and use:

- **General:** `Vortenix Daily Newsletter`; select **Run whether user is logged on or not**.
- **Trigger:** Daily at `08:00:00`, enabled.
- **Action / Program:** `powershell.exe`
- **Arguments:** `-NoProfile -ExecutionPolicy Bypass -File "C:\Anish\ai-projects\Vortenix\scripts\run_scheduled_newsletters.ps1"`
- **Start in:** `C:\Anish\ai-projects\Vortenix`
- **Conditions:** enable **Wake the computer to run this task** if appropriate; require a network connection.
- **Settings:** enable **Run task as soon as possible after a scheduled start is missed** and prevent overlapping instances.

The schedule uses the Windows machine's local timezone. The PC must be on (or able to wake), connected to the internet, and able to access the repository and `.env` at 8:00 AM.

Test the task using Task Scheduler's **Run** action. This performs real delivery to every enabled subscriber.

## GitHub Actions (recommended for cloud scheduling)

The workflow `.github/workflows/daily-newsletter.yml` runs every day at 8:00 AM in the `Europe/Dublin` timezone and can also be started manually. Scheduled workflows run from the repository's default branch, so merge the workflow before expecting the schedule to start.

Create these repository secrets under **Settings → Secrets and variables → Actions**:

- `SMTP_USERNAME`: Gmail account used to send.
- `SMTP_PASSWORD`: Gmail app password, not the normal account password.
- `SMTP_FROM_EMAIL`: sender Gmail address.
- `OPENAI_API_KEY`: optional for premium research; failures fall back to deterministic research.
- `VORTENIX_SUBSCRIBERS_B64`: Base64 representation of `config/subscribers.local.yaml`.

From an authenticated PowerShell session, the subscriber secret can be created without printing its contents:

```powershell
$subscriberBytes = [System.IO.File]::ReadAllBytes("config/subscribers.local.yaml")
$subscriberSecret = [Convert]::ToBase64String($subscriberBytes)
$subscriberSecret | gh secret set VORTENIX_SUBSCRIBERS_B64
```

The workflow grants its GitHub token read-only repository access, prevents overlapping newsletter runs, reconstructs the ignored subscriber file only on the temporary runner, and removes it in an `always()` cleanup step. Do not place private values directly in the workflow YAML.

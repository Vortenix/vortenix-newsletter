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

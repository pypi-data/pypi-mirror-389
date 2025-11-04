<div align="center">

# APT Toolkit

**Advanced Persistent Threat offensive simulation toolkit for authorized operators**

![status](https://img.shields.io/badge/status-beta-orange) ![python](https://img.shields.io/badge/python-3.8%2B-blue)

</div>

---

## ⚠️ Legal & Ethical Notice

The APT Toolkit is provided solely for **authorized penetration testing, security research, and educational purposes**.  
You must obtain explicit permission before targeting any network, system, or organization.  
Unauthorized access is illegal and unethical. The maintainers assume **no liability** for misuse.

---

## Table of Contents

1. [Overview](#overview)
2. [Feature Matrix](#feature-matrix)
3. [Installation](#installation)
4. [Configuration & Persistent Settings](#configuration--persistent-settings)
5. [Launching the Interactive Shell](#launching-the-interactive-shell)
6. [Command Reference & Usage Guides](#command-reference--usage-guides)  
   6.1 [Configuration Commands](#61-configuration-commands)  
   6.2 [Initial Access](#62-initial-access)  
   6.3 [Lateral Movement](#63-lateral-movement)  
   6.4 [Defense Evasion](#64-defense-evasion)  
   6.5 [Privilege Escalation](#65-privilege-escalation)  
   6.6 [Persistence](#66-persistence)  
   6.7 [Meta Commands](#67-meta-commands)
7. [SMTP Rate Limiting](#smtp-rate-limiting)
8. [Python API Usage](#python-api-usage)
9. [Logs, Outputs & Artifacts](#logs-outputs--artifacts)
10. [Development & Testing](#development--testing)
11. [Troubleshooting](#troubleshooting)
12. [Contributing](#contributing)

---

## Overview

The APT Toolkit bundles a wide range of adversary-emulation capabilities tailored for red teams, purple teams, and instructors who require realistic tradecraft in a controlled environment. The toolkit is packaged as a Python module with a comprehensive interactive shell that consolidates all features, including:

- Spear-phishing content generation, payload delivery, and target list campaigns.
- Conceptual lateral movement simulations (Pass-the-Hash, implant deployment, network reconnaissance).
- Defense evasion analytics covering Living-Off-The-Land (LOTL) tactics and process hollowing.
- Privilege escalation reconnaissance and vulnerability modelling for Active Directory environments.
- Persistence strategy modelling (scheduled tasks, WMI, registry, and malicious services).
- Persistent configuration management (API keys, SMTP credentials) stored in a git-ignored location.
- A unified help system with extensive instruction for every command.

The project was designed for modular extension. Core functionality is exported through the Python package API and from the operator shell, allowing teams to script bespoke campaigns or use the guided workflow directly.

---

## Feature Matrix

| Category              | Command(s)                   | Description                                                                                             |
|-----------------------|------------------------------|---------------------------------------------------------------------------------------------------------|
| Configuration         | `configure`, `show_config`   | Persist DeepSeek API keys and SMTP profiles; view masked settings.                                      |
| Initial Access        | `generate_email`, `send_email`, `phishing_attack` | Build spear-phishing lures, send individual payloads, or run list-driven campaigns.                     |
| Lateral Movement      | `lateral_discover`, `lateral_pth`, `lateral_deploy` | Simulate subnet discovery, Pass-the-Hash attempts, and implant deployment tradecraft.                   |
| Defense Evasion       | `defense_lotl`, `defense_lotl_detection`, `defense_process_hollowing` | Explore LOTL commands, detection considerations, and process hollowing guidance.                        |
| Privilege Escalation  | `privilege_ad_enum`, `privilege_vuln_scan` | Model AD group reconnaissance and vulnerability assessments for escalation planning.                    |
| Persistence           | `persistence_task`, `persistence_wmi`, `persistence_registry`, `persistence_service` | Generate persistence mechanisms for Windows and Unix-style environments.                                |
| Meta                  | `help`, `exit`, `quit`       | Access built-in documentation and exit the shell.                                                       |

---

## Installation

> **Python 3.8+** is required. Ensure `pip` and virtual environments are available on your platform.

```bash
git clone https://github.com/your-org/chinese_apt_toolkit.git
cd chinese_apt_toolkit
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

The editable install (`pip install -e .`) exposes the provided console scripts:

- `apt-toolkit` → Launches the unified interactive shell.
- `apt` → Alias for `apt-toolkit`.
- `python -m apt_toolkit` → Equivalent module invocation.

> If you previously used the legacy CLI (`apt_toolkit.cli_new`), it remains available but all capabilities are now accessible via the interactive shell.

---

## Configuration & Persistent Settings

- The shell persists operator preferences in `config/user_settings.json`.
- The file is **git ignored** (`.gitignore` contains an entry) to prevent credential leakage.
- Legacy installs using `config/secrets.json` will be auto-detected; the contents migrate on the next save.
- Sensitive values (SMTP password, API keys) are masked in the shell’s display output.  

### Sensitive Data Handling

- API keys and passwords are stored **unencrypted** on disk. Use OS-level encryption (BitLocker, FileVault, etc.) or secret management if required.
- The toolkit never transmits credentials externally; they are used locally for SMTP authentication.

---

## Launching the Interactive Shell

```bash
# From the project root (with virtual environment activated)
apt-toolkit
# or
python -m apt_toolkit
```

On startup you will see:

```
Advanced Persistent Threat Toolkit interactive shell. Type 'help' to explore available capabilities.
apt>
```

Use `help` for an overview or `help <command>` for a deep dive into a specific feature.

---

## Command Reference & Usage Guides

Below is a comprehensive guide for every interactive command, grouped by category. Each entry mirrors the built-in help text and expands on practical usage tips.

### 6.1 Configuration Commands

#### `configure`

- **Purpose:** Persist DeepSeek API keys and SMTP delivery credentials.
- **Usage:** `configure`
- **Workflow:**
  1. Run `configure`.
  2. When prompted, press Enter to keep the existing value or type a new one.
  3. DeepSeek API key is optional but required for AI-assisted email body generation (if integrated).
  4. Enter the SMTP server (e.g., `smtp.gmail.com`), port (often `465` for SSL), username, and password.
  5. All values save to `config/user_settings.json`. The save location is confirmed in-shell.
- **Notes:** Password prompts use masked input. If you mistype a value, rerun `configure` to update it.

#### `show_config`

- **Purpose:** Inspect the current configuration with masking applied to secrets.
- **Usage:** `show_config`
- **Output:** JSON-formatted snapshot showing which fields are set and the file path used.
- **Tip:** Use after `configure` to confirm values persisted as expected.

### 6.2 Initial Access

#### `generate_email`

- **Purpose:** Create a spear-phishing lure with realistic metadata and payload details.
- **Usage:**
  - `generate_email` (random target domain)
  - `generate_email dod.mil` (bias towards a specific domain)
- **Behaviour:**
  - Pulls template content from the internal email repository.
  - Generates subject, body, attachment path, and enrichment intelligence.
  - Stores the result as the “active email” for later commands.
- **Output:** JSON detailing subject, sender, target email, payload file, and tradecraft metadata.
- **Tip:** Run before `send_email` to review everything that will be delivered.

#### `send_email`

- **Purpose:** Deliver the active spear-phishing email to a target recipient via SMTP.
- **Usage:**
  - `send_email target@example.com`
  - `send_email` (uses target from most recent `generate_email`)
- **Prerequisites:** SMTP settings configured via `configure`.
- **Behaviours:**
  - Enforces the **3-second global rate limit** between sends.
  - Generates a fresh email if needed, ensuring attachments exist on disk.
  - Displays delivery status and payload details.
- **Troubleshooting:**
  - If authentication fails, confirm the SMTP credentials and less-secure app access (where applicable).
  - For Gmail, an app password may be required when two-factor authentication is enabled.

#### `phishing_attack`

- **Purpose:** Send spear-phishing emails to every address listed in a target file.
- **Usage:** `phishing_attack /path/to/targets.txt`
- **File Format:** Plain text, one email address per line; blank lines are ignored.
- **Behaviour:**
  - Respects the global 3-second send rate limit automatically.
  - Logs per-target status and produces a campaign summary.
- **Recommendations:**
  - Start with a small list for validation.
  - Monitor SMTP provider rate limits; large campaigns may require throttling or provider approval.

### 6.3 Lateral Movement

#### `lateral_discover`

- **Purpose:** Simulate reconnaissance for network segments suitable for lateral movement.
- **Usage:** `lateral_discover`
- **Output:** JSON containing discovered subnets, prioritised targets, and recommended focus areas.
- **Application:** Useful for briefing defenders or planning follow-on simulated actions.

#### `lateral_pth`

- **Purpose:** Model a Pass-the-Hash attempt with contextual success analysis.
- **Usage:** `lateral_pth <target_ip> <username> <ntlm_hash>`
- **Example:** `lateral_pth 10.0.0.25 admin_user aad3b435b51404eeaad3b435b51404ee`
- **Behaviour:**
  - Evaluates hash validity, network reachability, admin privilege likelihood, and defensive posture.
  - Returns success/failure plus prescribed next steps or failure rationale.
- **Hint:** The shell seeds the lateral movement context with the provided hash for more realistic simulation.

#### `lateral_deploy`

- **Purpose:** Describe implant deployment tradecraft on a chosen host.
- **Usage:** `lateral_deploy <target_ip> [implant_type]`
- **Implant Types:** `beacon` (default), `keylogger`, `recon`
- **Output:** Deployment configuration, persistence mechanism, communication channel, detection difficulty.
- **Use Case:** Planning engagement phases or training analysts on adversary behaviour.

### 6.4 Defense Evasion

#### `defense_lotl`

- **Purpose:** Generate Living-Off-The-Land (LOTL) command sequences across multiple tactics.
- **Usage:** `defense_lotl`
- **Output:** JSON mapping phase (download, execution, information gathering) to command lists.
- **Application:** Provide scriptable examples of trusted binary abuse for training or detection engineering.

#### `defense_lotl_detection`

- **Purpose:** Summarise detection challenges and defensive monitoring strategies for LOTL tooling.
- **Usage:** `defense_lotl_detection`
- **Output:** Detailed analysis per tool, including common use, detection difficulty, and defensive suggestions.
- **Tip:** Pair with `defense_lotl` when delivering cross-team briefings.

#### `defense_process_hollowing`

- **Purpose:** Analyse process hollowing from both attacker and defender perspectives.
- **Usage:** `defense_process_hollowing`
- **Output:** Comprehensive overview featuring targeted processes, indicators, and countermeasures.
- **Use Case:** Educational deep dives or planning detection coverage.

### 6.5 Privilege Escalation

#### `privilege_ad_enum`

- **Purpose:** Model enumeration of high-value Active Directory groups and accounts.
- **Usage:** `privilege_ad_enum`
- **Output:** High-privilege groups, member listings, prioritised escalation targets, recommended techniques.
- **Scenario:** Simulated recon prior to executing escalation attacks in purple-team exercises.

#### `privilege_vuln_scan`

- **Purpose:** Assess a target system for exploitable privilege escalation vulnerabilities.
- **Usage:**
  - `privilege_vuln_scan` (defaults to `dc1.dod.mil`)
  - `privilege_vuln_scan fileserver.acme.local`
- **Output:** Vulnerability presence, exploit availability, risk ranking, prioritised attack order.
- **Tip:** Use custom hostnames to align with scenario narratives.

### 6.6 Persistence

#### `persistence_task`

- **Purpose:** Create a disguised scheduled task (Windows) or cron job (Unix) for long-term access.
- **Usage:**
  - `persistence_task`
  - `persistence_task "Windows Update Service" /tmp/update.ps1`
- **Output:** Task configuration, action command, trigger schedule, detection commentary.
- **Advice:** Provide a payload path to craft scenario-specific demonstrations.

#### `persistence_wmi`

- **Purpose:** Model a WMI event subscription persistence method.
- **Usage:** `persistence_wmi`
- **Output:** WMI filter, consumer, command line, activation trigger, detection difficulty.
- **Note:** Returns an error if executed on non-Windows hosts to reflect platform limitations.

#### `persistence_registry`

- **Purpose:** Outline registry-based persistence via Run keys.
- **Usage:**
  - `persistence_registry`
  - `persistence_registry HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run`
- **Output:** Registry key/value details, payload, detection commentary, reboot survivability.
- **Hint:** Provide custom keys to mirror red-team findings.

#### `persistence_service`

- **Purpose:** Describe malicious Windows service persistence.
- **Usage:**
  - `persistence_service`
  - `persistence_service SystemUpdateService`
- **Output:** Service configuration (name, binary path, start type), detection difficulty.
- **Use Case:** Planning for long-lived footholds or defender training.

### 6.7 Meta Commands

#### `help`

- **Purpose:** Display comprehensive command help with detailed instructions.
- **Usage:**
  - `help` (overview grouped by category)
  - `help <command>` (deep dive on specific command)
- **Output:** Human-readable summaries, detailed descriptions, and usage examples.

#### `exit` / `quit`

- **Purpose:** Terminate the interactive shell.
- **Usage:** `exit` or `quit`
- **Behaviour:** Cleanly exits after printing a farewell message.
- **Shortcut:** Use `Ctrl-D` (EOF) or `Ctrl-C` to achieve the same effect.

---

## SMTP Rate Limiting

- Every call to `send_email` or `phishing_attack` enforces **one email every three seconds**.
- The limiter is implemented globally inside `apt_toolkit.phishing` using a thread-safe lock and monotonic timer.
- This prevents accidental abuse of SMTP providers, avoids triggering rate controls, and mirrors realistic operational pacing.
- The delay applies per process. Running multiple processes concurrently may still hit provider limits—coordinate accordingly.

---

## Python API Usage

While the shell is the primary interface, all functionality is exposed via the package API for scripting or integration into other automation frameworks.

```python
from apt_toolkit import (
    SpearPhishingGenerator,
    deliver_payload,
    LateralMover,
    DefenseEvader,
    PrivilegeEscalator,
    PersistenceManager,
    launch_shell,
)

# Generate a phishing email programmatically
generator = SpearPhishingGenerator()
email = generator.generate_email(target_domain="dod.mil")

# Deliver payload (respects global rate limit)
smtp_profile = {
    "server": "smtp.example.com",
    "port": 465,
    "user": "operator@example.com",
    "password": "app-password",
}
deliver_payload(email["target_email"], smtp_profile)

# Launch interactive shell from Python
launch_shell()
```

> The `launch_shell` function simply delegates to the same `main()` used by the console script—it blocks until the shell exits.

---

## Logs, Outputs & Artifacts

- **Email payloads**: Generated attachments are stored in temporary directories created by `tempfile`; paths appear in command output.
- **Campaign summaries**: JSON blobs printed in the shell can be redirected or copied for reporting.
- **Settings**: `config/user_settings.json` holds shell configuration. Keep it secure.
- **Logs**: Some legacy utilities write to the `logs/` directory (ignored by git). Review individual modules for additional logging behaviour.

---

## Development & Testing

### Repository Layout

- `apt_toolkit/` — Core package modules.
- `tools/`, `campaigns/`, `docs/` — Ancillary materials and scenario data.
- `tests/` — Automated test suites (pytest-based).

### Running Tests

```bash
pip install -r requirements.txt
pytest
```

### Linting & Formatting

- The project does not enforce a single formatter, but Black/flake8 are commonly used in related tooling.
- Static typing (where present) follows standard typing hints; run `mypy` if configured in your environment.

---

## Troubleshooting

| Issue | Possible Cause | Resolution |
|-------|----------------|------------|
| `python` command not found | Python not installed or not in PATH | Install Python 3.8+ and ensure `python3` or `python` resolves correctly. |
| SMTP authentication failures | Incorrect credentials or provider settings | Verify username/password; for Gmail use an App Password. Confirm SSL port (typically 465). |
| `phishing_attack` stops mid-run | Invalid email in list or rate limit reached | Review output for errors; correct email list and rerun. Allow the built-in delay to proceed. |
| Shell crashes on launch | Missing dependencies or incompatible Python version | Reinstall dependencies with `pip install -e .`; confirm Python ≥ 3.8. |
| Legacy configuration ignored | `config/secrets.json` sometimes not migrated | Run `configure` to save; the shell writes to `config/user_settings.json` automatically. |

For verbose debugging, run commands in a Python REPL and inspect stack traces, or instrument modules directly.

---

## Contributing

1. Fork the repository and create a dedicated branch.
2. Make changes with clear commit messages.
3. Ensure new features include documentation updates and (when appropriate) tests.
4. Submit a pull request describing the change, usage scenarios, and any operational caveats.

Before contributing new tradecraft:

- Verify that all tooling remains compliant with legal regulations.
- Provide safe defaults—never ship real malware or live C2 infrastructure.
- Consider adding simulation/analysis modes instead of active exploitation where possible.

---

Maintainers welcome feedback, feature requests, and responsible contributions aligned with ethical security research. For questions, open an issue or contact the project owners through the preferred channels.

Stay safe, stay authorized, and happy testing.

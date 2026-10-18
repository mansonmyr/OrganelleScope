# OrganelleScope 1.0.1

A compact interface update to the stable local research workbench:

- Smaller headers, controls, spacing and empty-image presentation, with responsive sizing.
- Workspace dropdown on narrower windows; compact tabs on wider screens. The image preview stays mounted when workspaces change.
- Collapsible Projects & recovery in the sidebar.
- Minimum STRING score stays blank when cleared. Network retrieval requires a valid integer from 0 to 1000; retyping submits the entered value.
- Fresh-profile native checks now explicitly require empty imported-image and saved-project lists. A separate account-isolation regression verifies that a fresh account starts empty while an existing account retains its own work.
- README application limits and the manual edition now reflect the stable release. The verification guide consolidates current evidence and links historical records.

Download only the Apple Silicon macOS `.dmg` or Windows x64 `.exe` for installation. The installer includes the local inference runtime; Gemma weights use one automatic, resumable 6.98 GB download. New accounts start without sample images or projects; upgrades preserve the existing account’s research data and verified weights.

Native startup/shutdown, artifact integrity and numerical checks run on both release platforms. macOS uses ad-hoc signing and Windows has no publisher certificate. AI drafts require review; source checks are separate from biological validation. See the [manual](../MANUAL.md), [verification scope](VALIDATION.md) and [software citation](../CITATION.cff).

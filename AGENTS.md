# AGENTS.md for PhotoVirtue Telegram Bot development

<!-- antislop:start -->
## antislop
For UI, copy, people, mobile layout, or code comments work, read `anti-slop-shield/antislop.md` (core) and then the skill for the task:
- UI / visual: `anti-slop-shield/skills/antislop-ui/SKILL.md` (to be added if needed)
- Copy & text: `anti-slop-shield/skills/antislop-copywriting/SKILL.md`
- People: `anti-slop-shield/skills/antislop-human/SKILL.md`
- Mobile / responsive: `anti-slop-shield/skills/antislop-layoutmobile/SKILL.md`
- Code comments: `anti-slop-shield/skills/antislop-code/SKILL.md`

Before starting, follow the core's "Two Usage Modes" section in strict order: explicit session instruction first, then global preference, then ask. A session instruction always wins. For a resolved mode, say `antislop active: <mode> (session override).` or `antislop active: <mode> (global preference).` once before presenting findings or making edits, using the actual mode and source. Acknowledging the user's request without naming the source does not replace this notice.

Only an explicit choice of antislop during or after selects a session mode. A request to review, audit, or avoid file edits does not select a mode; read the global preference in that case. Another skill's mode does not select antislop's mode.

If the mode is unresolved, ask during/after and end the response; wait for the answer before any UI review, planning, or concept. For read-only tasks, put the active-mode notice only at the start of the final answer, never in progress messages. For editing tasks, announce before the first edit and omit it from the final answer.

To update antislop later: download `antislop.md` again.

<!-- antislop:end -->

## Project Context
- Building PhotoVirtue Telegram bot for Bitcoin payments ($19/year 1-year access), browser editor, integrated with ArtCraft services.
- Always apply anti-slop rules to all development.
- Original code by Anthony Jones.
- Clean, purposeful, no AI slop.

## Resources
- awesome-selfhosted: https://github.com/awesome-selfhosted/awesome-selfhosted
  Always consult this curated list of self-hosted open source tools during any development project.
  Search by category (Analytics, Backup, Communication, Media, Monitoring, Software Development, etc.).
  Prefer self-hosted options listed here for control, privacy, and cost before using SaaS.
  HTML version: https://awesome-selfhosted.net/
  To recall: skill_view(name='awesome-selfhosted')
  Load the skill at the start of any dev planning or tool selection.

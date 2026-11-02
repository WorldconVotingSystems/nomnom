---
title: Changing the Text on Your Site
---

Most of the words members see belong to your convention, not to NomNom. Before you file an issue or change any text, work out which of the two repositories owns that text:

- **Your convention's repository**, such as `seattle-2025`. It was generated from the NomNom template and holds your site's wording, branding and instructions.
- **The [NomNom repository](https://github.com/WorldconVotingSystems/nomnom)**. It holds the shared application that every convention uses.

The question that settles it: **should this change appear on every convention's site, or only on yours?** If only yours, change your convention's repository. If every convention needs it, or the text is wrong because of a bug, change NomNom.

| What you want to change | Where the change belongs | Example |
| --- | --- | --- |
| Instructions or wording for your members | Your convention's repository | Removing an underline from the nomination instructions |
| Your header, footer, login text or packet welcome text | Your convention's repository | Adding your convention's name to the footer |
| Text that is wrong for every convention | NomNom | A typo in a shared page |
| Behaviour rather than wording | NomNom | A form that saves the wrong value |

## How your convention overrides NomNom

NomNom ships a default version of each template. Your convention is an application listed before NomNom's own applications in `INSTALLED_APPS`, so Django uses your copy of a template when both have the same path. The comment above your convention's entry in `config/settings.py` marks this ordering, and it must stay in place.

A new convention starts with copies of the templates you are most likely to change. In your convention's application folder, look in:

| File in `templates/` | What it controls |
| --- | --- |
| `nominate/bits/nomination_instructions.html` | The instructions on the nomination page |
| `nominate/bits/voting_instructions.html` | The instructions on the voting page |
| `nominate/bits/voting_disclaimers.html` | The disclaimers on the voting page |
| `bits/convention_header.html` and `bits/convention_footer.html` | The site header and footer |
| `bits/login_forms.html` | The login forms |
| `hugopacket/bits/welcome.html` | The welcome text for the Hugo packet |

## Changing text that is not in your templates

If the text you want is not in your convention's `templates/` folder, find the template in NomNom under `src/nomnom/<app>/templates/`. Copy it to the same relative path inside your convention's `templates/` folder, then edit your copy.

For example, the nomination email is at `src/nomnom/nominate/templates/nominate/email/nominations_for_user.html`, so your copy belongs at `templates/nominate/email/nominations_for_user.html`. Email templates usually have a `.txt` version as well, so check whether you need to copy both.

Your copy does not receive later changes that NomNom makes to the same template, so copy only the templates you need to change.

## If you are not sure

File the issue in your convention's repository first, and say what you saw and on which page. A developer can move it to NomNom if the cause turns out to be shared. When the text includes data that NomNom fills in, such as a time in an email, the cause might be in either place.

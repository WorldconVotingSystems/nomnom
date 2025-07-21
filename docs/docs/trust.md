# Trusting NomNom

NomNom offers a degree of protection against ballot manipulation. With the caveat that all voting systems rely on trust in the administrator to some degree, here's what it can do. 

## Auditability

All administrative actions, such as deleting or editing a nomination or vote, are tracked in an audit table within the nominating software. The Hugo Administrator role in NomNom does not have write access to that log. 

NomNom allows administrators to invalidate a vote or nomination. That change does not result in the removal of the nomination or vote, but determines whether it is counted when performing EPH or the IRV vote count. NomNom’s reports include these invalidated values.

In order to support the ability of the Hugo Helpdesk to assist members with their ballot, or to enter mailed-in nominations and votes, member ballots can be edited directly. When changes are made in that way, the system emails the member a notification that their ballot has been edited. The administrator and hugo helpdesk roles do not have the ability to prevent these emails from being sent.

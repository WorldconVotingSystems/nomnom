# Trusting NomNom

NomNom offers a degree of protection against ballot manipulation. With the caveat that all voting systems rely on trust in the administrator to some degree, here's what it can do. 

## Auditability

All administrative actions, such as deleting or editing a nomination or vote, are tracked in an audit table within the nominating software. The Hugo Administrator role in NomNom does not have write access to that log. 

In order to support the ability of the Hugo Helpdesk to assist members with their ballot, or to enter mailed-in nominations and votes, member ballots can be edited directly. When changes are made in that way, the system emails the member a notification that their ballot has been edited. The administrator and hugo helpdesk roles do not have the ability to control this.

# Advisory Votes

This is an optional feature added to support Glasgow 2024's "Advisory Vote" concept.

## Creating a new Vote

Votes are created in the admin pages, located at `/admin/advise/proposal/`

The detail page offers a title, a markdown entry for the full text of the proposal, and a couple of admin controls for it. By default, abstentions are not permitted, but that can be optionally enabled.

The proposal will be visible at `/bm/<id>` to logged in WSFS members.

## Permissions

In order to administer these, the following permissions should be set for any staff member who should be able to see it:

```
Advise | proposal | Can add proposal
Advise | proposal | Can change proposal
Advise | proposal | Can view proposal
Advise | proposal | Can delete proposal
Advise | vote | Can add vote
Advise | vote | Can change vote
Advise | vote | Can view vote
Advise | vote | Can delete vote
Advise | vote admin data | Can add vote admin data
Advise | vote admin data | Can change vote admin data
Advise | vote admin data | Can view vote admin data
Advise | vote admin data | Can delete vote admin data
```

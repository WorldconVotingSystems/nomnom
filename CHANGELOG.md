# Changelog

This system doesn't have a version yet, so everything in here is listed under `1.0.0`

## 1.0.0

### Major Features

* Hugo Voting
* Hugo Nomination
* Hugo Nomination administration
* Convention theme customization
* OAuth login with Clyde
* Theming via convention classes
* Tallying Hugo votes according to the 2023 WSFS constitution [#122, #119]

### Minor Features and Bugfixes

* Autocomplete nominators in the nomination editor view (admin)
* Add a creation date for member profiles (db, migration)
* Make the member number immutable (admin)
* Handle missing WSFS status keys in the authentication flow [#52] (bug, oauth)
* Support providing a registration email in templates as `REGISTRATION_EMAIL` (admin)
* Username login can be toggled consistently wherever we log in (dev)
* Added an autocompleting filter for nominations by member [#68]
* Fixed a major inconsistency when saving nominations [#62, fixed in #67]
* Submit ballots without losing one's place on the page [#73]
* Ballot tweaks for voting [#121]
* Ballot order respected for voting [#126]

### System Features

* Sentry integration for errors
* Docker image build

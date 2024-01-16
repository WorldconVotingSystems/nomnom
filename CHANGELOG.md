# Changelog

This system doesn't have a version yet, so everything in here is listed under `1.0.0`

## 1.0.0

### Major Features

* Hugo Voting bare bones
* Hugo Nomination bare bones
* Hugo Nomination administration
* Convention theme customization
* OAuth login with Clyde
* Theming via convention classes

### Minor Features and Bugfixes

* Autocomplete nominators in the nomination editor view (admin)
* Add a creation date for member profiles (db, migration)
* Make the member number immutable (admin)
* Handle missing WSFS status keys in the authentication flow [#52] (bug, oauth)
* Support providing a registration email in templates as `REGISTRATION_EMAIL` (admin)
* Username login can be toggled consistently wherever we log in (dev)
* Added an autocompleting filter for nominations by member [#68]
* Fixed a major inconsistency when saving nominations [#62, fixed in #67]

### System Features

* Sentry integration for errors
* Docker image build

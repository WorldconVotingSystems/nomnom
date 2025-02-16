# Canonicalization

One of the steps between nominating and voting is the selection of finalists. Before that can take place, though, it is necessary to "canonicalize" the raw nomination data. This process takes the many ways that nominators may write a title or an author, and associates them with a canonical name.

That process is nearly entirely manual, and NomNom provides support for it by way of the administration interface, in the "Canonicalize" section.

## Glossary

* **Nomination**: The text provided by the member to identify something they propose to include on the Hugo Award ballot
* **Work**: The single, canonical text form of one or more _Nominations_, so that they can all be referred to as a singular thing. Note that **Work** is the term that NomNom uses regardless of if the category refers to works or persons or other entities.

## Initial Canonicalization

The list of raw nominations is found at `/admin/canonicalize/canonicalizednomination/`; there are some optional filters oriented around making the process easier.

Canonicalizing a work consists of either selecting multiple works and associating them with a new or existing work, _or_ clicking the one-off button to make them an individual work.

## New Nominations

In order to allow the admins to canonicalize as they go, nominations are associated with canonicalized works as they arrive, if they exactly match the text of a previously canonicalized Nomination. No fuzzy matching takes place. If they exactly match nominations that are associated with more than one work, then one of the Works will be selected, with the ordering undefied.

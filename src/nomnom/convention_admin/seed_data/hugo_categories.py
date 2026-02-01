"""
Official Hugo Awards categories for seeding elections.

This file contains real Hugo Award category definitions based on the
2025 Hugo Awards at LAConV (Los Angeles Convention).

Each category includes:
- ballot_position: Order on the ballot
- name: Category name
- description: Eligibility requirements
- nominating_details: Additional guidance for nominators
- fields: Number of fields (1-3)
- field_1_description: Label for first field
- field_2_description: Label for second field (if fields >= 2)
- field_2_required: Whether second field is required
- field_3_description: Label for third field (if fields >= 3)
- field_3_required: Whether third field is required
"""

HUGO_CATEGORIES = [
    {
        "ballot_position": 1,
        "name": "Best Novel",
        "description": "A science fiction or fantasy story of 40,000 words or more, published for the first time in 2025.",
        "nominating_details": "",
        "fields": 3,
        "field_1_description": "Title",
        "field_2_description": "Author",
        "field_2_required": True,
        "field_3_description": "Publisher",
        "field_3_required": False,
    },
    {
        "ballot_position": 2,
        "name": "Best Novella",
        "description": "A science fiction or fantasy story between 17,500 and 40,000 words, which appeared for the first time in 2025.",
        "nominating_details": "",
        "fields": 3,
        "field_1_description": "Title",
        "field_2_description": "Author",
        "field_2_required": True,
        "field_3_description": "Where Published?",
        "field_3_required": False,
    },
    {
        "ballot_position": 3,
        "name": "Best Novelette",
        "description": "A science fiction or fantasy story between 7,500 and 17,500 words, which appeared for the first time in 2025.",
        "nominating_details": "",
        "fields": 3,
        "field_1_description": "Title",
        "field_2_description": "Author",
        "field_2_required": True,
        "field_3_description": "Where Published?",
        "field_3_required": False,
    },
    {
        "ballot_position": 4,
        "name": "Best Short Story",
        "description": "A science fiction or fantasy story of fewer than 7,500 words, which appeared for the first time in 2025.",
        "nominating_details": "",
        "fields": 3,
        "field_1_description": "Title",
        "field_2_description": "Author",
        "field_2_required": True,
        "field_3_description": "Where Published?",
        "field_3_required": False,
    },
    {
        "ballot_position": 5,
        "name": "Best Series",
        "description": (
            "A multi-installment science fiction or fantasy story, unified by elements such as plot, characters, "
            "setting, and presentation, appearing in at least three (3) installments consisting in total of at least "
            "240,000 words by the close of the calendar year 2025, at least one (1) installment of which was published "
            "in 2025, and which has not previously won under §3.3.5 of the WSFS Constitution.\n\n"
            "Previous losing finalists in the best series category shall be eligible only upon the publication of at "
            "least two (2) additional installments consisting in total of at least 240,000 words after they qualified "
            "for their last appearance on the final ballot and by the close of 2025. For finalists in the best series "
            "category that have previously appeared on the ballot for best series, any installments published in English "
            "in a year prior to that previous appearance, regardless of country of publication, shall be considered to "
            "be part of the series' previous eligibility, and will not count toward the re-eligibility requirements for "
            "the current year."
        ),
        "nominating_details": (
            "If any series and a subset series thereof both receive sufficient nominations to appear on the final ballot, "
            "only the version which received more nominations shall appear.\n"
            "See the LAConV web page for a note regarding 2025 best series eligibility for specific works which have "
            "previously won or been finalists for the Best Series Hugo Award: (INSERT LINK HERE)"
        ),
        "fields": 3,
        "field_1_description": "Series Name",
        "field_2_description": "Author",
        "field_2_required": True,
        "field_3_description": "2025 example from series",
        "field_3_required": False,
    },
    {
        "ballot_position": 6,
        "name": "Best Graphic Story or Comic",
        "description": "Any non-interactive science fiction or fantasy story told in graphic form, appearing for the first time in 2025.",
        "nominating_details": "",
        "fields": 3,
        "field_1_description": "Title",
        "field_2_description": "Author",
        "field_2_required": True,
        "field_3_description": "Publisher",
        "field_3_required": False,
    },
    {
        "ballot_position": 7,
        "name": "Best Related Work",
        "description": (
            "Any work related to the field of science fiction, fantasy, or fandom, appearing for the first time in 2025, "
            "or which has been substantially modified during 2025, and which is either non-fiction or, if fictional, "
            "is noteworthy primarily for aspects other than the fictional text, and which is not eligible in any other category."
        ),
        "nominating_details": "",
        "fields": 3,
        "field_1_description": "Title",
        "field_2_description": "Author or Editor",
        "field_2_required": True,
        "field_3_description": "Publisher",
        "field_3_required": False,
    },
    {
        "ballot_position": 8,
        "name": "Best Dramatic Presentation - Long Form",
        "description": (
            "Any non-interactive theatrical feature or other production with a complete running time of more than 90 minutes, "
            "in any medium of dramatized science fiction, fantasy, or related subjects that has been publicly presented for "
            "the first time in its present dramatic form during 2025."
        ),
        "nominating_details": "",
        "fields": 2,
        "field_1_description": "Title",
        "field_2_description": "Studio or Network",
        "field_2_required": False,
        "field_3_description": "",
        "field_3_required": False,
    },
    {
        "ballot_position": 9,
        "name": "Best Dramatic Presentation - Short Form",
        "description": (
            "Any non-interactive television program or other production with a complete running time of 90 minutes or less, "
            "in any medium of dramatized science fiction, fantasy, or related subjects that has been publicly presented for "
            "the first time in its present dramatic form during 2025."
        ),
        "nominating_details": 'If your nominee is not part of a serial dramatization, enter a dash "-" in the "Series (if applicable)" field.',
        "fields": 3,
        "field_1_description": "Title",
        "field_2_description": "Series (if applicable)",
        "field_2_required": True,
        "field_3_description": "Studio or Network",
        "field_3_required": False,
    },
    {
        "ballot_position": 10,
        "name": "Best Game or Interactive Work",
        "description": (
            "Any interactive work or interactive substantial modification of a work in the fields of science fiction, fantasy, "
            "or related subjects, released to the public in 2025 and available for public participation in the interactive "
            "elements of the work in 2025. An interactive work is (1) a game, or (2) a narrative or presentation in which "
            "active input or interactive play is an integral component of the work itself or where it impacts the outcome, "
            "narrative, or order of elements of the work itself in a nontrivial fashion, and (3) is not ephemeral, in the "
            "sense that the interactive elements of the work are accessible to participants through published or shareable "
            "artifacts, and the work is not an event requiring the participation of specific named persons."
        ),
        "nominating_details": "",
        "fields": 2,
        "field_1_description": "Title",
        "field_2_description": "Developer",
        "field_2_required": True,
        "field_3_description": "",
        "field_3_required": False,
    },
    {
        "ballot_position": 11,
        "name": "Best Editor - Short Form",
        "description": (
            "The editor of at least four (4) anthologies, collections, or magazine issues (or their equivalent in other media) "
            "primarily devoted to science fiction and/or fantasy, at least one of which was published in 2025."
        ),
        "nominating_details": "",
        "fields": 1,
        "field_1_description": "Editor Name",
        "field_2_description": "",
        "field_2_required": True,
        "field_3_description": "",
        "field_3_required": True,
    },
    {
        "ballot_position": 12,
        "name": "Best Editor - Long Form",
        "description": (
            "The editor of at least four (4) novel-length works primarily devoted to science fiction and/or fantasy "
            "published in 2025, which do not qualify as works under Best Editor - Long Form."
        ),
        "nominating_details": "",
        "fields": 1,
        "field_1_description": "Editor Name",
        "field_2_description": "",
        "field_2_required": True,
        "field_3_description": "",
        "field_3_required": True,
    },
    {
        "ballot_position": 13,
        "name": "Best Professional Artist",
        "description": (
            "An illustrator whose work has appeared in a professional publication* in the field of science fiction or "
            "fantasy during 2025.\n"
            "If possible, please cite an example of the nominee's 2025 work in this category and a source where it may be found. "
            "This information makes it easier for us to assess eligibility. (Failure to provide such references will not invalidate "
            "a nomination.)\n"
            "* A professional publication is one that meets at least one (1) of the following criteria:\n"
            "1. It provided at least a quarter of the income of any one person; or\n"
            "2. It was owned or published by any entity which provided at least a quarter of the income of any of its staff and/or owner."
        ),
        "nominating_details": "",
        "fields": 2,
        "field_1_description": "Artist Name",
        "field_2_description": "Example",
        "field_2_required": False,
        "field_3_description": "",
        "field_3_required": True,
    },
    {
        "ballot_position": 14,
        "name": "Best Semiprozine",
        "description": (
            "Any generally available non-professional periodical publication devoted to science fiction or fantasy, or related subjects "
            "which by the close of 2025 had published four (4) or more issues (or the equivalent in other media), at least one (1) of "
            "which appeared in 2025, which does not qualify as a fancast, and which in 2025 met at least one (1) of the following criteria:\n"
            "1. Paid its contributors and/or staff in other than copies of the publication.\n"
            "2. Was generally available only for paid purchase."
        ),
        "nominating_details": "",
        "fields": 1,
        "field_1_description": "Title",
        "field_2_description": "",
        "field_2_required": True,
        "field_3_description": "",
        "field_3_required": True,
    },
    {
        "ballot_position": 15,
        "name": "Best Fanzine",
        "description": (
            "Any generally available non-professional periodical publication devoted to science fiction, fantasy, or related subjects "
            "that, by the close of 2025, had published four (4) or more issues (or the equivalent in other media), at least one (1) of "
            "which appeared in 2025, that does not qualify as a semiprozine or a fancast, and which in 2025 met neither of the following criteria:\n"
            "1. Paid its contributors or staff monetarily in other than copies of the publication.\n"
            "2. Was generally available only for paid purchase."
        ),
        "nominating_details": "",
        "fields": 1,
        "field_1_description": "Title",
        "field_2_description": "",
        "field_2_required": True,
        "field_3_description": "",
        "field_3_required": True,
    },
    {
        "ballot_position": 16,
        "name": "Best Fancast",
        "description": (
            "Any generally available non-professional audio or video periodical devoted to science fiction, fantasy, or related subjects "
            "that by the close of 2025 had released four (4) or more episodes, at least one (1) of which appeared in 2025, and that does "
            "not qualify as a dramatic presentation."
        ),
        "nominating_details": "",
        "fields": 1,
        "field_1_description": "Title",
        "field_2_description": "",
        "field_2_required": True,
        "field_3_description": "",
        "field_3_required": True,
    },
    {
        "ballot_position": 17,
        "name": "Best Fan Writer",
        "description": (
            "A person whose writing has appeared in semiprozines or fanzines, or in generally available electronic media in 2025.\n"
            "If possible, please cite an example of the nominee's 2025 work in this category and a source where it may be found. "
            "This information makes it easier for us to assess eligibility. (Failure to provide such references will not invalidate a nomination.)"
        ),
        "nominating_details": "",
        "fields": 2,
        "field_1_description": "Author",
        "field_2_description": "Example",
        "field_2_required": False,
        "field_3_description": "",
        "field_3_required": True,
    },
    {
        "ballot_position": 18,
        "name": "Best Fan Artist",
        "description": (
            "An artist or cartoonist whose work has appeared through publication in semiprozines or fanzines, or through other public, "
            "non-professional, display (including at a convention or conventions, posting on the internet, in online or print-on-demand "
            "shops, or in another setting not requiring a fee to see the image in full-resolution) in 2025.\n"
            "If possible, please cite an example of the nominee's 2025 work in this category and a source where it may be found. "
            "This information makes it easier for us to assess eligibility. (Failure to provide such references will not invalidate a nomination.)"
        ),
        "nominating_details": "",
        "fields": 2,
        "field_1_description": "Artist Name",
        "field_2_description": "Example",
        "field_2_required": False,
        "field_3_description": "",
        "field_3_required": True,
    },
    {
        "ballot_position": 19,
        "name": "Best Poem",
        "description": "A science fiction or fantasy poem of any line length or word count appearing for the first time in 2025.",
        "nominating_details": "",
        "fields": 3,
        "field_1_description": "Title",
        "field_2_description": "Author",
        "field_2_required": True,
        "field_3_description": "Where Published?",
        "field_3_required": False,
    },
    {
        "ballot_position": 20,
        "name": "Lodestar Award for Best Young Adult Book (not a Hugo Award)",
        "description": "A book published for young adult readers in the field of science fiction or fantasy appearing for the first time in 2025.",
        "nominating_details": "",
        "fields": 3,
        "field_1_description": "Title",
        "field_2_description": "Author",
        "field_2_required": True,
        "field_3_description": "Publisher",
        "field_3_required": False,
    },
    {
        "ballot_position": 21,
        "name": "*Astounding* Award for Best New Writer, sponsored by Must Read (?? Still correct?) Magazines (not a Hugo Award)",
        "description": (
            "A new writer is one whose first work of science fiction or fantasy appeared in 2024 or 2025 in a professional publication. "
            "For *Astounding* Award purposes, a professional publication is one for which more than a nominal amount was paid, any "
            "publication that had an average press run of at least 10,000 copies, or for which the author can demonstrate net income "
            "of at least $3,000 within one year."
        ),
        "nominating_details": (
            "The following are not taken into account for *Astounding* Award eligibility: works in non-qualifying publications; poetry, "
            "even if it is SF/F and appears in a qualifying publication; nonfiction, even if it is SF/F and appears in a qualifying "
            "publication; fiction outside the SF/F genres; fan writing of any sort; letters to the editor; vanity press or self-published "
            "fiction for which the author is not paid, even if the print run is over 10,000; and writing for SF/F games.\n"
            "The *Astounding* Award FAQ can be found here: https://astoundingaward.info/#faq"
        ),
        "fields": 2,
        "field_1_description": "Author",
        "field_2_description": "Example",
        "field_2_required": False,
        "field_3_description": "",
        "field_3_required": True,
    },
]

"""Sample fictional works with realistic variations for seeding Hugo Awards data.

Each work includes:
- canonical: The "correct" form of the nomination
- variations: Common misspellings, typos, formatting differences, and abbreviations
- popularity_weight: Higher values = more likely to be nominated (1-10 scale)

These are FICTIONAL works created for testing purposes. This content was generated with an LLM and
any resemblance to real works is purely coincidental (and a bug, too! please report those, so I can
remove anything that turns out to, like, exist!)

"""

# Novel - field_1: Title, field_2: Author
SAMPLE_NOVELS = [
    {
        "canonical": {
            "field_1": "The Starlight Covenant",
            "field_2": "Miranda Chen",
        },
        "variations": [
            {"field_1": "Starlight Covenant", "field_2": "Miranda Chen"},
            {"field_1": "The Starlight Covenant", "field_2": "M. Chen"},
            {"field_1": "The Star Light Covenant", "field_2": "Miranda Chen"},
            {"field_1": "The Starlight Covenent", "field_2": "Miranda Chen"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {
            "field_1": "Memory's Edge",
            "field_2": "James Kowalski",
        },
        "variations": [
            {"field_1": "Memorys Edge", "field_2": "James Kowalski"},
            {"field_1": "Memory's Edge", "field_2": "J. Kowalski"},
            {"field_1": "Memory's Edge", "field_2": "James Kowalsky"},
            {"field_1": "Memories Edge", "field_2": "James Kowalski"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {
            "field_1": "The Last Algorithm",
            "field_2": "Sarah O'Brien",
        },
        "variations": [
            {"field_1": "Last Algorithm", "field_2": "Sarah O'Brien"},
            {"field_1": "The Last Algorithm", "field_2": "Sarah OBrien"},
            {"field_1": "The Last Algorithim", "field_2": "Sarah O'Brien"},
            {"field_1": "The Last Algorithm", "field_2": "S. O'Brien"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {
            "field_1": "Beneath the Copper Sky",
            "field_2": "Anika Patel",
        },
        "variations": [
            {"field_1": "Beneath The Copper Sky", "field_2": "Anika Patel"},
            {"field_1": "Beneath the Copper Sky", "field_2": "A. Patel"},
            {"field_1": "Below the Copper Sky", "field_2": "Anika Patel"},
            {"field_1": "Beneath the Copper Skies", "field_2": "Anika Patel"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {
            "field_1": "Quantum Tides",
            "field_2": "David Nakamura",
        },
        "variations": [
            {"field_1": "Quantum Tides", "field_2": "D. Nakamura"},
            {"field_1": "The Quantum Tides", "field_2": "David Nakamura"},
            {"field_1": "Quantum Tide", "field_2": "David Nakamura"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {
            "field_1": "Children of the Void",
            "field_2": "Elena Volkov",
        },
        "variations": [
            {"field_1": "Children of the Void", "field_2": "E. Volkov"},
            {"field_1": "The Children of the Void", "field_2": "Elena Volkov"},
            {"field_1": "Children of Void", "field_2": "Elena Volkov"},
            {"field_1": "Children of the Void", "field_2": "Elena Volkova"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {
            "field_1": "The Singing Mountain",
            "field_2": "Thomas Wright",
        },
        "variations": [
            {"field_1": "Singing Mountain", "field_2": "Thomas Wright"},
            {"field_1": "The Singing Mountain", "field_2": "T. Wright"},
            {"field_1": "The Singing Mountains", "field_2": "Thomas Wright"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {
            "field_1": "Echoes in the Dark",
            "field_2": "Maria Santos",
        },
        "variations": [
            {"field_1": "Echoes In The Dark", "field_2": "Maria Santos"},
            {"field_1": "Echoes in the Dark", "field_2": "M. Santos"},
            {"field_1": "Echo in the Dark", "field_2": "Maria Santos"},
        ],
        "popularity_weight": 6,
    },
    {
        "canonical": {
            "field_1": "The Crystal Imperative",
            "field_2": "Jennifer Kim",
        },
        "variations": [
            {"field_1": "Crystal Imperative", "field_2": "Jennifer Kim"},
            {"field_1": "The Crystal Imperative", "field_2": "J. Kim"},
            {"field_1": "The Crystall Imperative", "field_2": "Jennifer Kim"},
        ],
        "popularity_weight": 6,
    },
    {
        "canonical": {
            "field_1": "Shadows of Tomorrow",
            "field_2": "Robert Chen",
        },
        "variations": [
            {"field_1": "Shadows Of Tomorrow", "field_2": "Robert Chen"},
            {"field_1": "Shadow of Tomorrow", "field_2": "Robert Chen"},
            {"field_1": "Shadows of Tomorrow", "field_2": "R. Chen"},
        ],
        "popularity_weight": 5,
    },
    {
        "canonical": {
            "field_1": "The Frozen Protocol",
            "field_2": "Amanda Rodriguez",
        },
        "variations": [
            {"field_1": "Frozen Protocol", "field_2": "Amanda Rodriguez"},
            {"field_1": "The Frozen Protocol", "field_2": "A. Rodriguez"},
        ],
        "popularity_weight": 5,
    },
    {
        "canonical": {
            "field_1": "Orbital Descent",
            "field_2": "Marcus Ibrahim",
        },
        "variations": [
            {"field_1": "Orbital Descent", "field_2": "M. Ibrahim"},
            {"field_1": "The Orbital Descent", "field_2": "Marcus Ibrahim"},
        ],
        "popularity_weight": 4,
    },
    {
        "canonical": {
            "field_1": "The Glass Frontier",
            "field_2": "Lisa Zhang",
        },
        "variations": [
            {"field_1": "Glass Frontier", "field_2": "Lisa Zhang"},
            {"field_1": "The Glass Frontier", "field_2": "L. Zhang"},
        ],
        "popularity_weight": 4,
    },
    {
        "canonical": {
            "field_1": "Beyond the Pale Sun",
            "field_2": "Daniel Harper",
        },
        "variations": [
            {"field_1": "Beyond The Pale Sun", "field_2": "Daniel Harper"},
            {"field_1": "Beyond the Pale Sun", "field_2": "D. Harper"},
        ],
        "popularity_weight": 3,
    },
    {
        "canonical": {
            "field_1": "The Infinite Shore",
            "field_2": "Rachel Green",
        },
        "variations": [
            {"field_1": "Infinite Shore", "field_2": "Rachel Green"},
            {"field_1": "The Infinite Shore", "field_2": "R. Green"},
        ],
        "popularity_weight": 3,
    },
    {
        "canonical": {
            "field_1": "Timekeeper's Legacy",
            "field_2": "Alex Foster",
        },
        "variations": [
            {"field_1": "Timekeepers Legacy", "field_2": "Alex Foster"},
            {"field_1": "The Timekeeper's Legacy", "field_2": "Alex Foster"},
        ],
        "popularity_weight": 2,
    },
    {
        "canonical": {
            "field_1": "The Amber War",
            "field_2": "Victoria Lee",
        },
        "variations": [
            {"field_1": "Amber War", "field_2": "Victoria Lee"},
            {"field_1": "The Amber War", "field_2": "V. Lee"},
        ],
        "popularity_weight": 2,
    },
    {
        "canonical": {
            "field_1": "Whispers from Andromeda",
            "field_2": "Christopher Mills",
        },
        "variations": [
            {"field_1": "Whispers From Andromeda", "field_2": "Christopher Mills"},
            {"field_1": "Whispers from Andromeda", "field_2": "C. Mills"},
        ],
        "popularity_weight": 2,
    },
    {
        "canonical": {
            "field_1": "The Void Between Stars",
            "field_2": "Sophie Turner",
        },
        "variations": [
            {"field_1": "Void Between Stars", "field_2": "Sophie Turner"},
            {"field_1": "The Void Between Stars", "field_2": "S. Turner"},
        ],
        "popularity_weight": 1,
    },
    {
        "canonical": {
            "field_1": "Remnants of Earth",
            "field_2": "Benjamin Walsh",
        },
        "variations": [
            {"field_1": "Remnants Of Earth", "field_2": "Benjamin Walsh"},
            {"field_1": "Remnants of Earth", "field_2": "B. Walsh"},
        ],
        "popularity_weight": 1,
    },
]

# Novella - field_1: Title, field_2: Author
SAMPLE_NOVELLAS = [
    {
        "canonical": {
            "field_1": "The Silver Thread",
            "field_2": "Nora Quinn",
        },
        "variations": [
            {"field_1": "Silver Thread", "field_2": "Nora Quinn"},
            {"field_1": "The Silver Thread", "field_2": "N. Quinn"},
            {"field_1": "The Silver Threads", "field_2": "Nora Quinn"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {
            "field_1": "Ghost Protocol",
            "field_2": "Michael Reeves",
        },
        "variations": [
            {"field_1": "The Ghost Protocol", "field_2": "Michael Reeves"},
            {"field_1": "Ghost Protocol", "field_2": "M. Reeves"},
            {"field_1": "Ghost Protocal", "field_2": "Michael Reeves"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {
            "field_1": "Under Neon Skies",
            "field_2": "Priya Sharma",
        },
        "variations": [
            {"field_1": "Under Neon Skies", "field_2": "P. Sharma"},
            {"field_1": "Under the Neon Skies", "field_2": "Priya Sharma"},
            {"field_1": "Under Neon Sky", "field_2": "Priya Sharma"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {
            "field_1": "The Last Garden",
            "field_2": "Antonio Garcia",
        },
        "variations": [
            {"field_1": "Last Garden", "field_2": "Antonio Garcia"},
            {"field_1": "The Last Garden", "field_2": "A. Garcia"},
            {"field_1": "The Last Gardens", "field_2": "Antonio Garcia"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {
            "field_1": "Clockwork Dreams",
            "field_2": "Emma Davies",
        },
        "variations": [
            {"field_1": "Clockwork Dreams", "field_2": "E. Davies"},
            {"field_1": "Clockwork Dream", "field_2": "Emma Davies"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {
            "field_1": "The Midnight Engine",
            "field_2": "Hassan Al-Rashid",
        },
        "variations": [
            {"field_1": "Midnight Engine", "field_2": "Hassan Al-Rashid"},
            {"field_1": "The Midnight Engine", "field_2": "H. Al-Rashid"},
            {"field_1": "The Midnight Engine", "field_2": "Hassan Al Rashid"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {
            "field_1": "Songs of the Deep",
            "field_2": "Keiko Tanaka",
        },
        "variations": [
            {"field_1": "Songs Of The Deep", "field_2": "Keiko Tanaka"},
            {"field_1": "Songs of the Deep", "field_2": "K. Tanaka"},
            {"field_1": "Song of the Deep", "field_2": "Keiko Tanaka"},
        ],
        "popularity_weight": 6,
    },
    {
        "canonical": {
            "field_1": "The Bone Collector",
            "field_2": "Isaac Stone",
        },
        "variations": [
            {"field_1": "Bone Collector", "field_2": "Isaac Stone"},
            {"field_1": "The Bone Collector", "field_2": "I. Stone"},
        ],
        "popularity_weight": 6,
    },
    {
        "canonical": {
            "field_1": "Fragments of Light",
            "field_2": "Olivia Park",
        },
        "variations": [
            {"field_1": "Fragments Of Light", "field_2": "Olivia Park"},
            {"field_1": "Fragments of Light", "field_2": "O. Park"},
        ],
        "popularity_weight": 5,
    },
    {
        "canonical": {
            "field_1": "The Paper Crown",
            "field_2": "William Chen",
        },
        "variations": [
            {"field_1": "Paper Crown", "field_2": "William Chen"},
            {"field_1": "The Paper Crown", "field_2": "W. Chen"},
        ],
        "popularity_weight": 5,
    },
    {
        "canonical": {
            "field_1": "Electric Sheep",
            "field_2": "Anna Kowalczyk",
        },
        "variations": [
            {"field_1": "Electric Sheep", "field_2": "A. Kowalczyk"},
            {"field_1": "The Electric Sheep", "field_2": "Anna Kowalczyk"},
        ],
        "popularity_weight": 4,
    },
    {
        "canonical": {
            "field_1": "Twilight Signals",
            "field_2": "Carlos Mendez",
        },
        "variations": [
            {"field_1": "Twilight Signals", "field_2": "C. Mendez"},
            {"field_1": "Twilight Signal", "field_2": "Carlos Mendez"},
        ],
        "popularity_weight": 4,
    },
    {
        "canonical": {
            "field_1": "The Rust Angels",
            "field_2": "Grace Morrison",
        },
        "variations": [
            {"field_1": "Rust Angels", "field_2": "Grace Morrison"},
            {"field_1": "The Rust Angels", "field_2": "G. Morrison"},
        ],
        "popularity_weight": 3,
    },
    {
        "canonical": {
            "field_1": "Shadow Market",
            "field_2": "Ivan Petrov",
        },
        "variations": [
            {"field_1": "Shadow Market", "field_2": "I. Petrov"},
            {"field_1": "The Shadow Market", "field_2": "Ivan Petrov"},
        ],
        "popularity_weight": 3,
    },
    {
        "canonical": {
            "field_1": "Beneath the Ice",
            "field_2": "Julia Wagner",
        },
        "variations": [
            {"field_1": "Beneath The Ice", "field_2": "Julia Wagner"},
            {"field_1": "Beneath the Ice", "field_2": "J. Wagner"},
        ],
        "popularity_weight": 2,
    },
]

# Novelette - field_1: Title, field_2: Author
SAMPLE_NOVELETTES = [
    {
        "canonical": {
            "field_1": "The Memory Thief",
            "field_2": "Laura Martinez",
        },
        "variations": [
            {"field_1": "Memory Thief", "field_2": "Laura Martinez"},
            {"field_1": "The Memory Thief", "field_2": "L. Martinez"},
            {"field_1": "The Memory Theif", "field_2": "Laura Martinez"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {
            "field_1": "Fireflies at Dawn",
            "field_2": "Samuel Lee",
        },
        "variations": [
            {"field_1": "Fireflies At Dawn", "field_2": "Samuel Lee"},
            {"field_1": "Fireflies at Dawn", "field_2": "S. Lee"},
            {"field_1": "Firefly at Dawn", "field_2": "Samuel Lee"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {
            "field_1": "The Glass Door",
            "field_2": "Yuki Sato",
        },
        "variations": [
            {"field_1": "Glass Door", "field_2": "Yuki Sato"},
            {"field_1": "The Glass Door", "field_2": "Y. Sato"},
            {"field_1": "The Glass Doors", "field_2": "Yuki Sato"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {
            "field_1": "Whispers in Silicon",
            "field_2": "Fatima Hassan",
        },
        "variations": [
            {"field_1": "Whispers In Silicon", "field_2": "Fatima Hassan"},
            {"field_1": "Whispers in Silicon", "field_2": "F. Hassan"},
            {"field_1": "Whisper in Silicon", "field_2": "Fatima Hassan"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {
            "field_1": "The Autumn Machine",
            "field_2": "Patrick O'Connor",
        },
        "variations": [
            {"field_1": "Autumn Machine", "field_2": "Patrick O'Connor"},
            {"field_1": "The Autumn Machine", "field_2": "P. O'Connor"},
            {"field_1": "The Autumn Machine", "field_2": "Patrick OConnor"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {
            "field_1": "Dancing with Shadows",
            "field_2": "Zoe Williams",
        },
        "variations": [
            {"field_1": "Dancing With Shadows", "field_2": "Zoe Williams"},
            {"field_1": "Dancing with Shadows", "field_2": "Z. Williams"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {
            "field_1": "The Coral Garden",
            "field_2": "Diego Silva",
        },
        "variations": [
            {"field_1": "Coral Garden", "field_2": "Diego Silva"},
            {"field_1": "The Coral Garden", "field_2": "D. Silva"},
        ],
        "popularity_weight": 6,
    },
    {
        "canonical": {
            "field_1": "Seven Keys",
            "field_2": "Maya Patel",
        },
        "variations": [
            {"field_1": "Seven Keys", "field_2": "M. Patel"},
            {"field_1": "The Seven Keys", "field_2": "Maya Patel"},
        ],
        "popularity_weight": 6,
    },
    {
        "canonical": {
            "field_1": "Beneath the Binary",
            "field_2": "Nathan Ford",
        },
        "variations": [
            {"field_1": "Beneath The Binary", "field_2": "Nathan Ford"},
            {"field_1": "Beneath the Binary", "field_2": "N. Ford"},
        ],
        "popularity_weight": 5,
    },
    {
        "canonical": {
            "field_1": "The Last Signal",
            "field_2": "Isabella Romano",
        },
        "variations": [
            {"field_1": "Last Signal", "field_2": "Isabella Romano"},
            {"field_1": "The Last Signal", "field_2": "I. Romano"},
        ],
        "popularity_weight": 5,
    },
    {
        "canonical": {
            "field_1": "Morning Star",
            "field_2": "Raj Kumar",
        },
        "variations": [
            {"field_1": "Morning Star", "field_2": "R. Kumar"},
            {"field_1": "The Morning Star", "field_2": "Raj Kumar"},
        ],
        "popularity_weight": 4,
    },
    {
        "canonical": {
            "field_1": "Through Broken Glass",
            "field_2": "Sophia Chen",
        },
        "variations": [
            {"field_1": "Through Broken Glass", "field_2": "S. Chen"},
            {"field_1": "Thru Broken Glass", "field_2": "Sophia Chen"},
        ],
        "popularity_weight": 4,
    },
    {
        "canonical": {
            "field_1": "The Copper Mask",
            "field_2": "Elijah Brown",
        },
        "variations": [
            {"field_1": "Copper Mask", "field_2": "Elijah Brown"},
            {"field_1": "The Copper Mask", "field_2": "E. Brown"},
        ],
        "popularity_weight": 3,
    },
]

# Short Story - field_1: Title, field_2: Author
SAMPLE_SHORT_STORIES = [
    {
        "canonical": {
            "field_1": "The Rain Remembers",
            "field_2": "Alice Johnson",
        },
        "variations": [
            {"field_1": "Rain Remembers", "field_2": "Alice Johnson"},
            {"field_1": "The Rain Remembers", "field_2": "A. Johnson"},
            {"field_1": "The Rain Remember", "field_2": "Alice Johnson"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {
            "field_1": "Ghost in the Machine",
            "field_2": "Kevin Murphy",
        },
        "variations": [
            {"field_1": "Ghost In The Machine", "field_2": "Kevin Murphy"},
            {"field_1": "Ghost in the Machine", "field_2": "K. Murphy"},
            {"field_1": "The Ghost in the Machine", "field_2": "Kevin Murphy"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {
            "field_1": "Paper Wings",
            "field_2": "Mei Lin",
        },
        "variations": [
            {"field_1": "Paper Wings", "field_2": "M. Lin"},
            {"field_1": "Paper Wing", "field_2": "Mei Lin"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {
            "field_1": "The Lighthouse Keeper",
            "field_2": "Omar Farah",
        },
        "variations": [
            {"field_1": "Lighthouse Keeper", "field_2": "Omar Farah"},
            {"field_1": "The Lighthouse Keeper", "field_2": "O. Farah"},
            {"field_1": "The Light House Keeper", "field_2": "Omar Farah"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {
            "field_1": "Digital Ghosts",
            "field_2": "Rebecca Taylor",
        },
        "variations": [
            {"field_1": "Digital Ghosts", "field_2": "R. Taylor"},
            {"field_1": "Digital Ghost", "field_2": "Rebecca Taylor"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {
            "field_1": "The Last Bloom",
            "field_2": "Andre Costa",
        },
        "variations": [
            {"field_1": "Last Bloom", "field_2": "Andre Costa"},
            {"field_1": "The Last Bloom", "field_2": "A. Costa"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {
            "field_1": "Silver Lining",
            "field_2": "Hannah Schmidt",
        },
        "variations": [
            {"field_1": "Silver Lining", "field_2": "H. Schmidt"},
            {"field_1": "The Silver Lining", "field_2": "Hannah Schmidt"},
        ],
        "popularity_weight": 6,
    },
    {
        "canonical": {
            "field_1": "Echoes of Tomorrow",
            "field_2": "Jamal Wright",
        },
        "variations": [
            {"field_1": "Echoes Of Tomorrow", "field_2": "Jamal Wright"},
            {"field_1": "Echoes of Tomorrow", "field_2": "J. Wright"},
        ],
        "popularity_weight": 6,
    },
    {
        "canonical": {
            "field_1": "The Quantum Rose",
            "field_2": "Leila Abbas",
        },
        "variations": [
            {"field_1": "Quantum Rose", "field_2": "Leila Abbas"},
            {"field_1": "The Quantum Rose", "field_2": "L. Abbas"},
        ],
        "popularity_weight": 5,
    },
    {
        "canonical": {
            "field_1": "Starlight Sonata",
            "field_2": "Felix Novak",
        },
        "variations": [
            {"field_1": "Starlight Sonata", "field_2": "F. Novak"},
            {"field_1": "Star Light Sonata", "field_2": "Felix Novak"},
        ],
        "popularity_weight": 5,
    },
]

# Series - field_1: Series Name, field_2: Author(s)
SAMPLE_SERIES = [
    {
        "canonical": {
            "field_1": "The Broken Earth Saga",
            "field_2": "Victoria Stone",
        },
        "variations": [
            {"field_1": "Broken Earth Saga", "field_2": "Victoria Stone"},
            {"field_1": "The Broken Earth Saga", "field_2": "V. Stone"},
            {"field_1": "The Broken Earth", "field_2": "Victoria Stone"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {
            "field_1": "Chronicles of the Void",
            "field_2": "Marcus Bell",
        },
        "variations": [
            {"field_1": "Chronicles Of The Void", "field_2": "Marcus Bell"},
            {"field_1": "Chronicles of the Void", "field_2": "M. Bell"},
            {"field_1": "The Chronicles of the Void", "field_2": "Marcus Bell"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {
            "field_1": "The Wayfarers Series",
            "field_2": "Becky Chambers",
        },
        "variations": [
            {"field_1": "Wayfarers Series", "field_2": "Becky Chambers"},
            {"field_1": "The Wayfarers", "field_2": "Becky Chambers"},
            {"field_1": "The Wayfarers Series", "field_2": "B. Chambers"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {
            "field_1": "Imperial Radch",
            "field_2": "Ann Leckie",
        },
        "variations": [
            {"field_1": "The Imperial Radch", "field_2": "Ann Leckie"},
            {"field_1": "Imperial Radch Series", "field_2": "Ann Leckie"},
            {"field_1": "Imperial Radch", "field_2": "A. Leckie"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {
            "field_1": "The Expanse",
            "field_2": "James S.A. Corey",
        },
        "variations": [
            {"field_1": "Expanse", "field_2": "James S.A. Corey"},
            {"field_1": "The Expanse Series", "field_2": "James S.A. Corey"},
            {"field_1": "The Expanse", "field_2": "James SA Corey"},
        ],
        "popularity_weight": 7,
    },
]

# Dramatic Presentation (Long Form) - field_1: Title, field_2: Production Company/Studio
SAMPLE_DRAMATIC_LONG = [
    {
        "canonical": {
            "field_1": "Echoes from the Void",
            "field_2": "Constellation Pictures",
        },
        "variations": [
            {"field_1": "Echoes From The Void", "field_2": "Constellation Pictures"},
            {"field_1": "Echoes from the Void", "field_2": "Constellation Pics"},
            {"field_1": "Echo from the Void", "field_2": "Constellation Pictures"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {
            "field_1": "The Last Frontier",
            "field_2": "Stellar Productions",
        },
        "variations": [
            {"field_1": "Last Frontier", "field_2": "Stellar Productions"},
            {"field_1": "The Last Frontier", "field_2": "Stellar Prods"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {
            "field_1": "Quantum Dreams",
            "field_2": "Nebula Studios",
        },
        "variations": [
            {"field_1": "Quantum Dreams", "field_2": "Nebula Studio"},
            {"field_1": "Quantum Dream", "field_2": "Nebula Studios"},
        ],
        "popularity_weight": 8,
    },
]

# Dramatic Presentation (Short Form) - field_1: Episode Title, field_2: Series Name, field_3: Production Company
SAMPLE_DRAMATIC_SHORT = [
    {
        "canonical": {
            "field_1": "The Empty Chair",
            "field_2": "Starlight Chronicles",
            "field_3": "Cosmos Entertainment",
        },
        "variations": [
            {
                "field_1": "The Empty Chair",
                "field_2": "Starlight Chronicles",
                "field_3": "Cosmos Ent",
            },
            {
                "field_1": "Empty Chair",
                "field_2": "Starlight Chronicles",
                "field_3": "Cosmos Entertainment",
            },
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {
            "field_1": "Signal Lost",
            "field_2": "Deep Space Nine",
            "field_3": "Paramount Television",
        },
        "variations": [
            {
                "field_1": "Signal Lost",
                "field_2": "Deep Space Nine",
                "field_3": "Paramount TV",
            },
            {
                "field_1": "Signal Lost",
                "field_2": "DS9",
                "field_3": "Paramount Television",
            },
        ],
        "popularity_weight": 9,
    },
]

# Related Work - field_1: Title, field_2: Author/Creator
SAMPLE_RELATED_WORKS = [
    {
        "canonical": {
            "field_1": "The Science of Worldbuilding",
            "field_2": "Dr. Sarah Chen",
        },
        "variations": [
            {"field_1": "Science of Worldbuilding", "field_2": "Dr. Sarah Chen"},
            {"field_1": "The Science of Worldbuilding", "field_2": "Sarah Chen"},
            {"field_1": "The Science of World-building", "field_2": "Dr. Sarah Chen"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {
            "field_1": "History of Science Fiction Podcast",
            "field_2": "Mark Johnson",
        },
        "variations": [
            {"field_1": "History of Science Fiction Podcast", "field_2": "M. Johnson"},
            {"field_1": "History of SF Podcast", "field_2": "Mark Johnson"},
        ],
        "popularity_weight": 9,
    },
]

# Graphic Story/Comic - field_1: Title, field_2: Author, field_3: Artist
SAMPLE_GRAPHIC_STORIES = [
    {
        "canonical": {
            "field_1": "The Broken World",
            "field_2": "Emma Stone",
            "field_3": "Lucas Martinez",
        },
        "variations": [
            {
                "field_1": "Broken World",
                "field_2": "Emma Stone",
                "field_3": "Lucas Martinez",
            },
            {
                "field_1": "The Broken World",
                "field_2": "E. Stone",
                "field_3": "Lucas Martinez",
            },
            {
                "field_1": "The Broken World",
                "field_2": "Emma Stone",
                "field_3": "L. Martinez",
            },
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {
            "field_1": "Nebula Rising",
            "field_2": "Jordan Lee",
            "field_3": "Aiko Tanaka",
        },
        "variations": [
            {"field_1": "Nebula Rising", "field_2": "J. Lee", "field_3": "Aiko Tanaka"},
            {
                "field_1": "Nebula Rising",
                "field_2": "Jordan Lee",
                "field_3": "A. Tanaka",
            },
        ],
        "popularity_weight": 9,
    },
]

# Best Game or Interactive Work - field_1: Title, field_2: Developer
SAMPLE_GAMES = [
    {
        "canonical": {"field_1": "Starbound Odyssey", "field_2": "Nebula Interactive"},
        "variations": [
            {"field_1": "Starbound Odyssey", "field_2": "Nebula Int."},
            {"field_1": "Star Bound Odyssey", "field_2": "Nebula Interactive"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {"field_1": "Chrono Rifts", "field_2": "Temporal Studios"},
        "variations": [
            {"field_1": "Chrono Rifts", "field_2": "Temporal Studio"},
            {"field_1": "ChronoRifts", "field_2": "Temporal Studios"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {"field_1": "The Last Colony", "field_2": "Asimov Games"},
        "variations": [
            {"field_1": "Last Colony", "field_2": "Asimov Games"},
            {"field_1": "The Last Colony", "field_2": "Asimov Game Studio"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {"field_1": "Void Explorer", "field_2": "Deep Space Interactive"},
        "variations": [
            {"field_1": "Void Explorer", "field_2": "Deep Space Int."},
            {"field_1": "VoidExplorer", "field_2": "Deep Space Interactive"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {"field_1": "Quantum Paradox", "field_2": "Heisenberg Studios"},
        "variations": [
            {"field_1": "Quantum Paradox", "field_2": "Heisenberg Studio"},
            {"field_1": "The Quantum Paradox", "field_2": "Heisenberg Studios"},
        ],
        "popularity_weight": 6,
    },
]

# Best Editor - Short Form - field_1: Editor Name
SAMPLE_EDITORS_SHORT = [
    {
        "canonical": {"field_1": "Ellen Datlow"},
        "variations": [
            {"field_1": "E. Datlow"},
            {"field_1": "Ellen M. Datlow"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {"field_1": "Gardner Dozois"},
        "variations": [
            {"field_1": "G. Dozois"},
            {"field_1": "Gardner R. Dozois"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {"field_1": "Neil Clarke"},
        "variations": [
            {"field_1": "N. Clarke"},
            {"field_1": "Neil C. Clarke"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {"field_1": "Jonathan Strahan"},
        "variations": [
            {"field_1": "J. Strahan"},
            {"field_1": "Jonathan A. Strahan"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {"field_1": "John Joseph Adams"},
        "variations": [
            {"field_1": "J.J. Adams"},
            {"field_1": "John Adams"},
        ],
        "popularity_weight": 6,
    },
]

# Best Editor - Long Form - field_1: Editor Name
SAMPLE_EDITORS_LONG = [
    {
        "canonical": {"field_1": "Sheila E. Gilbert"},
        "variations": [
            {"field_1": "S. Gilbert"},
            {"field_1": "Sheila Gilbert"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {"field_1": "Patrick Nielsen Hayden"},
        "variations": [
            {"field_1": "P. Nielsen Hayden"},
            {"field_1": "Patrick N. Hayden"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {"field_1": "Liz Gorinsky"},
        "variations": [
            {"field_1": "L. Gorinsky"},
            {"field_1": "Elizabeth Gorinsky"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {"field_1": "Joe Monti"},
        "variations": [
            {"field_1": "J. Monti"},
            {"field_1": "Joseph Monti"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {"field_1": "Betsy Wollheim"},
        "variations": [
            {"field_1": "B. Wollheim"},
            {"field_1": "Betsy W. Wollheim"},
        ],
        "popularity_weight": 6,
    },
]

# Best Professional Artist - field_1: Artist Name, field_2: Example
SAMPLE_PROFESSIONAL_ARTISTS = [
    {
        "canonical": {"field_1": "Julie Dillon", "field_2": "Cover art for 'Starborn'"},
        "variations": [
            {"field_1": "J. Dillon", "field_2": "Cover art for 'Starborn'"},
            {"field_1": "Julie Dillon", "field_2": "Starborn cover art"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {
            "field_1": "John Picacio",
            "field_2": "Cover art for 'The Expanse'",
        },
        "variations": [
            {"field_1": "J. Picacio", "field_2": "Cover art for 'The Expanse'"},
            {"field_1": "John Picacio", "field_2": "The Expanse cover"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {
            "field_1": "Galen Dara",
            "field_2": "Interior art for 'Lightspeed'",
        },
        "variations": [
            {"field_1": "G. Dara", "field_2": "Interior art for 'Lightspeed'"},
            {"field_1": "Galen Dara", "field_2": "Lightspeed magazine art"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {"field_1": "Victo Ngai", "field_2": "Cover for 'Clarkesworld'"},
        "variations": [
            {"field_1": "V. Ngai", "field_2": "Cover for 'Clarkesworld'"},
            {"field_1": "Victo Ngai", "field_2": "Clarkesworld cover art"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {
            "field_1": "Charles Vess",
            "field_2": "Illustrations for 'Stardust'",
        },
        "variations": [
            {"field_1": "C. Vess", "field_2": "Illustrations for 'Stardust'"},
            {"field_1": "Charles Vess", "field_2": "Stardust illustrations"},
        ],
        "popularity_weight": 6,
    },
]

# Best Semiprozine - field_1: Title
SAMPLE_SEMIPROZINES = [
    {
        "canonical": {"field_1": "Clarkesworld Magazine"},
        "variations": [
            {"field_1": "Clarkesworld"},
            {"field_1": "Clarkes World Magazine"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {"field_1": "Lightspeed Magazine"},
        "variations": [
            {"field_1": "Lightspeed"},
            {"field_1": "Light Speed Magazine"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {"field_1": "Uncanny Magazine"},
        "variations": [
            {"field_1": "Uncanny"},
            {"field_1": "The Uncanny Magazine"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {"field_1": "Strange Horizons"},
        "variations": [
            {"field_1": "Strange Horizon"},
            {"field_1": "StrangeHorizons"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {"field_1": "Beneath Ceaseless Skies"},
        "variations": [
            {"field_1": "Beneath Ceasless Skies"},
            {"field_1": "BCS"},
        ],
        "popularity_weight": 6,
    },
]

# Best Fanzine - field_1: Title
SAMPLE_FANZINES = [
    {
        "canonical": {"field_1": "Journey Planet"},
        "variations": [
            {"field_1": "JourneyPlanet"},
            {"field_1": "The Journey Planet"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {"field_1": "Lady Business"},
        "variations": [
            {"field_1": "LadyBusiness"},
            {"field_1": "The Lady Business"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {"field_1": "Nerds of a Feather, Flock Together"},
        "variations": [
            {"field_1": "Nerds of a Feather"},
            {"field_1": "NoaF, Flock Together"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {"field_1": "File 770"},
        "variations": [
            {"field_1": "File770"},
            {"field_1": "File 770 Fanzine"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {"field_1": "Rocket Stack Rank"},
        "variations": [
            {"field_1": "RocketStackRank"},
            {"field_1": "Rocket Stack"},
        ],
        "popularity_weight": 6,
    },
]

# Best Fancast - field_1: Title
SAMPLE_FANCASTS = [
    {
        "canonical": {"field_1": "The Coode Street Podcast"},
        "variations": [
            {"field_1": "Coode Street Podcast"},
            {"field_1": "Coode St. Podcast"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {"field_1": "Galactic Suburbia"},
        "variations": [
            {"field_1": "GalacticSuburbia"},
            {"field_1": "The Galactic Suburbia"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {"field_1": "The Skiffy and Fanty Show"},
        "variations": [
            {"field_1": "Skiffy and Fanty Show"},
            {"field_1": "Skiffy & Fanty"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {"field_1": "SF Signal Podcast"},
        "variations": [
            {"field_1": "SFSignal Podcast"},
            {"field_1": "SF Signal"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {"field_1": "The Hugos There Podcast"},
        "variations": [
            {"field_1": "Hugos There Podcast"},
            {"field_1": "The Hugo's There"},
        ],
        "popularity_weight": 6,
    },
]

# Best Fan Writer - field_1: Author, field_2: Example
SAMPLE_FAN_WRITERS = [
    {
        "canonical": {
            "field_1": "Foz Meadows",
            "field_2": "Reviews on Strange Horizons",
        },
        "variations": [
            {"field_1": "F. Meadows", "field_2": "Reviews on Strange Horizons"},
            {"field_1": "Foz Meadows", "field_2": "Strange Horizons reviews"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {
            "field_1": "Abigail Nussbaum",
            "field_2": "Asking the Wrong Questions blog",
        },
        "variations": [
            {"field_1": "A. Nussbaum", "field_2": "Asking the Wrong Questions blog"},
            {"field_1": "Abigail Nussbaum", "field_2": "Wrong Questions blog"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {
            "field_1": "Liz Bourke",
            "field_2": "Sleeps With Monsters column",
        },
        "variations": [
            {"field_1": "L. Bourke", "field_2": "Sleeps With Monsters column"},
            {"field_1": "Liz Bourke", "field_2": "Sleeps With Monsters"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {"field_1": "Mike Glyer", "field_2": "File 770 blog"},
        "variations": [
            {"field_1": "M. Glyer", "field_2": "File 770 blog"},
            {"field_1": "Mike Glyer", "field_2": "File770"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {"field_1": "Natalie Luhrs", "field_2": "Pretty Terrible reviews"},
        "variations": [
            {"field_1": "N. Luhrs", "field_2": "Pretty Terrible reviews"},
            {"field_1": "Natalie Luhrs", "field_2": "Pretty Terrible blog"},
        ],
        "popularity_weight": 6,
    },
]

# Best Fan Artist - field_1: Artist Name, field_2: Example
SAMPLE_FAN_ARTISTS = [
    {
        "canonical": {"field_1": "Sara Felix", "field_2": "Convention program covers"},
        "variations": [
            {"field_1": "S. Felix", "field_2": "Convention program covers"},
            {"field_1": "Sara Felix", "field_2": "Con program covers"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {"field_1": "Steve Stiles", "field_2": "Fanzine cartoons"},
        "variations": [
            {"field_1": "S. Stiles", "field_2": "Fanzine cartoons"},
            {"field_1": "Steve Stiles", "field_2": "Fanzine illustrations"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {
            "field_1": "Maurine Starkey",
            "field_2": "Journey Planet illustrations",
        },
        "variations": [
            {"field_1": "M. Starkey", "field_2": "Journey Planet illustrations"},
            {"field_1": "Maurine Starkey", "field_2": "JourneyPlanet art"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {"field_1": "Dan Steffan", "field_2": "File 770 art"},
        "variations": [
            {"field_1": "D. Steffan", "field_2": "File 770 art"},
            {"field_1": "Dan Steffan", "field_2": "File770 illustrations"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {"field_1": "Alison Scott", "field_2": "Plokta cover art"},
        "variations": [
            {"field_1": "A. Scott", "field_2": "Plokta cover art"},
            {"field_1": "Alison Scott", "field_2": "Plokta covers"},
        ],
        "popularity_weight": 6,
    },
]

# Best Poem - field_1: Title, field_2: Author, field_3: Where Published
SAMPLE_POEMS = [
    {
        "canonical": {
            "field_1": "The Stars Between",
            "field_2": "Ada Palmer",
            "field_3": "Strange Horizons",
        },
        "variations": [
            {
                "field_1": "Stars Between",
                "field_2": "Ada Palmer",
                "field_3": "Strange Horizons",
            },
            {
                "field_1": "The Stars Between",
                "field_2": "A. Palmer",
                "field_3": "Strange Horizons",
            },
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {
            "field_1": "When the Robots Dream",
            "field_2": "Ursula Vernon",
            "field_3": "Uncanny Magazine",
        },
        "variations": [
            {
                "field_1": "When Robots Dream",
                "field_2": "Ursula Vernon",
                "field_3": "Uncanny Magazine",
            },
            {
                "field_1": "When the Robots Dream",
                "field_2": "U. Vernon",
                "field_3": "Uncanny",
            },
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {
            "field_1": "Elegy for Lost Worlds",
            "field_2": "Amal El-Mohtar",
            "field_3": "Lightspeed Magazine",
        },
        "variations": [
            {
                "field_1": "Elegy for Lost Worlds",
                "field_2": "A. El-Mohtar",
                "field_3": "Lightspeed Magazine",
            },
            {
                "field_1": "Elegy for Lost Worlds",
                "field_2": "Amal El-Mohtar",
                "field_3": "Lightspeed",
            },
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {
            "field_1": "Song of the Void",
            "field_2": "Yoon Ha Lee",
            "field_3": "Clarkesworld Magazine",
        },
        "variations": [
            {
                "field_1": "Song of the Void",
                "field_2": "Y. H. Lee",
                "field_3": "Clarkesworld Magazine",
            },
            {
                "field_1": "Song of the Void",
                "field_2": "Yoon Ha Lee",
                "field_3": "Clarkesworld",
            },
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {
            "field_1": "The Last Astronaut",
            "field_2": "Jane Yolen",
            "field_3": "Tor.com",
        },
        "variations": [
            {
                "field_1": "Last Astronaut",
                "field_2": "Jane Yolen",
                "field_3": "Tor.com",
            },
            {
                "field_1": "The Last Astronaut",
                "field_2": "J. Yolen",
                "field_3": "Tor",
            },
        ],
        "popularity_weight": 6,
    },
]

# Astounding Award for Best New Writer - field_1: Author, field_2: Example
SAMPLE_NEW_WRITERS = [
    {
        "canonical": {
            "field_1": "Rivers Solomon",
            "field_2": "An Unkindness of Ghosts",
        },
        "variations": [
            {"field_1": "R. Solomon", "field_2": "An Unkindness of Ghosts"},
            {"field_1": "Rivers Solomon", "field_2": "Unkindness of Ghosts"},
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {"field_1": "P. Djèlí Clark", "field_2": "The Black God's Drums"},
        "variations": [
            {"field_1": "P. D. Clark", "field_2": "The Black God's Drums"},
            {"field_1": "P. Djèlí Clark", "field_2": "Black God's Drums"},
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {"field_1": "Rebecca Roanhorse", "field_2": "Trail of Lightning"},
        "variations": [
            {"field_1": "R. Roanhorse", "field_2": "Trail of Lightning"},
            {"field_1": "Rebecca Roanhorse", "field_2": "Trail Of Lightning"},
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {"field_1": "Tade Thompson", "field_2": "Rosewater"},
        "variations": [
            {"field_1": "T. Thompson", "field_2": "Rosewater"},
            {"field_1": "Tade Thompson", "field_2": "Rose Water"},
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {"field_1": "Jeannette Ng", "field_2": "Under the Pendulum Sun"},
        "variations": [
            {"field_1": "J. Ng", "field_2": "Under the Pendulum Sun"},
            {"field_1": "Jeannette Ng", "field_2": "Under The Pendulum Sun"},
        ],
        "popularity_weight": 6,
    },
]

# Expanded Related Works - field_1: Title, field_2: Author/Creator, field_3: Publisher
SAMPLE_RELATED_WORKS_EXPANDED = [
    {
        "canonical": {
            "field_1": "The Science of Worldbuilding",
            "field_2": "Dr. Sarah Chen",
            "field_3": "Orbit Books",
        },
        "variations": [
            {
                "field_1": "Science of Worldbuilding",
                "field_2": "Dr. Sarah Chen",
                "field_3": "Orbit Books",
            },
            {
                "field_1": "The Science of Worldbuilding",
                "field_2": "Sarah Chen",
                "field_3": "Orbit",
            },
        ],
        "popularity_weight": 10,
    },
    {
        "canonical": {
            "field_1": "History of Science Fiction Podcast",
            "field_2": "Mark Johnson",
            "field_3": "Independent",
        },
        "variations": [
            {
                "field_1": "History of Science Fiction Podcast",
                "field_2": "M. Johnson",
                "field_3": "Independent",
            },
            {
                "field_1": "History of SF Podcast",
                "field_2": "Mark Johnson",
                "field_3": "Indie",
            },
        ],
        "popularity_weight": 9,
    },
    {
        "canonical": {
            "field_1": "The Hugo Awards: A Retrospective",
            "field_2": "Jo Walton",
            "field_3": "Tor Books",
        },
        "variations": [
            {
                "field_1": "Hugo Awards: A Retrospective",
                "field_2": "Jo Walton",
                "field_3": "Tor Books",
            },
            {
                "field_1": "The Hugo Awards: A Retrospective",
                "field_2": "J. Walton",
                "field_3": "Tor",
            },
        ],
        "popularity_weight": 8,
    },
    {
        "canonical": {
            "field_1": "Designing Fantasy Characters",
            "field_2": "Alison Lee",
            "field_3": "Impact Books",
        },
        "variations": [
            {
                "field_1": "Designing Fantasy Characters",
                "field_2": "A. Lee",
                "field_3": "Impact Books",
            },
            {
                "field_1": "Designing Fantasy Chars",
                "field_2": "Alison Lee",
                "field_3": "Impact",
            },
        ],
        "popularity_weight": 7,
    },
    {
        "canonical": {
            "field_1": "Women in Science Fiction: An Oral History",
            "field_2": "Farah Mendlesohn",
            "field_3": "Liverpool University Press",
        },
        "variations": [
            {
                "field_1": "Women in Science Fiction",
                "field_2": "Farah Mendlesohn",
                "field_3": "Liverpool University Press",
            },
            {
                "field_1": "Women in Science Fiction: An Oral History",
                "field_2": "F. Mendlesohn",
                "field_3": "Liverpool UP",
            },
        ],
        "popularity_weight": 6,
    },
    {
        "canonical": {
            "field_1": "The Art of Star Trek",
            "field_2": "Judith and Garfield Reeves-Stevens",
            "field_3": "Pocket Books",
        },
        "variations": [
            {
                "field_1": "Art of Star Trek",
                "field_2": "Judith and Garfield Reeves-Stevens",
                "field_3": "Pocket Books",
            },
            {
                "field_1": "The Art of Star Trek",
                "field_2": "J. and G. Reeves-Stevens",
                "field_3": "Pocket",
            },
        ],
        "popularity_weight": 5,
    },
    {
        "canonical": {
            "field_1": "From the Annals of Nephelokokkygia: A Fanzine Retrospective",
            "field_2": "Claire Brialey & Mark Plummer",
            "field_3": "Self-published",
        },
        "variations": [
            {
                "field_1": "From the Annals of Nephelokokkygia",
                "field_2": "Claire Brialey & Mark Plummer",
                "field_3": "Self-published",
            },
            {
                "field_1": "From the Annals of Nephelokokkygia: A Fanzine Retrospective",
                "field_2": "C. Brialey & M. Plummer",
                "field_3": "Self-pub",
            },
        ],
        "popularity_weight": 5,
    },
]


# Category name mappings - maps category keywords to sample data lists
# Each entry is a tuple of (required_keywords, excluded_keywords, sample_list)
# The function will check if all required keywords are in the category name
# and none of the excluded keywords are present
CATEGORY_MAPPINGS = [
    # Order matters - more specific patterns first
    (["dramatic", "long"], [], SAMPLE_DRAMATIC_LONG),
    (["dramatic", "short"], [], SAMPLE_DRAMATIC_SHORT),
    (["novel"], ["novella"], SAMPLE_NOVELS),  # Exclude novella to avoid matching it
    (["novella"], [], SAMPLE_NOVELLAS),
    (["novelette"], [], SAMPLE_NOVELETTES),
    (["short story"], [], SAMPLE_SHORT_STORIES),
    (["series"], [], SAMPLE_SERIES),
    (["related work"], [], SAMPLE_RELATED_WORKS_EXPANDED),
    (["graphic"], [], SAMPLE_GRAPHIC_STORIES),
    (["game", "interactive"], [], SAMPLE_GAMES),
    (["game"], [], SAMPLE_GAMES),  # Fallback for just "game"
    (["editor", "short"], [], SAMPLE_EDITORS_SHORT),
    (["editor", "long"], [], SAMPLE_EDITORS_LONG),
    (["professional artist"], [], SAMPLE_PROFESSIONAL_ARTISTS),
    (["semiprozine"], [], SAMPLE_SEMIPROZINES),
    (["fanzine"], [], SAMPLE_FANZINES),
    (["fancast"], [], SAMPLE_FANCASTS),
    (["fan writer"], [], SAMPLE_FAN_WRITERS),
    (["fan artist"], [], SAMPLE_FAN_ARTISTS),
    (["poem"], [], SAMPLE_POEMS),
    (["lodestar"], [], SAMPLE_NOVELS),  # Lodestar Award uses novels (YA books)
    (["astounding", "new writer"], [], SAMPLE_NEW_WRITERS),
    (["astounding"], [], SAMPLE_NEW_WRITERS),  # Fallback for just "Astounding"
]


def get_samples_for_category_name(category_name: str) -> list[dict]:
    """
    Return the appropriate sample works list based on category name.

    Args:
        category_name: The name of the category (e.g., "Best Novel", "Novel")

    Returns:
        List of sample works with canonical forms and variations
    """
    category_lower = category_name.lower()

    # Check each mapping pattern
    for required_keywords, excluded_keywords, sample_list in CATEGORY_MAPPINGS:
        # Check if all required keywords are present
        has_required = all(keyword in category_lower for keyword in required_keywords)

        # Check if any excluded keywords are present
        has_excluded = any(keyword in category_lower for keyword in excluded_keywords)

        if has_required and not has_excluded:
            return sample_list

    # Default to novels if we can't determine the category
    return SAMPLE_NOVELS

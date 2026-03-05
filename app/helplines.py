"""
app/helplines.py — Central configuration for all crisis helplines.

Edit this file to customize every helpline shown across the entire app:
  - Wellness Hub cards
  - Chat page crisis footer
  - LLM crisis escalation message
  - Base template navbar footer

Each helpline is a dict with these keys:
  name     : Display name of the service
  number   : Phone number string (used for tel: links)
  display  : Human-readable number shown in UI (e.g. "1800-599-0019")
  url      : Optional website URL (None if not applicable)
  hours    : Availability description
  emoji    : Emoji icon for visual identification
"""

# ── YOUR HELPLINES ────────────────────────────────────────────────────────────
# Add, remove, or edit entries here. All templates read from this list.

HELPLINES = [
    {
        "name":    "iCall – TISS",
        "number":  "9152987821",
        "display": "91529-87821",
        "url":     "https://icallhelpline.org",
        "hours":   "Mon–Sat, 8 AM – 10 PM",
        "emoji":   "📞",
    },
    {
        "name":    "Vandrevala Foundation",
        "number":  "18602662345",
        "display": "1860-2662-345",
        "url":     "https://www.vandrevalafoundation.com",
        "hours":   "24/7 Free",
        "emoji":   "🆘",
    },
    {
        "name":    "Snehi India",
        "number":  "044-24640050",
        "display": "044-24640050",
        "url":     "https://snehiindia.org",
        "hours":   "Daily 8 AM – 10 PM",
        "emoji":   "💚",
    },
    {
        "name":    "NIMHANS Mental Health",
        "number":  "08046110007",
        "display": "080-4611-0007",
        "url":     "https://nimhans.ac.in",
        "hours":   "Mon–Sat, 9 AM – 5 PM",
        "emoji":   "🏥",
    },
    {
        "name":    "Fortis Stress Helpline",
        "number":  "8376804102",
        "display": "8376-804-102",
        "url":     None,
        "hours":   "24/7",
        "emoji":   "🌟",
    },
    {
        "name":    "International Crisis Centres (IASP)",
        "number":  None,
        "display": None,
        "url":     "https://www.iasp.info/resources/Crisis_Centres/",
        "hours":   "Global directory",
        "emoji":   "🌍",
    },
]

# ── PRIMARY helpline (shown in compact footers & LLM messages) ─────────────
# Update these two if you change your main helpline.
PRIMARY_NAME = "Ashwath"
PRIMARY_NUMBER = "9443205398"
SECONDARY_NAME = "Gokul"
SECONDARY_NUMBER = "8682033021"

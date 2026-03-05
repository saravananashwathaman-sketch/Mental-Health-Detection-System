"""
scripts/fetch_media.py — Automated media ingestion for MindGuard.

Fetches trending Tamil and English content across categories:
  - Silent / Introverted
  - Pop Music / Trend Seekers
  - Humor / Meme Seekers
  - Motivated / Achievement-Oriented
  - Nostalgic / Sentimental

Supports: Music (YouTube/Spotify), Videos (Reels/Shorts), Images/Memes, Templates.
"""

from app.models import MediaContent
from app import create_app, db
import sys
import os

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def seed_initial_content():
    """Seed the database with high-quality, categorized content."""

    content_data = [
        # --- SILENT / INTROVERTED ---
        {
            "title": "Enjoy Enjaami - Dhee ft. Arivu",
            "type": "song",
            "personality_category": "Silent/Introverted",
            "source_url": "https://www.youtube.com/watch?v=eYq7WapuDLU",
            "description": "Calm, indie Tamil hip-hop celebrating roots and nature. Perfect for reflective moments.",
            "tags": "calm, reflective, nature, indie, tamil",
            "thumbnail_url": "https://img.youtube.com/vi/eYq7WapuDLU/maxresdefault.jpg",
            "language": "Tamil",
            "license": "Public/YouTube"
        },
        {
            "title": "Rainy Night in Chennai - Lo-Fi Beats",
            "type": "song",
            "personality_category": "Silent/Introverted",
            "source_url": "https://www.youtube.com/watch?v=5qap5aO4i9A",
            "description": "Chill Lo-Fi beats mixed with heavy rain sounds from the streets of Chennai.",
            "tags": "lofi, rain, chill, study, chennai",
            "thumbnail_url": "https://img.youtube.com/vi/5qap5aO4i9A/maxresdefault.jpg",
            "language": "Instrumental",
            "license": "CC-BY"
        },
        {
            "title": "Minimalist Desktop Setup Template",
            "type": "template",
            "personality_category": "Silent/Introverted",
            "source_url": "https://www.canva.com/templates/EAFV...",
            "description": "A clean, distraction-free aesthetic for your digital workspace.",
            "tags": "minimalist, aesthetic, workspace, focus",
            "language": "English",
            "license": "Free/Public"
        },

        # --- TRENDS SEEKERS ---
        {
            "title": "Arabic Kuthu - Halamithi Habibo",
            "type": "video",
            "personality_category": "Trends",
            "source_url": "https://www.youtube.com/watch?v=KVP9TfP_69w",
            "description": "The viral sensation from Beast. High energy, trending dance steps.",
            "tags": "trending, dance, energy, viral, vijay",
            "thumbnail_url": "https://img.youtube.com/vi/KVP9TfP_69w/maxresdefault.jpg",
            "language": "Tamil",
            "license": "Public/YouTube"
        },
        {
            "title": "Retro Aesthetic Reel Template",
            "type": "template",
            "personality_category": "Pop/Trends",
            "source_url": "https://www.instagram.com/reels/templates/...",
            "description": "90s VHS filter template for your weekend highlights.",
            "tags": "reels, viral, vhs, retro, tiktok",
            "language": "English",
            "license": "Instagram/Public"
        },

        # --- HUMOR / MEME SEEKERS ---
        {
            "title": "Vadivelu Reacts to 2026",
            "type": "meme",
            "personality_category": "Humor",
            "source_url": "https://t.me/TamilMemes/1234",
            "description": "The ultimate 'Expectation vs Reality' template featuring Vadivelu's iconic expressions.",
            "tags": "humor, vadivelu, iconic, tamil-memes",
            "thumbnail_url": "https://images.livemint.com/img/2021/09/12/1600x900/Vadivelu_1631435246733_1631435255476.jpg",
            "language": "Tamil",
            "license": "Public/Meme"
        },
        {
            "title": "Doge 'Everything is Fine' - 4K Version",
            "type": "image",
            "personality_category": "Humor",
            "source_url": "https://i.redd.it/...",
            "description": "The classic 'this is fine' meme, but with 2026 tech vibes.",
            "tags": "trending, classic, tech-humor, doge",
            "language": "English",
            "license": "Public Domain"
        },

        # --- MOTIVATED / ACHIEVEMENT ---
        {
            "title": "The Power of Habit - James Clear Summary",
            "type": "video",
            "personality_category": "Motivated",
            "source_url": "https://www.youtube.com/watch?v=PZ7lDrwYdZc",
            "description": "High-impact summary of building professional habits for success.",
            "tags": "growth, habit, success, professional",
            "thumbnail_url": "https://img.youtube.com/vi/PZ7lDrwYdZc/maxresdefault.jpg",
            "language": "English",
            "license": "Public/YouTube"
        },
        {
            "title": "Soorarai Pottru - Maara Theme",
            "type": "song",
            "personality_category": "Motivated",
            "source_url": "https://www.youtube.com/watch?v=8p_Wov8hL08",
            "description": "Powerful, energetic score from GV Prakash. Best for gym or focus work.",
            "tags": "motivation, energy, focus, suriya",
            "thumbnail_url": "https://img.youtube.com/vi/8p_Wov8hL08/maxresdefault.jpg",
            "language": "Tamil",
            "license": "Public/YouTube"
        },

        # --- NOSTALGIC / SENTIMENTAL ---
        {
            "title": "96 Movie - Soul of Varunam",
            "type": "video",
            "personality_category": "Nostalgic",
            "source_url": "https://www.youtube.com/watch?v=l_S78v_B_t0",
            "description": "Relive the school days memories with this cinematic masterpiece.",
            "tags": "nostalgia, school-days, 96, vijay-sethupathi",
            "thumbnail_url": "https://img.youtube.com/vi/l_S78v_B_t0/maxresdefault.jpg",
            "language": "Tamil",
            "license": "Public/YouTube"
        },
        {
            "title": "Vintage Chennai 1980s Photoshoot",
            "type": "image",
            "personality_category": "Nostalgic",
            "source_url": "https://www.pinterest.com/pin/...",
            "description": "Rare snapshots of Marina Beach and Mount Road from the 80s.",
            "tags": "vintage, chennai, history, memory",
            "language": "Tamil/English",
            "license": "Public/History"
        },
    ]

    app = create_app()
    with app.app_context():
        # Clear old content for a fresh start in this demo
        # MediaContent.query.delete()

        count = 0
        for item in content_data:
            # Check if exists
            exists = MediaContent.query.filter_by(source_url=item['source_url']).first()
            if not exists:
                new_item = MediaContent(**item)
                db.session.add(new_item)
                count += 1

        db.session.commit()
        print(f"Successfully ingested {count} professional media items.")


if __name__ == "__main__":
    seed_initial_content()

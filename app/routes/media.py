"""
app/routes/media.py — Media Dashboard blueprint.

Routes:
  GET /media                  → main dashboard page
  GET /media/category/<cat>    → filter by personality category
  GET /media/type/<type>       → filter by content type
"""

from flask import Blueprint, render_template
from app.models import MediaContent
from app.routes.auth import login_required

media_bp = Blueprint("media", __name__, url_prefix="/media")


@media_bp.route("/")
@login_required
def index():
    """Render the main media dashboard."""
    # Group by category for the 'Explore' section
    categories = ["Silent/Introverted", "Trends", "Humor", "Motivated", "Nostalgic"]

    # Fetch recent items for each category (preview)
    sections = {}
    for cat in categories:
        sections[cat] = MediaContent.query.filter_by(personality_category=cat).limit(4).all()

    # Also fetch all for the main grid
    all_content = MediaContent.query.order_by(MediaContent.fetched_at.desc()).limit(20).all()

    return render_template(
        "media/index.html",
        sections=sections,
        all_content=all_content,
        categories=categories
    )


@media_bp.route("/category/<path:category>")
@login_required
def category_view(category):
    """View all content for a specific personality category."""
    # Handle slugs or alternate names
    cat_query = category
    if category.lower() == "trends":
        cat_query = "Trends"

    items = MediaContent.query.filter(MediaContent.personality_category.ilike(f"%{cat_query}%")).order_by(MediaContent.fetched_at.desc()).all()
    return render_template("media/list.html", items=items, title=category.capitalize(), type="Category")


@media_bp.route("/type/<content_type>")
@login_required
def type_view(content_type):
    """View all content of a specific type (e.g., songs, memes)."""
    items = MediaContent.query.filter_by(type=content_type).order_by(MediaContent.fetched_at.desc()).all()
    return render_template("media/list.html", items=items, title=content_type.capitalize(), type="Type")

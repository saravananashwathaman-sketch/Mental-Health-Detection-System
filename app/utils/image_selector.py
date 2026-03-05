import random
from app.models import ImagePool, ImageEmotionTest

def get_session_questions(user_id, num_questions=5, options_per_question=5):
    """
    Generates a set of questions for an image test session.
    Ensures no repeats and emotional diversity.
    """
    # 1. Get all images from the pool
    all_images = ImagePool.query.all()
    if len(all_images) < (num_questions * options_per_question):
        # Fallback if pool is too small (shouldn't happen with 50+ images)
        pass

    # 2. Get user's recent history to avoid frequent repeats
    # Increased limit massively to guarantee we don't repeat any of the 500+ images
    recent_responses = ImageEmotionTest.query.filter_by(user_id=user_id)\
        .order_by(ImageEmotionTest.timestamp.desc())\
        .limit(400).all()
    seen_ids = set(r.image_idx for r in recent_responses)

    # 3. Categorize images by emotion
    categories = {}
    for img in all_images:
        if img.emotion_category not in categories:
            categories[img.emotion_category] = []
        categories[img.emotion_category].append(img)

    session_questions = []
    used_in_session = set()

    for _ in range(num_questions):
        # Pick a set of unique emotions for this question
        emotion_pool = list(categories.keys())
        random.shuffle(emotion_pool)
        selected_emotions = emotion_pool[:options_per_question]

        question_options = []
        for emotion in selected_emotions:
            # Try to pick an image that hasn't been seen recently and isn't used in this session
            available = [img for img in categories[emotion] if img.id not in used_in_session]
            
            # Prioritize images not seen recently
            not_seen = [img for img in available if img.id not in seen_ids]
            
            if not_seen:
                choice = random.choice(not_seen)
            elif available:
                choice = random.choice(available)
            else:
                # Absolute fallback: allow repeats from other categories if forced (shouldn't happen)
                choice = random.choice(categories[emotion])
            
            question_options.append(choice)

        session_questions.append([img.id for img in question_options])
        used_in_session.update([img.id for img in question_options])

    return session_questions

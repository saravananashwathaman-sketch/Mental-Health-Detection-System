"""
app/ai_engine/prediction_engine.py — Mood Prediction Engine.

Combines PHQ-9, GAD-7, Sentiment, Color Mood, and Image Emotion scores.
"""
import random

def predict_mental_health_state(phq9_score, gad7_score, sentiment_score, color_score, image_score, image_max=3):
    """
    Calculates overall mood score, risk level, and concerns.
    
    Scores are expected to be normalized or handled by weight:
    - phq9: 0-27 (Higher is worse) -> Scale to 0-100 (0 is healthy)
    - gad7: 0-21 (Higher is worse) -> Scale to 0-100
    - sentiment: -1.0 to 1.0 (Lower is worse) -> Scale to 0-100 (0 is positive)
    - color: 0-5 (Lower is worse) -> Scale to 0-100
    - image: 0-3 (Lower is worse) -> Scale to 0-100
    """
    
    # Weight configuration (can be tuned)
    # Total weights = 100
    w_phq9 = 0.30
    w_gad7 = 0.25
    w_sentiment = 0.20
    w_color = 0.10
    w_image = 0.15
    
    # Normalize inputs to 0-100 Scale (where 0 is best/healthy)
    norm_phq9 = (phq9_score / 27) * 100
    norm_gad7 = (gad7_score / 21) * 100
    norm_sentiment = ((1 - sentiment_score) / 2) * 100  # -1 -> 100 (unhealthy), 1 -> 0 (healthy)
    norm_color = ((5 - color_score) / 5) * 100         # 0 -> 100, 5 -> 0
    norm_image = ((image_max - image_score) / image_max) * 100 if image_max > 0 else 50
    
    overall_unhealthiness_score = (
        (norm_phq9 * w_phq9) +
        (norm_gad7 * w_gad7) +
        (norm_sentiment * w_sentiment) +
        (norm_color * w_color) +
        (norm_image * w_image)
    )
    
    # Invert to get wellbeing score (0-100, where 100 is best)
    wellbeing_score = 100 - overall_unhealthiness_score
    
    # Determine Risk Level and Category
    if wellbeing_score >= 85:
        risk_level = "GREEN"
        category = "Healthy"
        concerns = random.choice([
            "No significant mental health concerns detected.",
            "Your emotional markers are strong and stable.",
            "Current indicators show a healthy mental state.",
            "You appear to be in a very positive mental space right now."
        ])
        recommendations = random.choice([
            "Continue your current wellness practices. Regular meditation and activity help maintain this state.",
            "Keep up the great work! Engaging in hobbies and staying active will sustain this healthy mindset.",
            "Maintain your healthy routines. Connecting with loved ones is a great way to celebrate your wellbeing.",
            "Your routine is working well. Remember to take time for yourself to rest and recharge."
        ])
    elif wellbeing_score >= 70:
        risk_level = "GREEN"
        category = "Mild Stress"
        concerns = random.choice([
            "Slight indicators of stress or emotional pressure.",
            "Minor signs of mental fatigue or mild anxiousness.",
            "You might be carrying a bit of extra cognitive load right now.",
            "Some very early signs of stress appear present, though manageable."
        ])
        recommendations = random.choice([
            "Consider light exercise, talking to a friend, or our Grounding Exercises in the Wellness Hub.",
            "Taking short breaks throughout your day can help alleviate this mild pressure.",
            "A short walk outside or listening to calming music could be highly beneficial today.",
            "Try a 5-minute mindfulness session from the Wellness Hub to center yourself."
        ])
    elif wellbeing_score >= 50:
        risk_level = "AMBER"
        category = "Moderate Anxiety"
        concerns = random.choice([
            "Noticeable levels of anxiety and emotional fatigue.",
            "Consistent markers of moderate stress and potential burnout.",
            "You seem to be experiencing a notable amount of emotional strain.",
            "Indicators suggest your anxiety levels are higher than usual."
        ])
        recommendations = random.choice([
            "Practice deep breathing (see Wellness Hub). Journaling your thoughts might help identify triggers.",
            "It might be a good time to step back and prioritize self-care. Don't hesitate to lean on your support network.",
            "Consider engaging in a relaxing hobby this evening to help decompress.",
            "The breathing exercises in the Wellness Hub are specifically designed to help lower this level of anxiety."
        ])
    elif wellbeing_score >= 30:
        risk_level = "RED"
        category = "Depression Risk"
        concerns = random.choice([
            "High indicators consistent with depressive symptoms.",
            "Significant emotional distress is apparent in your assessment.",
            "Your results show a heavy emotional burden that needs attention.",
            "High levels of distress and potential depressive markers are present."
        ])
        recommendations = random.choice([
            "We recommend consulting a therapist. Use our crisis helplines if you feel overwhelmed.",
            "Please reach out to a mental health professional. You don't have to carry this alone.",
            "Consider sharing how you feel with a trusted friend or family member today. Professional support is also advised.",
            "It is highly recommended that you speak to a counselor. The helplines in the footer are available 24/7."
        ])
    else:
        risk_level = "RED"
        category = "High Risk Emotional State"
        concerns = random.choice([
            "Multiple severe indicators across assessment types.",
            "Critical levels of emotional distress and burnout.",
            "Your assessment shows acute signs of mental health distress.",
            "Severe depressive or anxious indicators have been flagged."
        ])
        recommendations = random.choice([
            "Please seek immediate professional help or call a crisis hotline found in the footer.",
            "Your wellbeing is priority number one. Please contact a mental health professional right away.",
            "We strongly urge you to call the crisis line listed at the bottom of the page or go to your nearest emergency room.",
            "Please do not wait. Reach out to a professional or helpline immediately for support."
        ])
        
    return {
        "overall_score": wellbeing_score,
        "risk_level": risk_level,
        "category": category,
        "concerns": concerns,
        "recommendations": recommendations
    }

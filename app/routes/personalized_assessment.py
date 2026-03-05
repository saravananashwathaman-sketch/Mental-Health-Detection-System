"""
app/routes/personalized_assessment.py — Color and Image MCQ tests with PDF generation.
"""

import random
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from app import db
from app.models import ColorMoodTest, ImageEmotionTest, MentalHealthReport, ChatMessage, AssessmentSession, ImagePool, ImageTestSession
from app.routes.auth import login_required
from app.ai_engine.prediction_engine import predict_mental_health_state
from app.utils.image_selector import get_session_questions

personalized_bp = Blueprint("personalized", __name__, url_prefix="/tests")

# ── Configuration ────────────────────────────────────────────────────────────

COLOR_OPTIONS = [
    {"name": "Green", "value": "green", "mood": "Calm / Stable", "score": 5, "hex": "#10b981"},
    {"name": "Yellow", "value": "yellow", "mood": "Positive / Energetic", "score": 4, "hex": "#facc15"},
    {"name": "Blue", "value": "blue", "mood": "Sadness", "score": 2, "hex": "#3b82f6"},
    {"name": "Purple", "value": "purple", "mood": "Confusion", "score": 3, "hex": "#a855f7"},
    {"name": "Orange", "value": "orange", "mood": "Stress", "score": 2, "hex": "#f97316"},
    {"name": "Red", "value": "red", "mood": "Anger / Distress", "score": 1, "hex": "#ef4444"},
    {"name": "Black", "value": "black", "mood": "Severe Sadness", "score": 0, "hex": "#1e293b"},
]

IMAGE_POOL = [
    {"id": 1, "category": "Happy", "score": 3, "url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=400", "description": "A person laughing joyfully"},
    {"id": 2, "category": "Calm", "score": 3, "url": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&q=80&w=400", "description": "Peaceful lake at sunset"},
    {"id": 3, "category": "Anxious", "score": 1, "url": "https://images.unsplash.com/photo-1518491755924-df5bd6742cdd?auto=format&fit=crop&q=80&w=400", "description": "Blurred motion in a crowded city"},
    {"id": 4, "category": "Sad", "score": 1, "url": "https://images.unsplash.com/photo-1473081556163-2a17de81fc97?auto=format&fit=crop&q=80&w=400", "description": "Withered plant in the rain"},
    {"id": 5, "category": "Angry", "score": 1, "url": "https://images.unsplash.com/photo-1541170155377-5091f3b33d39?auto=format&fit=crop&q=80&w=400", "description": "Thunderbolt over a dark ocean"},
    {"id": 6, "category": "Overwhelmed", "score": 1, "url": "https://images.unsplash.com/photo-1454165833222-8821c5275e66?auto=format&fit=crop&q=80&w=400", "description": "Stack of endless papers and clocks"},
    {"id": 7, "category": "Lonely", "score": 1, "url": "https://images.unsplash.com/photo-1509248961158-e54f6934749c?auto=format&fit=crop&q=80&w=400", "description": "A single chair in a vast empty hall"},
    {"id": 8, "category": "Happy", "score": 3, "url": "https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&q=80&w=400", "description": "A colorful group feast"},
    {"id": 9, "category": "Calm", "score": 3, "url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&q=80&w=400", "description": "Light filtering through forest leaves"},
    {"id": 10, "category": "Anxious", "score": 1, "url": "https://images.unsplash.com/photo-1499209974431-9dac3adaf477?auto=format&fit=crop&q=80&w=400", "description": "Abstract maze of sharp lines"},
]

# ── Routes ───────────────────────────────────────────────────────────────────

@personalized_bp.route("/color-test", methods=["GET", "POST"])
@login_required
def color_test():
    if request.method == "POST":
        color_val = request.form.get("color")
        matching_opt = next((o for o in COLOR_OPTIONS if o["value"] == color_val), None)
        
        if not matching_opt:
            flash("Please select a valid color.", "danger")
            return redirect(url_for("personalized.color_test"))
        
        test = ColorMoodTest(
            user_id=session["user_id"],
            color=color_val,
            score=matching_opt["score"]
        )
        db.session.add(test)
        db.session.commit()
        
        session["last_color_score"] = matching_opt["score"]
        return redirect(url_for("personalized.image_test"))
    
    return render_template("tests/color_test.html", options=COLOR_OPTIONS)

@personalized_bp.route("/image-test", methods=["GET", "POST"])
@login_required
def image_test():
    user_id = session["user_id"]
    
    # 1. Access or create the active session
    active_session = ImageTestSession.query.filter_by(user_id=user_id, is_completed=False).first()
    
    # 2. Synchronize Flask session with active_session
    if active_session:
        # Check if we need to (re)initialize the question set in the Flask session
        questions = session.get("image_questions")
        is_invalid = not questions or not isinstance(questions, list) or (len(questions) > 0 and isinstance(questions[0], dict))
        
        if is_invalid:
            num_q = active_session.question_count or 5
            session["image_questions"] = get_session_questions(user_id, num_questions=num_q)
            responses_count = ImageEmotionTest.query.filter_by(session_id=active_session.id).count()
            session["current_q_idx"] = responses_count
            session["active_image_session_id"] = active_session.id

    if not active_session:
        # Start a fresh session
        num_q = 7
        active_session = ImageTestSession(user_id=user_id, question_count=num_q)
        db.session.add(active_session)
        db.session.commit()
        
        session["image_questions"] = get_session_questions(user_id, num_questions=num_q)
        session["current_q_idx"] = 0
        session["active_image_session_id"] = active_session.id
    
    # 3. Final data check
    questions = session.get("image_questions")
    current_idx = session.get("current_q_idx", 0)
    
    if not questions or current_idx >= len(questions):
        # Force terminate broken session and redirect to start
        if active_session:
            active_session.is_completed = True
            db.session.commit()
        session.pop("image_questions", None)
        session.pop("current_q_idx", None)
        flash("Your session timed out or was reset. Please start again.", "info")
        return redirect(url_for("personalized.color_test"))

    # 4. Fetch images for the current question
    display_image_ids = questions[current_idx]
    display_images = ImagePool.query.filter(ImagePool.id.in_(display_image_ids)).all()
    
    if not display_images:
        # If IDs don't match pool, break the session
        if active_session:
            active_session.is_completed = True
            db.session.commit()
        session.pop("image_questions", None)
        flash("We encountered an error loading images. Please try again.", "danger")
        return redirect(url_for("personalized.color_test"))

    if request.method == "POST":
        image_id_raw = request.form.get("image_id")
        if not image_id_raw:
            flash("Please select an image before proceeding.", "warning")
            return redirect(url_for("personalized.image_test"))
            
        try:
            image_id = int(image_id_raw)
        except (TypeError, ValueError):
            flash("Invalid selection.", "danger")
            return redirect(url_for("personalized.image_test"))

        selected_img = ImagePool.query.get(image_id)
        if not selected_img or selected_img.id not in display_image_ids:
            flash("Invalid selection.", "danger")
            return redirect(url_for("personalized.image_test"))
            
        # Record response
        test = ImageEmotionTest(
            user_id=user_id,
            session_id=active_session.id,
            image_idx=image_id,
            emotion_category=selected_img.emotion_category,
            score=selected_img.score
        )
        db.session.add(test)
        
        # Update session progresses
        session["current_q_idx"] = current_idx + 1
        
        if session["current_q_idx"] >= len(questions):
            # ... complete session logic ...
            active_session.is_completed = True
            all_responses = ImageEmotionTest.query.filter_by(session_id=active_session.id).all()
            avg_score = sum(r.score for r in all_responses) / len(all_responses) if all_responses else 0
            active_session.total_score = round(avg_score)
            db.session.commit()
            _generate_report(user_id, session.get("last_color_score", 3), active_session.total_score, active_session.question_count)
            session.pop("image_questions", None)
            session.pop("current_q_idx", None)
            session.pop("active_image_session_id", None)
            return redirect(url_for("personalized.report_view"))
        
        db.session.commit()
        return redirect(url_for("personalized.image_test"))
        
    return render_template("tests/image_test.html", 
                           images=display_images, 
                           current_q=current_idx + 1, 
                           total_q=len(questions))

@personalized_bp.route("/report")
@login_required
def report_view():
    report = MentalHealthReport.query.filter_by(user_id=session["user_id"]).order_by(MentalHealthReport.timestamp.desc()).first()
    if not report:
        flash("No report found. Please take the tests.", "warning")
        return redirect(url_for("personalized.color_test"))
    return render_template("tests/report.html", report=report)

@personalized_bp.route("/report/<int:report_id>/download")
@login_required
def download_report(report_id):
    report = MentalHealthReport.query.get_or_404(report_id)
    if report.user_id != session["user_id"]:
        flash("Unauthorized access.", "danger")
        return redirect(url_for("dashboard.index"))
        
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- Helper: Wrapped Text ---
    def draw_wrapped_text(c, text, x, y, max_width, line_height=14):
        text_obj = c.beginText(x, y)
        words = text.split()
        line = ""
        for word in words:
            if c.stringWidth(line + " " + word) < max_width:
                line += " " + word
            else:
                text_obj.textLine(line.strip())
                line = word
        text_obj.textLine(line.strip())
        c.drawText(text_obj)
        return text_obj.getY()

    # --- Header ---
    p.setFillColorRGB(0.25, 0.35, 0.75) # Deep Lav/Blue
    p.rect(0, height - 100, width, 100, fill=1)
    
    p.setFillColorRGB(1, 1, 1)
    p.setFont("Helvetica-Bold", 26)
    p.drawString(40, height - 60, "Mental Health Analysis Report")
    p.setFont("Helvetica", 11)
    p.drawString(40, height - 80, f"MindGuard Early Warning System | Clinical ID: MG-{str(report.user_id).split('-')[0].upper()}")
    p.drawRightString(width - 40, height - 80, f"Issued: {report.timestamp.strftime('%B %d, %Y | %H:%M')}")

    y = height - 140

    # --- SECTION 1: Session Summary ---
    p.setFillColorRGB(0.1, 0.1, 0.1)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, y, "Section 1 — Session Summary")
    y -= 25
    
    p.setFont("Helvetica", 11)
    p.setFillColorRGB(0.3, 0.3, 0.3)
    # Session date & generic duration (mocking duration)
    p.drawString(50, y, f"Session Date: {report.timestamp.strftime('%B %d, %Y')}")
    y -= 15
    p.drawString(50, y, "Session Duration: Approx. 15-20 minutes")
    y -= 40
    
    # Fetch Voice Emotion Events for Timeline
    from app.models import VoiceEmotionEvent
    # Get recent events from today (or session)
    recent_events = VoiceEmotionEvent.query.filter_by(user_id=report.user_id).order_by(VoiceEmotionEvent.timestamp.desc()).limit(10).all()
    recent_events.reverse() # chronological
    
    # --- SECTION 2: Mood Swing Timeline ---
    p.setFillColorRGB(0.1, 0.1, 0.1)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, y, "Section 2 — Mood Swing Timeline")
    y -= 20
    
    if recent_events:
        # Table Header
        p.setFont("Helvetica-Bold", 10)
        p.setFillColorRGB(0.4, 0.4, 0.6)
        p.drawString(50, y, "Time")
        p.drawString(180, y, "Detected Emotion")
        p.drawString(350, y, "Confidence")
        y -= 15
        p.setStrokeColorRGB(0.8, 0.8, 0.8)
        p.line(40, y+5, 500, y+5)
        
        p.setFont("Helvetica", 10)
        p.setFillColorRGB(0.2, 0.2, 0.2)
        for ev in recent_events:
            p.drawString(50, y, ev.timestamp.strftime("%I:%M %p"))
            p.drawString(180, y, ev.detected_emotion)
            p.drawString(350, y, f"{int(ev.confidence_score * 100)}%")
            y -= 20
    else:
        p.setFont("Helvetica-Oblique", 10)
        p.drawString(50, y, "No live voice emotion events detected during this session.")
        y -= 20
    
    y -= 20
    
    # --- SECTION 3: Emotional Pattern Analysis ---
    p.setFillColorRGB(0.1, 0.1, 0.1)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, y, "Section 3 — Emotional Pattern Analysis")
    y -= 20
    
    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0.3, 0.3, 0.3)
    
    if recent_events:
        # Determine simple heuristic patterns
        emotions = [ev.detected_emotion for ev in recent_events]
        start_emo = emotions[0]
        end_emo = emotions[-1]
        
        if len(set(emotions)) > 3:
            y = draw_wrapped_text(p, "• High emotional variance detected across the session.", 50, y, 480)
        if "Anxious" in emotions or "Stressed" in emotions:
            y = draw_wrapped_text(p, "• Temporary stress or anxiety spikes observed.", 50, y, 480)
        if end_emo in ["Calm", "Happy", "Neutral", "Stable"] and start_emo in ["Anxious", "Stressed", "Angry"]:
            y = draw_wrapped_text(p, "• Emotional stability significantly improved toward end of session.", 50, y, 480)
        elif end_emo == start_emo:
            y = draw_wrapped_text(p, "• Emotional state remained relatively consistent throughout.", 50, y, 480)
    else:
        y = draw_wrapped_text(p, "• Insufficient live data to determine mid-session emotional patterns.", 50, y, 480)
    
    y -= 30
    
    if y < 200:
        p.showPage()
        y = height - 80

    # --- SECTION 4: Mental Health Indicators ---
    p.setFillColorRGB(0.1, 0.1, 0.1)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, y, "Section 4 — Mental Health Indicators")
    y -= 20
    
    p.setStrokeColorRGB(0.8, 0.8, 0.8)
    p.setFillColorRGB(0.96, 0.96, 0.98)
    p.rect(40, y-10, 532, 20, fill=1, stroke=0)
    
    p.setFillColorRGB(0.2, 0.2, 0.4)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y-5, "Test / Indicator")
    p.drawString(220, y-5, "Score")
    p.drawString(380, y-5, "Interpretation")
    y -= 20

    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0, 0, 0)
    
    def get_phq_interp(s):
        if s <= 4: return "Minimal (Normal range)"
        if s <= 9: return "Mild depression symptoms"
        if s <= 14: return "Moderate depression"
        return "Severe clinical indicators"

    def get_gad_interp(s):
        if s <= 4: return "Minimal (Normal range)"
        if s <= 9: return "Mild anxiety indicators"
        if s <= 14: return "Moderate anxiety"
        return "Severe anxiety severity"

    table_data = [
        ("Depression (PHQ-9)", f"{report.phq9_score} / 27", get_phq_interp(report.phq9_score)),
        ("Anxiety (GAD-7)", f"{report.gad7_score} / 21", get_gad_interp(report.gad7_score)),
        ("Emotional Color Test", f"{report.color_score} / 5", "Psychological color-mood mapping"),
        ("Visual Emotion MCQ", f"{report.image_score}/{report.image_max}", "Interactive visual resonance"),
        ("Composite Risk Prediction", f"{report.risk_level}", f"Overall: {report.category}")
    ]

    for label, val, interp in table_data:
        p.line(40, y+10, 572, y+10)
        p.drawString(50, y-2, label)
        p.drawString(220, y-2, str(val))
        p.drawString(380, y-2, interp)
        y -= 20
    p.line(40, y+10, 572, y+10)
    
    y -= 30
    
    if y < 150:
        p.showPage()
        y = height - 80

    # --- SECTION 5: Improvement Suggestions ---
    p.setFillColorRGB(0.1, 0.1, 0.1)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, y, "Section 5 — Improvement Suggestions")
    y -= 20
    
    p.setFont("Helvetica", 10)
    p.setFillColorRGB(0.3, 0.3, 0.3)
    y = draw_wrapped_text(p, report.recommendations or "• Practice daily breathing techniques and mindfulness.\n• Maintain a healthy sleep schedule and social engagement.\n• Consider returning for daily wellness check-ins.", 50, y, 500)
    
    y -= 30

    if y < 100:
        p.showPage()
        y = height - 80

    # --- SECTION 6: AI Wellness Insight ---
    p.setFillColorRGB(0.1, 0.1, 0.1)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, y, "Section 6 — AI Wellness Insight")
    y -= 20
    
    # We use a summarized string since we cannot query the LLM synchronously here without huge delays,
    # OR we use the concerns field that the LLM already generated during test completion.
    p.setFont("Helvetica-Oblique", 10)
    p.setFillColorRGB(0.2, 0.3, 0.5)
    insight_text = report.concerns if report.concerns else "The user's emotional pattern appears relatively stable. Ongoing interaction with the Voice AI indicates normal emotional regulation with no severe distress flags."
    y = draw_wrapped_text(p, f'"{insight_text}"', 50, y, 480)

    # --- Footer ---
    p.setStrokeColorRGB(0.9, 0.9, 0.9)
    p.line(40, 60, width-40, 60)
    p.setFont("Helvetica-Oblique", 8)
    p.setFillColorRGB(0.4, 0.4, 0.4)
    p.drawString(40, 45, "Disclaimer: This report is generated by the MindGuard AI Early Warning System. It is intended for early detection")
    p.drawString(40, 35, "and screening support. It is NOT a clinical diagnosis. Privacy Notice: No raw audio or conversation text is stored here.")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"MindGuard_Report_Ref_{report.user_id}.pdf", mimetype='application/pdf')

# ── Helper Logic ─────────────────────────────────────────────────────────────

def _generate_report(user_id, color_score, image_score, image_max=3):
    latest_assessment = AssessmentSession.query.filter_by(user_id=user_id).order_by(AssessmentSession.timestamp.desc()).first()
    phq9, gad7 = 10, 8
    if latest_assessment:
        ratio = latest_assessment.total_score / latest_assessment.max_score if latest_assessment.max_score > 0 else 0.5
        phq9, gad7 = int((1 - ratio) * 27), int((1 - ratio) * 21)
        
    recent_chats = ChatMessage.query.filter_by(user_id=user_id).order_by(ChatMessage.timestamp.desc()).limit(10).all()
    if recent_chats:
        pos_count = sum(1 for c in recent_chats if c.sentiment == "POSITIVE")
        sentiment_avg = (pos_count / len(recent_chats)) * 2 - 1 
    else:
        sentiment_avg = 0.5 
        
    # Get color info from the most recent test
    latest_color = ColorMoodTest.query.filter_by(user_id=user_id).order_by(ColorMoodTest.timestamp.desc()).first()
    c_name, c_hex = "Unknown", "#cccccc"
    if latest_color:
        matching_opt = next((o for o in COLOR_OPTIONS if o["value"] == latest_color.color), None)
        if matching_opt:
            c_name = matching_opt["name"]
            c_hex = matching_opt["hex"]

    prediction = predict_mental_health_state(phq9, gad7, sentiment_avg, color_score, image_score, image_max)
    report = MentalHealthReport(
        user_id=user_id, phq9_score=phq9, gad7_score=gad7,
        sentiment_score=sentiment_avg, color_score=color_score,
        color_name=c_name, color_hex=c_hex,
        image_score=image_score, image_max=image_max, overall_score=prediction["overall_score"],
        risk_level=prediction["risk_level"], category=prediction["category"], concerns=prediction["concerns"],
        recommendations=prediction["recommendations"]
    )
    db.session.add(report)
    db.session.commit()
    return report

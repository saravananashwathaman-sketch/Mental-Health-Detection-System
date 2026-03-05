import json
from app import create_app, db
from app.models import AssessmentQuestion


def seed_questions():
    app = create_app()
    with app.app_context():
        db.session.query(AssessmentQuestion).delete()

        # High-quality empathetic MCQ templates
        # Pattern: (Positive/Stable Score 3, Mild Score 2, Moderate Score 1, Severe Score 0)

        data = {
            "Teenagers": [
                # School & Social
                ("How often do you feel you have a friend you can truly talk to?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you feel like your teachers understand your perspective?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often does schoolwork make you feel exhausted before the day starts?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel safe and comfortable in the hallways at school?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel left out of social plans or group chats?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("How many nights a week do you get enough sleep to feel rested?", ["6–7 nights", "4–5 nights", "2–3 nights", "0–1 nights"]),
                ("Do you feel like you can be your true self around your classmates?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you worry about your grades or future college plans?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you have a hobby or activity that makes you feel genuinely happy?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel pressured to look or act a certain way?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                # Self-Esteem
                ("When you look in the mirror, how often do you feel okay with who you see?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you feel like your voice matters in family decisions?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel 'not good enough' compared to others on social media?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel comfortable talking to your parents about your feelings?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel proud of something you've accomplished?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("When things get tough, do you feel like you have a safe place to go?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel lonely even when there are people around?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel like you have control over your daily schedule?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you experience sudden mood swings that feel hard to manage?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel excited about the things you have planned for next week?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How frequently do you feel like you have to perform for others?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel like you are growing into someone you like?", ["Almost always", "Often", "Sometimes", "Almost never"]),
            ],
            "College Students": [
                ("How manageable does your current course load feel to you?", ["Very manageable", "Average", "Difficult", "Overwhelming"]),
                ("Do you feel like you've found a 'home' or community on campus?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you worry about the cost of your education or living stays?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel your major or field of study is actually a good fit for you?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel overwhelmed by the need to be independent?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you find it easy to balance studying with your social life?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you stay up late worrying about upcoming exams or deadlines?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel you have a clear plan for your life after graduation?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel like you're 'imposter' in your academic program?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you have access to healthy food and regular meals most days?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel anxious about finding a job or internship?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel safe and comfortable in your current living situation?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel disconnected from your family back home?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel like you have time for physical activity or exercise?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel like you have to hide your stress to look 'okay'?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel supported by your college's mentors or professors?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel drained by social expectations or 'FOMO'?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you enjoy the clubs or organizations you are part of?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel like there's no way to catch up on your work?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel like you are learning things that will be useful for your future?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel pressure to network or build a resume constantly?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel like your college life is personally fulfilling?", ["Almost always", "Often", "Sometimes", "Almost never"]),
            ],
            "Working Professionals": [
                ("How often do you feel satisfied with the impact of your work?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you feel like your boss or supervisor respects your personal time?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel your workload is unrealistic for one person?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel comfortable setting boundaries with your colleagues?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel drained of energy when you get home from work?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel your professional environment is supportive of your well-being?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel anxious about your job security or performance reviews?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you find it easy to 'switch off' from work-related thoughts in the evening?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel like you're working just to keep your head above water?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel you have opportunities for growth in your current role?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel isolated or lonely while working (remotely or in-office)?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel fairly compensated for the effort you put into your job?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel physically unwell due to work-related stress?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you have someone at work you consider a trusted peer or friend?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel bored or uninspired by your daily tasks?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel your skills and talents are being well-utilized?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you find yourself working through lunch or breaks?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel like you have enough time for your family and friends?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you worry about the direction of your career?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel like your workplace values diversity and inclusion?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you go through your workday feeling like a robot?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel your commute (if any) or workspace is tolerable?", ["Almost always", "Often", "Sometimes", "Almost never"]),
            ],
            "Adult / General Population": [
                ("How often do you find time to do something specifically for yourself?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you feel like you are meeting the expectations you have for your life?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel overwhelmed by your household responsibilities?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel connected to your local community or neighborhood?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you worry about your physical health or aging?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you have people in your life you can rely on for help when you need it?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel like your daily routine is meaningful?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you get quality sleep most nights of the week?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel anxious about things you cannot control?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you find it easy to stay organized and manage your schedule?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel lonely in your personal life?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel like you have enough financial resources to lead a comfortable life?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel regret about past decisions or opportunities?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel like you have a sense of purpose in your life right now?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you find it hard to concentrate on quiet tasks like reading?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel like your living environment is a place of peace for you?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel like you are just going through the motions?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel comfortable asking for emotional support when you're down?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel hopeful about the future?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you feel like you have a good relationship with your family members?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel like you are carrying a heavy invisible weight?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel like you have a reason to get out of bed every morning?", ["Almost always", "Often", "Sometimes", "Almost never"]),
            ],
            "Senior Citizens": [
                ("How often do you feel that your wisdom and experience are valued?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you feel a sense of peace about your current stage in life?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel lonely or isolated from your family?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel you have things to look forward to in the coming months?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you worry about your physical mobility or health?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel connected to the people in your local surroundings?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel like the world is moving too fast for you?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you find joy in your daily hobbies or habits?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you reflect on your life with a sense of pride?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you feel you have enough social support for your needs?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel forgotten by the younger generation?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you find yourself dwelling on past mistakes more than you'd like?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("How often do you feel like you still have a contribution to make?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you have someone you can call immediately if you feel unwell?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel anxious about your future living situation?", ["Almost never", "Sometimes", "Often", "Almost always"]),
            ],
            "Trauma-sensitive women": [
                ("Do you feel safe and protected in your current home?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel a strong sense of inner strength and resilience?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you find it difficult to relax or 'let your guard down' in public?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("How often do you feel supported by the women in your life?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you find yourself avoiding certain places or people due to bad memories?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("How often do you feel proud of the person you have become?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you experience sudden feelings of panic without an obvious cause?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("How often do you feel capable of handling life's challenges?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you find it hard to keep a consistent sleep schedule due to worries?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("How often do you feel that your story and experiences are valid?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you feel you have a voice and agency in your relationships?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you experience physical symptoms like heart racing when stressed?", ["Almost never", "Sometimes", "Often", "Almost always"]),
                ("Do you feel like you have a supportive community you trust?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel optimistic about your healing journey?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you feel like your personal boundaries are respected by others?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you find peace in small daily moments?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you feel empowered to make your own life choices?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel like you've regained control over your life?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you feel like you are finally moving forward from past pains?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel valued by the people who matter to you?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("Do you feel like you have a safe way to express your emotions?", ["Almost always", "Often", "Sometimes", "Almost never"]),
                ("How often do you feel like your future is yours to define?", ["Almost always", "Often", "Sometimes", "Almost never"]),
            ]
        }

        # Expansion logic to reach 500+ questions total
        # We will create variations of these base questions with slightly different phrasing
        expanded_data = {}
        for cat, questions in data.items():
            cat_list = list(questions)
            # Create variations
            variations = []
            for q, opts in questions:
                # Variation 1: Direct address
                v1_text = q.replace("Do you feel", "Are you feeling").replace("How often do you", "How frequently do you")
                if v1_text != q:
                    variations.append((v1_text, opts))

                # Variation 2: Recent timeframe
                v2_text = q.replace("?", " lately?").replace("??", "?")
                if v2_text != q:
                    variations.append((v2_text, opts))

                # Variation 3: Empathy prefix
                v3_text = "Reflecting on your past few days, " + q[0].lower() + q[1:]
                variations.append((v3_text, opts))

                # Variation 4: Personal check-in
                v4_text = "Just checking in: " + q
                variations.append((v4_text, opts))

            cat_list.extend(variations)
            expanded_data[cat] = cat_list

        count = 0
        for cat, questions in expanded_data.items():
            for q_text, options in questions:
                # Scoring heuristic:
                # If first option is positive (e.g. Almost always, Very, 6-7 nights, Excellence, Very manageable),
                # scores should be [3, 2, 1, 0].
                # If it's a "frequency of negative" question (starting with Almost never),
                # scores should also be [3, 2, 1, 0] because 'Almost never' is the healthiest state.

                scores = [3, 2, 1, 0]

                # Check for reversed phrasing where options might be ordered differently (rare in this template)
                # But to be safe, if we had ["Overwhelming", "Difficult", "Average", "Very manageable"]:
                # if options[0] in ["Overwhelming", "Poor", "0–1 nights", "Unsatisfied"]:
                #     scores = [0, 1, 2, 3]

                db.session.add(AssessmentQuestion(
                    category=cat,
                    question_text=q_text,
                    options_json=json.dumps(options),
                    scores_json=json.dumps(scores)
                ))
                count += 1

        db.session.commit()
        print(f"Seeded {count} professional assessment questions across all categories.")


if __name__ == "__main__":
    seed_questions()

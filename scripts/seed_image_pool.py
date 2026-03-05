from app import create_app, db
from app.models import ImagePool

def seed_image_pool():
    app = create_app()
    with app.app_context():
        # Clear existing pool for fresh seed
        db.session.query(ImagePool).delete()

        images = [
            # HAPPY (Score 3)
            {"url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400", "emotion_category": "happy", "score": 3, "description": "Laughter"},
            {"url": "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=400", "emotion_category": "happy", "score": 3, "description": "Friends sharing a meal"},
            {"url": "https://images.unsplash.com/photo-1517486808906-6ca8b3f04846?w=400", "emotion_category": "happy", "score": 3, "description": "Joyful celebration"},
            {"url": "https://images.unsplash.com/photo-1531058240690-006c446962d8?w=400", "emotion_category": "happy", "score": 3, "description": "Running in a sunlit field"},
            {"url": "https://images.unsplash.com/photo-1471440671318-55bdbb772f93?w=400", "emotion_category": "happy", "score": 3, "description": "Smiling child with a balloon"},
            {"url": "https://images.unsplash.com/photo-1506869640319-fe1a24fd76dc?w=400", "emotion_category": "happy", "score": 3, "description": "Happy group high-five"},
            {"url": "https://images.unsplash.com/photo-1543132220-4bf3de6e10ae?w=400", "emotion_category": "happy", "score": 3, "description": "Vibrant festive lights"},
            {"url": "https://images.unsplash.com/photo-1527529482837-4698179dc6ce?w=400", "emotion_category": "happy", "score": 3, "description": "Dancing at a party"},

            # CALM (Score 3)
            {"url": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=400", "emotion_category": "calm", "score": 3, "description": "Sunset at a lake"},
            {"url": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400", "emotion_category": "calm", "score": 3, "description": "Deep forest path"},
            {"url": "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?w=400", "emotion_category": "calm", "score": 3, "description": "Quiet mountain range"},
            {"url": "https://images.unsplash.com/photo-1518005020251-5fb501707c7c?w=400", "emotion_category": "calm", "score": 3, "description": "Zen garden stones"},
            {"url": "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=400", "emotion_category": "calm", "score": 3, "description": "Peaceful river flow"},
            {"url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400", "emotion_category": "calm", "score": 3, "description": "Empty sandy beach"},
            {"url": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=400", "emotion_category": "calm", "score": 3, "description": "Foggy mountains"},
            {"url": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=400", "emotion_category": "calm", "score": 3, "description": "Coffee cup on a rainy window"},

            # NEUTRAL (Score 2)
            {"url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=400", "emotion_category": "neutral", "score": 2, "description": "Modern office building"},
            {"url": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=400", "emotion_category": "neutral", "score": 2, "description": "Empty conference room"},
            {"url": "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?w=400", "emotion_category": "neutral", "score": 2, "description": "Busy city street crosswalk"},
            {"url": "https://images.unsplash.com/photo-1503387762-592dea58ef23?w=400", "emotion_category": "neutral", "score": 2, "description": "Architectural geometric lines"},
            {"url": "https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=400", "emotion_category": "neutral", "score": 2, "description": "Abstract gray pattern"},
            {"url": "https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?w=400", "emotion_category": "neutral", "score": 2, "description": "Person typing on a laptop"},
            {"url": "https://images.unsplash.com/photo-1497215728101-856f4ea42174?w=400", "emotion_category": "neutral", "score": 2, "description": "Minimalist bookshelf"},
            {"url": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=400", "emotion_category": "neutral", "score": 2, "description": "Students studying in a library"},

            # ANXIOUS (Score 1)
            {"url": "https://images.unsplash.com/photo-1518491755924-df5bd6742cdd?w=400", "emotion_category": "anxious", "score": 1, "description": "Blurred motion, high speed"},
            {"url": "https://images.unsplash.com/photo-1499209974431-9dac3adaf477?w=400", "emotion_category": "anxious", "score": 1, "description": "Stairs that lead nowhere"},
            {"url": "https://images.unsplash.com/photo-1532012197367-6349013898fd?w=400", "emotion_category": "anxious", "score": 1, "description": "Crowded subway station"},
            {"url": "https://images.unsplash.com/photo-1506485338023-6ce5f366927f?w=400", "emotion_category": "anxious", "score": 1, "description": "Dark tunnel with a small light"},
            {"url": "https://images.unsplash.com/photo-1551836022-d5d88e9218df?w=400", "emotion_category": "anxious", "score": 1, "description": "Tangled wires and chaos"},
            {"url": "https://images.unsplash.com/photo-1506784365847-bbad939e9335?w=400", "emotion_category": "anxious", "score": 1, "description": "Shattered glass window"},
            {"url": "https://images.unsplash.com/photo-1509114397022-ed747cca3f65?w=400", "emotion_category": "anxious", "score": 1, "description": "Red flashing alarm light"},
            {"url": "https://images.unsplash.com/photo-1541170155377-5091f3b33d39?w=400", "emotion_category": "anxious", "score": 1, "description": "Stormy sky with lightning"},

            # SAD (Score 1)
            {"url": "https://images.unsplash.com/photo-1473081556163-2a17de81fc97?w=400", "emotion_category": "sad", "score": 1, "description": "Withered autumn leaf"},
            {"url": "https://images.unsplash.com/photo-1516585427167-9f4af9627e6c?w=400", "emotion_category": "sad", "score": 1, "description": "Person sitting alone in shadows"},
            {"url": "https://images.unsplash.com/photo-1520121401995-928cd50d4e27?w=400", "emotion_category": "sad", "score": 1, "description": "Gloomy rainy city afternoon"},
            {"url": "https://images.unsplash.com/photo-1518199266791-5375a83190b7?w=400", "emotion_category": "sad", "score": 1, "description": "Broken wooden fence"},
            {"url": "https://images.unsplash.com/photo-1501430654243-c934cec2e1ce?w=400", "emotion_category": "sad", "score": 1, "description": "Gray clouds over an empty road"},
            {"url": "https://images.unsplash.com/photo-1514846323538-02685025958f?w=400", "emotion_category": "sad", "score": 1, "description": "Faded old photograph"},
            {"url": "https://images.unsplash.com/photo-1456318019113-df4358079a78?w=400", "emotion_category": "sad", "score": 1, "description": "Lonely bench in winter"},
            {"url": "https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=400", "emotion_category": "sad", "score": 1, "description": "Drooping flower heads"},

            # LONELY (Score 0)
            {"url": "https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=400", "emotion_category": "lonely", "score": 0, "description": "Empty lighthouse on a cliff"},
            {"url": "https://images.unsplash.com/photo-1508247469910-5d2ef4a6d84d?w=400", "emotion_category": "lonely", "score": 0, "description": "Solitary tree in a desert"},
            {"url": "https://images.unsplash.com/photo-1516589174184-c685eaa367ec?w=400", "emotion_category": "lonely", "score": 0, "description": "Abandoned house in a field"},
            {"url": "https://images.unsplash.com/photo-1534067783941-51c9c23ecefd?w=400", "emotion_category": "lonely", "score": 0, "description": "One star in a dark sky"},
            {"url": "https://images.unsplash.com/photo-1521133573832-3f1101db95cc?w=400", "emotion_category": "lonely", "score": 0, "description": "Single chair by a cold window"},
            {"url": "https://images.unsplash.com/photo-1469474968028-56623f02e42e?w=400", "emotion_category": "lonely", "score": 0, "description": "Vast empty canyon"},
            {"url": "https://images.unsplash.com/photo-1493246507139-91e8bef99c02?w=400", "emotion_category": "lonely", "score": 0, "description": "Lone boat on a still lake"},
            {"url": "https://images.unsplash.com/photo-1512403754473-27835f7b9984?w=400", "emotion_category": "lonely", "score": 0, "description": "Empty airport terminal at night"},

            # OVERWHELMED (Score 0)
            {"url": "https://images.unsplash.com/photo-1454165833222-8821c5275e66?w=400", "emotion_category": "overwhelmed", "score": 0, "description": "Endless paperwork and clocks"},
            {"url": "https://images.unsplash.com/photo-1528642463367-ad55778a483e?w=400", "emotion_category": "overwhelmed", "score": 0, "description": "Tangled knots of rope"},
            {"url": "https://images.unsplash.com/photo-1507413245164-6160d8298b31?w=400", "emotion_category": "overwhelmed", "score": 0, "description": "Fragmented abstract patterns"},
            {"url": "https://images.unsplash.com/photo-1516321497487-e288fb19713f?w=400", "emotion_category": "overwhelmed", "score": 0, "description": "Data matrix overloaded with info"},
            {"url": "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?w=400", "emotion_category": "overwhelmed", "score": 0, "description": "Person holding their head in hands"},
            {"url": "https://images.unsplash.com/photo-1506197603482-1c280165133f?w=400", "emotion_category": "overwhelmed", "score": 0, "description": "Huge wave crashing down"},
            {"url": "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?w=400", "emotion_category": "overwhelmed", "score": 0, "description": "Desk covered in coffee stains"},
            {"url": "https://images.unsplash.com/photo-1554178286-db408551fe39?w=400", "emotion_category": "overwhelmed", "score": 0, "description": "Maze of heavy machinery"},

            # ANGRY (Score 1)
            {"url": "https://images.unsplash.com/photo-1542385151-efd9000785a0?w=400", "emotion_category": "angry", "score": 1, "description": "Spattering red paint like fire"},
            {"url": "https://images.unsplash.com/photo-1511216335778-7cb8f49fa7a3?w=400", "emotion_category": "angry", "score": 1, "description": "Jagged sharp mountain peaks"},
            {"url": "https://images.unsplash.com/photo-1463171359979-330b66a3589b?w=400", "emotion_category": "angry", "score": 1, "description": "Explosive eruption of lights"},
            {"url": "https://images.unsplash.com/photo-1529154146176-29d943480ea1?w=400", "emotion_category": "angry", "score": 1, "description": "Shattered mirror reflecting frustration"},
            {"url": "https://images.unsplash.com/photo-1553152531-b98a2fc8d3bf?w=400", "emotion_category": "angry", "score": 1, "description": "Furious red sunset sky"},
            {"url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=400", "emotion_category": "angry", "score": 1, "description": "Dark storm approaching fast"},
            {"url": "https://images.unsplash.com/photo-1533038590840-1cde6e668a91?w=400", "emotion_category": "angry", "score": 1, "description": "Cracked dry earth surface"},
            {"url": "https://images.unsplash.com/photo-1510519133417-c8c331193310?w=400", "emotion_category": "angry", "score": 1, "description": "Abstract spikes and thorns"},
        ]

        for img_data in images:
            img = ImagePool(**img_data)
            db.session.add(img)
        
        db.session.commit()
        print(f"Successfully seeded {len(images)} images into the pool.")

if __name__ == "__main__":
    seed_image_pool()

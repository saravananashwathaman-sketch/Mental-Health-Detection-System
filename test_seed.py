import random
from app import create_app, db
from app.models import ImagePool

app = create_app()
with app.app_context():
    db.session.query(ImagePool).delete()

    emotions = {
        'happy': {'score': 3, 'desc': 'Bright, colorful, energetic'},
        'calm': {'score': 3, 'desc': 'Peaceful, serene landscape'},
        'neutral': {'score': 2, 'desc': 'Minimalist, everyday object'},
        'anxious': {'score': 1, 'desc': 'Chaotic, cluttered scene'},
        'sad': {'score': 1, 'desc': 'Gloomy, overcast, fading colors'},
        'lonely': {'score': 0, 'desc': 'Isolated focus in vast space'},
        'overwhelmed': {'score': 0, 'desc': 'Complex heavy patterns'},
        'angry': {'score': 1, 'desc': 'Harsh contrasts, sharp angles'}
    }

    count = 0
    for emotion, data in emotions.items():
        for i in range(1, 71):
            seed = f'mh_{emotion}_{i}'
            url = f'https://picsum.photos/seed/{seed}/400/400'
            img = ImagePool(
                url=url,
                emotion_category=emotion,
                score=data['score'],
                description=f"{data['desc']} #{i}"
            )
            db.session.add(img)
            count += 1
            
    db.session.commit()
    print(f'Successfully seeded {count} unique images into the pool!')

import json
from run import app
from flask import session

with app.test_client() as c:
    # 1. Login
    r_login = c.post('/login', data={'email': 'test@example.com', 'password': 'password'})
    print("Login:", r_login.status_code)
    
    # 2. Get CSRF token
    r_get = c.get('/chat/voice')
    import re
    m = re.search(r'name="csrf-token" content="(.*?)"', r_get.text)
    csrf = m.group(1) if m else ''
    print("CSRF:", csrf)
    
    # 3. Post to /chat/send
    r_post = c.post('/chat/send', 
                    json={
                        'message': 'Hello this is an angry message',
                        'acoustic_features': {'pitch': 250, 'energy': 0.1, 'speech_speed': 0.3}
                    },
                    headers={'X-CSRFToken': csrf})
    print("Post status:", r_post.status_code)
    if r_post.status_code != 200:
        print("Error content:", r_post.text)
    else:
        print("Success:", r_post.json)

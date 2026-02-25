from flask import Flask, render_template, jsonify
import psutil
import random

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    data = {
        'temp': {
            'cpu': random.randint(40, 75),
            'gpu': random.randint(45, 80),
            'mb': random.randint(35, 45),
            'vrm': random.randint(40, 60),
            'sys': random.randint(30, 40),
            # On génère une liste de 4 températures pour les SSD
            'ssds': [random.randint(30, 50) for _ in range(4)] 
        },
        'usage': {
            'cpu': psutil.cpu_percent(interval=None),
            'ram': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent,
            'net': random.randint(5, 100),
            'gpu': random.randint(10, 90),
            'vram': random.randint(20, 80),
            # On génère une liste de 4 pourcentages d'usage pour les SSD
            'ssds': [random.randint(10, 90) for _ in range(4)]
        }
    }
    return jsonify(data)

if __name__ == '__main__':
    # On lance le serveur sur le port 5000
    app.run(debug=True, port=5000)
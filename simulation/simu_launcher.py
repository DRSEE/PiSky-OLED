import sys
import os
from flask import Flask, jsonify, render_template

# On remonte d'un cran pour charger ADSBManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.adsb import ADSBManager

app = Flask(__name__)
adsb = ADSBManager()

MY_LAT, MY_LON = 45.77050, 5.00443

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    # Envoie juste les données brutes, le JS s'occupe du dessin
    stats = adsb.get_aircraft_stats(MY_LAT, MY_LON)
    return jsonify(stats)

if __name__ == '__main__':
    print("Simulateur actif sur http://192.168.0.38:5000")
    app.run(host='0.0.0.0', port=5000)
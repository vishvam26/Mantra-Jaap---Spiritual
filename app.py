import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Tables banavva mate
    cursor.execute('''CREATE TABLE IF NOT EXISTS jap_counter 
                      (id INTEGER PRIMARY KEY, current_count INTEGER, total_count INTEGER, last_date TEXT)''')
    cursor.execute('CREATE TABLE IF NOT EXISTS jap_history (date TEXT PRIMARY KEY, count INTEGER)')
    
    cursor.execute('SELECT id FROM jap_counter WHERE id = 1')
    if cursor.fetchone() is None:
        cursor.execute('INSERT INTO jap_counter (id, current_count, total_count, last_date) VALUES (1, 0, 0, ?)', 
                       (datetime.now().strftime('%Y-%m-%d'),))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auto-jap.html')
def auto_jap():
    return render_template('auto-jap.html')

@app.route('/get_count', methods=['GET'])
def get_count():
    today_dt = datetime.now()
    today = today_dt.strftime('%Y-%m-%d')
    yesterday = (today_dt - timedelta(days=1)).strftime('%Y-%m-%d') # 2. Yesterday calculate karo
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 3. Streak column check karo, na hoy to umero (Migration)
    try:
        cursor.execute('ALTER TABLE jap_counter ADD COLUMN streak INTEGER DEFAULT 0')
        conn.commit()
    except: pass

    cursor.execute('SELECT current_count, total_count, last_date, streak FROM jap_counter WHERE id = 1')
    row = cursor.fetchone()
    
    curr_val, total_val, last_date, streak = row if row else (0, 0, "", 0)

    # 4. Streak Logic
    if last_date != today:
        if last_date == yesterday:
            if curr_val > 0: streak += 1
        else:
            # Jo user aaje jaap sharu kare to streak 1 thavi joie
            streak = 1 if curr_val > 0 else 0
            
        curr_val = 0
        cursor.execute('UPDATE jap_counter SET current_count = 0, last_date = ?, streak = ? WHERE id = 1', (today, streak))
        conn.commit()
    
    cursor.execute('SELECT date, count FROM jap_history')
    history = dict(cursor.fetchall())
    conn.close()

    return jsonify({
        'current_count': curr_val,
        'total_count': total_val,
        'streak': streak, # 5. Streak return karo
        'today': today,
        'history': history
    })

@app.route('/update_count', methods=['POST'])
def update_count():
    data = request.get_json()
    curr = data.get('current_count', 0)
    total = data.get('total_count', 0)
    today = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # 1. Pehla check karo ke hal ni streak ketli chhe
        cursor.execute('SELECT streak FROM jap_counter WHERE id = 1')
        s_row = cursor.fetchone()
        streak = s_row[0] if s_row else 0
        
        # 2. Logic: Jo aaje pehli var jaap thaya (curr > 0) ane streak 0 chhe, to tene 1 karo
        if curr > 0 and streak == 0:
            streak = 1
            
        # 3. Database ma badhu update karo (streak sathe)
        cursor.execute('''UPDATE jap_counter 
                          SET current_count = ?, total_count = ?, last_date = ?, streak = ? 
                          WHERE id = 1''', (curr, total, today, streak))
        
        # 4. History table update karo
        cursor.execute('''INSERT INTO jap_history (date, count) VALUES (?, ?) 
                          ON CONFLICT(date) DO UPDATE SET count = ?''', (today, curr, curr))
        
        conn.commit()
        return jsonify({'status': 'success', 'streak': streak})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# PWA Support
@app.route('/manifest.json')
def serve_manifest():
    return app.send_static_file('manifest.json')

@app.route('/sw.js')
def serve_sw():
    return app.send_static_file('sw.js')

if __name__ == '__main__':
    init_db()  # <--- Aa call hovvo khub jaruri chhe!
    app.run(debug=True, host='0.0.0.0', port=5000)

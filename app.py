import os
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, jsonify, request
from supabase import create_client, Client

app = Flask(__name__)
IST = pytz.timezone('Asia/Kolkata')

# --- Supabase Setup (અહીં તમારી સાચી વિગતો નાખો) ---
SUPABASE_URL = "https://jxyrbfwibjlkkdjrsrqg.supabase.co"
SUPABASE_KEY = "sb_publishable_UQOjjJApS0CYWhBKtrm_rA_ekDreIji"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auto-jap.html')
def auto_jap():
    return render_template('auto-jap.html')

@app.route('/get_count', methods=['GET'])
@app.route('/get_count', methods=['GET'])
def get_count():
    now = datetime.now(IST)
    today = now.strftime('%Y-%m-%d')
    yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')

    # 1. Main counter મેળવો
    res = supabase.table("jap_counter").select("*").eq("id", 1).execute()
    row = res.data[0] if res.data else {"current_count": 0, "total_count": 0, "last_date": today, "streak": 0}

    curr_val = row['current_count']
    total_val = row['total_count']
    last_date = row['last_date']
    streak = row['streak']

    # 2. Streak Logic (જો દિવસ બદલાઈ ગયો હોય)
    if last_date != today:
        if last_date == yesterday and curr_val > 0:
            streak += 1
        elif last_date != yesterday:
            streak = 0
        
        curr_val = 0 
        supabase.table("jap_counter").update({
            "current_count": 0, "last_date": today, "streak": streak
        }).eq("id", 1).execute()

    # 3. History મેળવો
    hist_res = supabase.table("jap_history").select("*").execute()
    history = {item['date']: item['count'] for item in hist_res.data}

    return jsonify({
        'current_count': curr_val, 'total_count': total_val,
        'streak': streak, 'today': today, 'history': history
    })

@app.route('/update_count', methods=['POST'])
def update_count():
    data = request.get_json()
    curr = data.get('current_count', 0)
    total = data.get('total_count', 0)
    today = datetime.now().strftime('%Y-%m-%d')
    
    supabase.table("jap_counter").update({
        "current_count": curr, "total_count": total, "last_date": today
    }).eq("id", 1).execute()

    supabase.table("jap_history").upsert({"date": today, "count": curr}).execute()

    return jsonify({'status': 'success'})
    try:
        # 1. Pehla check karo ke hal ni streak ketli chhe
        cursor.execute('SELECT last_date, streak FROM jap_counter WHERE id = 1')
        row = cursor.fetchone()
        last_date, streak = row if row else (None, 0)
        
        # 2. Logic: Jo aaje pehli var jaap thaya (curr > 0) ane streak 0 chhe, to tene 1 karo
        if curr > 0 and last_date != today:
            if last_date == yesterday:
               streak += 1
            else:
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
    app.run(debug=True)

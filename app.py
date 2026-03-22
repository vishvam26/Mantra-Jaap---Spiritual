import os
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, jsonify, request, send_from_directory, make_response
from supabase import create_client, Client

app = Flask(__name__)
IST = pytz.timezone('Asia/Kolkata')

# --- Supabase Setup ---
SUPABASE_URL = "https://qpjqkeujoylexlsegpef.supabase.co"
SUPABASE_KEY = "sb_publishable_wCoGC4x07Qg6joI6oyJ4kQ_lxQJWz43"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auto-jap.html')
def auto_jap():
    return render_template('auto-jap.html')

@app.route('/get_count', methods=['GET'])
def get_count():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'User ID missing'}), 400

    now = datetime.now(IST)
    today = now.strftime('%Y-%m-%d')
    yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')

    try:
        # User નો ડેટા મેળવો
        res = supabase.table("jap_counter").select("*").eq("user_id", user_id).execute()
        
        if not res.data:
            # જો નવો યુઝર હોય તો નવી રો બનાવો
            row = {"user_id": user_id, "current_count": 0, "total_count": 0, "last_date": today, "streak": 0}
            supabase.table("jap_counter").insert(row).execute()
        else:
            row = res.data[0]

        curr_val = row['current_count']
        total_val = row['total_count']
        last_date = row['last_date']
        streak = row['streak']

        # Streak Logic
        if last_date != today:
            if last_date == yesterday and curr_val > 0:
                streak += 1
            elif last_date != yesterday:
                streak = 0
            
            curr_val = 0 
            supabase.table("jap_counter").update({
                "current_count": 0, "last_date": today, "streak": streak
            }).eq("user_id", user_id).execute()

        # History મેળવો
        hist_res = supabase.table("jap_history").select("*").eq("user_id", user_id).execute()
        history = {item['date']: item['count'] for item in hist_res.data}

        return jsonify({
            'current_count': curr_val, 'total_count': total_val,
            'streak': streak, 'today': today, 'history': history
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_count', methods=['POST'])
def update_count():
    data = request.get_json()
    user_id = data.get('user_id')
    curr = data.get('current_count', 0)
    total = data.get('total_count', 0)
    today = datetime.now(IST).strftime('%Y-%m-%d')
    
    if not user_id:
        return jsonify({'error': 'User ID missing'}), 400

    try:
        supabase.table("jap_counter").update({
            "current_count": curr, "total_count": total, "last_date": today
        }).eq("user_id", user_id).execute()

        supabase.table("jap_history").upsert({
            "user_id": user_id, "date": today, "count": curr
        }).execute()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# PWA Support
@app.route('/sw.js')
def serve_sw():
    response = make_response(send_from_directory('static', 'sw.js'))
    response.headers['Content-Type'] = 'application/javascript'
    return response

if __name__ == '__main__':
    app.run(debug=True)

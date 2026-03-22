import os
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from supabase import create_client, Client

app = Flask(__name__)

# --- Supabase Setup ---
SUPABASE_URL = "https://hddjwsnketzenwvtzrgv.supabase.co"
SUPABASE_KEY = "sb_publishable_4VVMimPp7BbnCocnYNRuDw_gl8py4yI"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/auto-jap.html')
def auto_jap():
    return render_template('auto-jap.html')

@app.route('/get_count', methods=['GET'])
def get_count():
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    # 1. Main counter data મેળવો
    res = supabase.table("jap_counter").select("*").eq("id", 1).execute()
    row = res.data[0] if res.data else {"current_count": 0, "total_count": 0, "last_date": today, "streak": 0}

    curr_val = row['current_count']
    total_val = row['total_count']
    last_date = row['last_date']
    streak = row['streak']

    # 2. Streak Logic
    if last_date != today:
        if last_date == yesterday and curr_val > 0:
            streak += 1
        else:
            streak = 1 if curr_val > 0 else 0
        
        curr_val = 0 # નવો દિવસ એટલે આજનો કાઉન્ટ 0
        supabase.table("jap_counter").update({
            "current_count": 0, 
            "last_date": today, 
            "streak": streak
        }).eq("id", 1).execute()

    # 3. History મેળવો
    hist_res = supabase.table("jap_history").select("*").execute()
    history = {item['date']: item['count'] for item in hist_res.data}

    return jsonify({
        'current_count': curr_val,
        'total_count': total_val,
        'streak': streak,
        'today': today,
        'history': history
    })

@app.route('/update_count', methods=['POST'])
def update_count():
    data = request.get_json()
    curr = data.get('current_count', 0)
    total = data.get('total_count', 0)
    today = datetime.now().strftime('%Y-%m-%d')

    try:
        # 1. Streak update logic
        res = supabase.table("jap_counter").select("streak").eq("id", 1).execute()
        streak = res.data[0]['streak'] if res.data else 0
        if curr > 0 and streak == 0: streak = 1

        # 2. Update Main Table
        supabase.table("jap_counter").update({
            "current_count": curr,
            "total_count": total,
            "last_date": today,
            "streak": streak
        }).eq("id", 1).execute()

        # 3. Update History Table (Upsert)
        supabase.table("jap_history").upsert({"date": today, "count": curr}).execute()

        return jsonify({'status': 'success', 'streak': streak})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

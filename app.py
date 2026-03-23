import os
from dotenv import load_dotenv # આ નવી લાઇન ઉમેરો
from datetime import datetime, timedelta
import pytz
from flask import Flask, render_template, jsonify, request, send_from_directory, make_response
from supabase import create_client, Client

# .env ફાઇલમાંથી વેલ્યુ લોડ કરવા માટે
load_dotenv()

app = Flask(__name__)
IST = pytz.timezone('Asia/Kolkata')

# --- Supabase Setup (હવે સુરક્ષિત રીતે) ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials missing! Check your .env file.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# બાકીનો કોડ અહીં નીચે આવશે...

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
        res = supabase.table("jap_counter").select("*").eq("user_id", user_id).execute()
        
        if not res.data:
            row = {"user_id": user_id, "current_count": 0, "total_count": 0, "last_date": today, "streak": 0}
            supabase.table("jap_counter").insert(row).execute()
            return jsonify({'current_count': 0, 'total_count': 0, 'streak': 0, 'today': today, 'history': {}})
        
        row = res.data[0]
        curr_val = row['current_count']
        total_val = row['total_count']
        last_date = row['last_date']
        streak = row['streak']

        # જો નવો દિવસ હોય
        if last_date != today:
            # જો ગઈકાલે જાપ કર્યા હતા, તો જ સ્ટ્રીક વધારો
            if last_date == yesterday and curr_val > 0:
                streak += 1
            elif last_date != yesterday:
                # જો એક દિવસ વચ્ચે રહી ગયો હોય, તો સ્ટ્રીક ૦ કરી દો
                streak = 0
            
            # નવા દિવસ માટે current_count ૦ કરો
            curr_val = 0 
            supabase.table("jap_counter").update({
                "current_count": 0, 
                "last_date": today, 
                "streak": streak
            }).eq("user_id", user_id).execute()

        hist_res = supabase.table("jap_history").select("*").eq("user_id", user_id).execute()
        history = {item['date']: item['count'] for item in hist_res.data}

        return jsonify({
            'current_count': curr_val, 
            'total_count': total_val,
            'streak': streak, 
            'today': today, 
            'history': history
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
        # Supabase માં ડેટા અપડેટ કરવા માટે
        supabase.table("jap_counter").update({
            "current_count": curr, "total_count": total, "last_date": today
        }).eq("user_id", user_id).execute()

        supabase.table("jap_history").upsert({
            "user_id": user_id, "date": today, "count": curr
        }).execute()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/sw.js')
def serve_sw():
    response = make_response(send_from_directory('static', 'sw.js'))
    response.headers['Content-Type'] = 'application/javascript'
    return response

if __name__ == '__main__':
    app.run(debug=True)

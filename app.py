import os
from pymongo import MongoClient
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

# --- STEP 1: MONGODB CONNECTION ---
# Render par Environment Variable ma 'MONGO_URI' set karjo.
# Local mate: mongodb+srv://<user>:<password>@cluster.mongodb.net/dbname
MONGO_URI = os.environ.get('MONGO_URI', "mongodb+srv://pvishu2685:<db_password>@cluster0.ur9qbe0.mongodb.net/?appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client.divine_jap_db

# Collections
counter_col = db.jap_counter
history_col = db.jap_history

def init_db():
    if counter_col.count_documents({"id": 1}) == 0:
        counter_col.insert_one({
            "id": 1,
            "current_count": 0,
            "total_count": 0,
            "last_date": datetime.now().strftime('%Y-%m-%d'),
            "streak": 0
        })

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
    yesterday = (today_dt - timedelta(days=1)).strftime('%Y-%m-%d')
    
    data = counter_col.find_one({"id": 1})
    
    curr_val = data.get('current_count', 0)
    total_val = data.get('total_count', 0)
    last_date = data.get('last_date', "")
    streak = data.get('streak', 0)

    # Streak & Reset Logic
    if last_date != today:
        if last_date == yesterday:
            if curr_val > 0: streak += 1
        else:
            streak = 1 if curr_val > 0 else 0
            
        curr_val = 0
        counter_col.update_one(
            {"id": 1},
            {"$set": {"current_count": 0, "last_date": today, "streak": streak}}
        )

    # Weekly History
    history_cursor = history_col.find({}, {"_id": 0})
    history = {item['date']: item['count'] for item in history_cursor}

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
    # Total count ma direct overwrite thava thi data loss thase, etle increment vapray
    # Pan hal tame moklo chho e mujab:
    total = data.get('total_count', 0)
    today = datetime.now().strftime('%Y-%m-%d')
    
    user_data = counter_col.find_one({"id": 1})
    streak = user_data.get('streak', 0)
    if curr > 0 and streak == 0: streak = 1
            
    counter_col.update_one(
        {"id": 1},
        {"$set": {
            "current_count": curr,
            "total_count": total,
            "last_date": today,
            "streak": streak
        }}
    )
    
    history_col.update_one(
        {"date": today},
        {"$set": {"count": curr}},
        upsert=True
    )
    
    return jsonify({'status': 'success', 'streak': streak})

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

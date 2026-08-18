require('dotenv').config();
const express = require('express');
const path = require('path');
const cors = require('cors');
const { createClient } = require('@supabase/supabase-js');

const app = express();
const PORT = process.env.PORT || 5000;

// Enable CORS and JSON parsing
app.use(cors());
app.use(express.json());

// --- Supabase Setup ---
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_KEY;

if (!SUPABASE_URL || !SUPABASE_KEY) {
    console.error("Supabase credentials missing! Check your .env file.");
    process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// Helper function to get Date in IST (Asia/Kolkata)
const getISTDate = (offsetDays = 0) => {
    const d = new Date();
    d.setDate(d.getDate() + offsetDays);
    const options = { timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit' };
    return new Intl.DateTimeFormat('en-CA', options).format(d); // YYYY-MM-DD format
};

// --- Serve Static Assets ---
app.use('/static', express.static(path.join(__dirname, 'static')));

app.get('/manifest.json', (req, res) => {
    res.sendFile(path.join(__dirname, 'manifest.json'));
});

app.get('/sw.js', (req, res) => {
    res.setHeader('Content-Type', 'application/javascript');
    res.sendFile(path.join(__dirname, 'static', 'sw.js'));
});

// --- Page Routes ---
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'index.html'));
});

app.get('/auto-jap.html', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'auto-jap.html'));
});

// --- API Routes ---

// Get current user count and history
app.get('/get_count', async (req, res) => {
    const userId = req.query.user_id;
    if (!userId) {
        return res.status(400).json({ error: 'User ID missing' });
    }

    const today = getISTDate(0);
    const yesterday = getISTDate(-1);

    try {
        // Query jap_counter table
        const { data: counterData, error: counterError } = await supabase
            .from('jap_counter')
            .select('*')
            .eq('user_id', userId);

        if (counterError) throw counterError;

        if (!counterData || counterData.length === 0) {
            // New user, create default row
            const newRow = {
                user_id: userId,
                current_count: 0,
                total_count: 0,
                last_date: today,
                streak: 0
            };
            const { error: insertError } = await supabase
                .from('jap_counter')
                .insert(newRow);

            if (insertError) throw insertError;

            return res.json({
                current_count: 0,
                total_count: 0,
                streak: 0,
                today: today,
                history: {}
            });
        }

        const row = counterData[0];
        let currVal = row.current_count;
        const totalVal = row.total_count;
        let lastDate = row.last_date;
        let streak = row.streak;

        // Check if date changed (new day logic)
        if (lastDate !== today) {
            if (lastDate === yesterday && currVal > 0) {
                streak += 1;
            } else {
                streak = 0;
            }

            currVal = 0;
            const { error: updateError } = await supabase
                .from('jap_counter')
                .update({
                    current_count: 0,
                    last_date: today,
                    streak: streak
                })
                .eq('user_id', userId);

            if (updateError) throw updateError;
        }

        // Fetch history data
        const { data: historyData, error: historyError } = await supabase
            .from('jap_history')
            .select('*')
            .eq('user_id', userId);

        if (historyError) throw historyError;

        const history = {};
        if (historyData) {
            historyData.forEach(item => {
                history[item.date] = item.count;
            });
        }

        return res.json({
            current_count: currVal,
            total_count: totalVal,
            streak: streak,
            today: today,
            history: history
        });

    } catch (err) {
        console.error("Error in /get_count:", err);
        return res.status(500).json({ error: err.message });
    }
});

// Update user counts
app.post('/update_count', async (req, res) => {
    const { user_id: userId, current_count: curr, total_count: total } = req.body;
    if (!userId) {
        return res.status(400).json({ error: 'User ID missing' });
    }

    const today = getISTDate(0);

    try {
        // 1. Check current streak in database
        const { data: counterData, error: fetchError } = await supabase
            .from('jap_counter')
            .select('streak')
            .eq('user_id', userId);

        if (fetchError) throw fetchError;
        let streak = (counterData && counterData.length > 0) ? counterData[0].streak : 0;

        // 2. If first time chanting today and streak is 0, make it 1
        if (curr > 0 && streak === 0) {
            streak = 1;
            const { error: updateError } = await supabase
                .from('jap_counter')
                .update({
                    current_count: curr,
                    total_count: total,
                    last_date: today,
                    streak: streak
                })
                .eq('user_id', userId);
            
            if (updateError) throw updateError;
        } else {
            const { error: updateError } = await supabase
                .from('jap_counter')
                .update({
                    current_count: curr,
                    total_count: total,
                    last_date: today
                })
                .eq('user_id', userId);
            
            if (updateError) throw updateError;
        }

        // 3. Upsert into history table
        const { error: upsertError } = await supabase
            .from('jap_history')
            .upsert({
                user_id: userId,
                date: today,
                count: curr
            });

        if (upsertError) throw upsertError;

        return res.json({ status: 'success', streak: streak });

    } catch (err) {
        console.error("Error in /update_count:", err);
        return res.status(500).json({ error: err.message });
    }
});

// Start the Server
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});

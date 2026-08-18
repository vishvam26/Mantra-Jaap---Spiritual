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

app.get('/aarti.html', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'aarti.html'));
});

// --- API Routes ---

// Helper function to check if the query is spiritual/devotional
const isSpiritualQuery = (query) => {
    if (!query) return false;
    const q = query.toLowerCase();
    
    const spiritualKeywords = [
        // Devotional terms
        'aarti', 'arti', 'bhajan', 'kirtan', 'dhun', 'chalisa', 'stotra', 'mantra', 'jap', 'jaap', 'shloka', 'stuti', 
        'devotional', 'spiritual', 'path', 'paath', 'prayer', 'bhakti', 'gita', 'geeta', 'chants', 'chanting', 'kathaa', 'katha',
        // Deity/Spiritual Names (English/Hindi transliteration)
        'ganesh', 'ganpati', 'hanuman', 'ram', 'rama', 'krishna', 'shiva', 'shiv', 'mahadev', 'bholenath', 'durga', 
        'laxmi', 'lakshmi', 'saraswati', 'vishnu', 'radha', 'radhe', 'swaminarayan', 'sai', 'bhagwan', 'narayan', 
        'kali', 'amritwani', 'ganesha', 'govinda', 'radheshyam', 'shyam', 'murli', 'baba', 'mata', 'mataji', 'devi', 
        'ambaji', 'khodiyar', 'mogal', 'bahuchar', 'gayatri', 'sharda', 'bramha', 'sarangpur', 'salangpur', 'kashtbhanjan',
        // Gujarati script support for key terms
        'આરતી', 'આરતિ', 'ભજન', 'કીર્તન', 'કીર્તનો', 'ધૂન', 'ચાલીસા', 'સ્તોત્ર', 'મંત્ર', 'જાપ', 'શ્લોક', 'સ્તુતિ', 'ભક્તિ', 'ગીતા', 'કથા',
        'ગણેશ', 'ગણપતિ', 'હનુમાન', 'રામ', 'કૃષ્ણ', 'શિવ', 'મહાદેવ', 'દુર્ગા', 'લક્ષ્મી', 'સરસ્વતી', 'વિષ્ણુ', 'રાધા', 'રાધે', 'સ્વામિનારાયણ', 'સાઈ'
    ];
    
    return spiritualKeywords.some(keyword => q.includes(keyword));
};

// API to search Aarti videos from YouTube without API Key
app.get('/api/search_aarti', async (req, res) => {
    const query = req.query.q;
    if (!query) {
        return res.status(400).json({ error: 'Search query missing' });
    }
    
    // Restrict search results to spiritual/devotional queries only
    if (!isSpiritualQuery(query)) {
        return res.json([]); // Return empty list for unrelated searches
    }
    
    // Append "aarti" to query if not present to ensure relevant devotional results
    const searchQuery = query.toLowerCase().includes('aarti') || 
                        query.toLowerCase().includes('chalisa') || 
                        query.toLowerCase().includes('bhajan') ||
                        query.toLowerCase().includes('mantra')
        ? query 
        : `${query} aarti`;
        
    const url = `https://www.youtube.com/results?search_query=${encodeURIComponent(searchQuery)}`;
    
    try {
        const response = await fetch(url, {
            headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9'
            }
        });
        const html = await response.text();
        
        const regex = /var ytInitialData = ({.*?});/;
        const match = html.match(regex);
        
        if (!match) {
            return res.json([]);
        }
        
        const data = JSON.parse(match[1]);
        const videos = [];
        
        function findVideoRenderers(obj) {
            if (!obj || typeof obj !== 'object') return;
            
            if (obj.videoRenderer) {
                const video = obj.videoRenderer;
                const videoId = video.videoId;
                
                let title = 'Unknown';
                if (video.title && video.title.runs && video.title.runs[0]) {
                    title = video.title.runs[0].text;
                } else if (video.title && video.title.simpleText) {
                    title = video.title.simpleText;
                }
                
                let thumbnailUrl = '';
                if (video.thumbnail && video.thumbnail.thumbnails && video.thumbnail.thumbnails[0]) {
                    thumbnailUrl = video.thumbnail.thumbnails[0].url;
                }
                
                let duration = 'Unknown';
                if (video.lengthText && video.lengthText.runs && video.lengthText.runs[0]) {
                    duration = video.lengthText.runs[0].text;
                } else if (video.lengthText && video.lengthText.simpleText) {
                    duration = video.lengthText.simpleText;
                }
                
                if (videoId) {
                    videos.push({ videoId, title, thumbnailUrl, duration });
                }
            } else {
                for (const key in obj) {
                    if (Object.prototype.hasOwnProperty.call(obj, key)) {
                        findVideoRenderers(obj[key]);
                    }
                }
            }
        }
        
        findVideoRenderers(data);
        return res.json(videos);
        
    } catch (err) {
        console.error("YouTube search error:", err);
        return res.status(500).json({ error: 'Failed to fetch search results from YouTube' });
    }
});

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

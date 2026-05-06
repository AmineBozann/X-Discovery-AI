import datetime
import json
import math
import sqlite3
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DB_PATH = 'database.db'

def get_db_connection():
    # timeout ve check_same_thread kilitlenmeleri önlemek için kritik
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS discoveries 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, repo_name TEXT, score REAL, discovery_date TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS global_stats 
                        (key TEXT PRIMARY KEY, value INTEGER)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS cache 
                        (keyword TEXT PRIMARY KEY, data TEXT, timestamp DATETIME)''')
        conn.execute("INSERT OR IGNORE INTO global_stats (key, value) VALUES ('github_clicks', 0)")
        conn.execute("INSERT OR IGNORE INTO global_stats (key, value) VALUES ('total_searches', 0)")
        conn.commit()
    finally:
        conn.close()

init_db()

def advanced_scoring(repo):
    """
    GÜNCELLENMİŞ MÜHENDİSLİK MODELİ
    Issue Paradox çözüldü, Stabilite Endeksi eklendi.
    """
    stars = repo.get('stargazers_count', 0)
    forks = repo.get('forks_count', 0)
    open_issues = repo.get('open_issues_count', 0)
    pushed_at = repo.get('pushed_at', "")
    
    now = datetime.datetime.now()
    try:
        push_date = datetime.datetime.strptime(pushed_at, '%Y-%m-%dT%H:%M:%SZ')
    except:
        push_date = now

    # 1. Popülerlik Bileşeni (Logaritmik Normalizasyon)
    popularity_score = (math.log10(stars + 1) * 20) + (math.log10(forks + 1) * 10)
    
    # 2. Kalite ve Stabilite Endeksi (YENİ FORMÜL)
    # Projeyi fork edenlerin ne kadarının sorunla (issue) karşılaştığını ölçer.
    denominator = forks + open_issues
    quality_index = (forks / denominator * 100) if denominator > 0 else 0
    
    # 3. Zaman Duyarlı Bozulma Çarpanı (Decay Function)
    inactivity_days = (now - push_date).days
    decay_multiplier = 1.0
    if inactivity_days > 365: 
        decay_multiplier = 0.1  # 1 yıldan eski ise %90 ceza
    elif inactivity_days > 180: 
        decay_multiplier = 0.5  # 6 ay - 1 yıl arası %50 ceza

    # Nihai Skor: Kalite ağırlığı %60, Popülerlik %40
    final_score = round(((popularity_score * 0.4) + (quality_index * 0.6)) * decay_multiplier, 2)

    return {
        "score": final_score,
        "quality": round(quality_index, 2),
        "explanation": "Dinamik" if inactivity_days < 30 else "Standart",
        "pushed_date": pushed_at[:10],
        "created_date": repo.get('created_at', "")[:10],
        "tag": "ELİT" if final_score > 65 else ("STABİL" if final_score > 35 else "RİSKLİ")
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    keyword = data.get('keyword', '').lower().strip()
    requested_page = data.get('page', 1)
    per_page = 20
    
    if not keyword:
        return jsonify({"results": [], "total_count": 0})

    conn = get_db_connection()
    try:
        # 1. ÖNBELLEK KONTROLÜ
        cache_hit = conn.execute("SELECT data FROM cache WHERE keyword=?", (keyword,)).fetchone()
        
        if cache_hit:
            full_pool = json.loads(cache_hit['data'])
            all_results = full_pool['all_results']
            start = (requested_page - 1) * per_page
            end = start + per_page
            return jsonify({
                "results": all_results[start:end],
                "total_count": full_pool['total_count'],
                "pages": math.ceil(len(all_results) / per_page),
                "current_page": requested_page
            })

        # 2. YENİ ARAMA
        all_analyzed_results = []
        total_found_github = 0
        headers = {'Accept': 'application/vnd.github.v3+json', 'User-Agent': 'Mozilla/5.0'}
        
        for page_num in range(1, 6):
            api_url = f"https://api.github.com/search/repositories?q={keyword}&sort=stars&order=desc&per_page=20&page={page_num}"
            r = requests.get(api_url, headers=headers, timeout=10)
            if r.status_code != 200: break
            
            gh_data = r.json()
            if page_num == 1: total_found_github = gh_data.get('total_count', 0)
            
            items = gh_data.get('items', [])
            if not items: break

            for item in items:
                analysis = advanced_scoring(item)
                all_analyzed_results.append({
                    "name": item['name'],
                    "owner": item['owner']['login'],
                    "description": item['description'] or "Açıklama yok.",
                    "url": item['html_url'],
                    "stars": item['stargazers_count'],
                    "forks": item['forks_count'],
                    "issues": item['open_issues_count'],
                    "score": analysis['score'],
                    "quality": analysis['quality'],
                    "explanation": analysis['explanation'],
                    "pushed_date": analysis['pushed_date'],
                    "created_date": analysis['created_date'],
                    "tag": analysis['tag']
                })

        # Skora göre KÜRESEL sıralama
        all_analyzed_results.sort(key=lambda x: x['score'], reverse=True)

        # Önbelleğe yaz ve bağlantıyı hemen kapat
        cache_save = {"all_results": all_analyzed_results, "total_count": total_found_github}
        conn.execute("INSERT OR REPLACE INTO cache (keyword, data, timestamp) VALUES (?, ?, ?)",
                     (keyword, json.dumps(cache_save), datetime.datetime.now().isoformat()))
        conn.execute("UPDATE global_stats SET value = value + 1 WHERE key = 'total_searches'")
        conn.commit()

        start = (requested_page - 1) * per_page
        return jsonify({
            "results": all_analyzed_results[start:start+per_page],
            "total_count": total_found_github,
            "pages": math.ceil(len(all_analyzed_results) / per_page),
            "current_page": requested_page
        })
    finally:
        conn.close()

@app.route('/get_stats')
def get_stats():
    conn = get_db_connection()
    try:
        clicks = conn.execute("SELECT value FROM global_stats WHERE key='github_clicks'").fetchone()[0]
        searches = conn.execute("SELECT value FROM global_stats WHERE key='total_searches'").fetchone()[0]
        db_count = conn.execute('SELECT COUNT(*) FROM discoveries').fetchone()[0]
        return jsonify({"clicks": clicks, "searches": searches, "db_total": db_count})
    finally:
        conn.close()

@app.route('/track_discovery', methods=['POST'])
def track():
    data = request.get_json()
    conn = get_db_connection()
    try:
        conn.execute("UPDATE global_stats SET value = value + 1 WHERE key = 'github_clicks'")
        conn.execute('INSERT INTO discoveries (repo_name, score, discovery_date) VALUES (?, ?, ?)',
                    (data.get('name'), data.get('score'), datetime.datetime.now().isoformat()))
        conn.commit()
        return jsonify({"status": "ok"})
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5001, threaded=True)
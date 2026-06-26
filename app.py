import datetime
import json
import math
import sqlite3
import requests
import statistics
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
DB_PATH = 'database.db'

def get_db_connection():
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

# --- AKADEMİK ANALİZ MODÜLLERİ ---

def run_sensitivity_analysis(repo):
    stars = repo.get('stargazers_count', 0)
    forks = repo.get('forks_count', 0)
    issues = repo.get('open_issues_count', 0)
    
    pop_base = (math.log10(stars + 1) * 20) + (math.log10(forks + 1) * 10)
    qual_base = (forks / (forks + issues) * 100) if (forks + issues) > 0 else 0
    
    scenarios = []
    for w in [0.2, 0.4, 0.6, 0.8]:
        s = (pop_base * w) + (qual_base * (1 - w))
        scenarios.append(s)
    
    return round(statistics.stdev(scenarios), 2) if len(scenarios) > 1 else 0

def run_academic_validation(results):
    if not results: return {"precision": 0, "recall": 0}
    ground_truth = [r for r in results if r['stars'] > 30000 and r['quality'] > 50]
    model_prediction = [r for r in results if r['tag'] == "ELİT"]
    
    tp = len([r for r in model_prediction if r in ground_truth])
    fp = len(model_prediction) - tp
    fn = len(ground_truth) - tp
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    
    return {"precision": round(precision, 2), "recall": round(recall, 2)}

# --- GÜNCEL SKORLAMA (ÇARPIMSAL SÖNÜMLEME) ---

def advanced_scoring(repo):
    stars = repo.get('stargazers_count', 0)
    forks = repo.get('forks_count', 0)
    open_issues = repo.get('open_issues_count', 0)
    pushed_at = repo.get('pushed_at', "")
    
    now = datetime.datetime.now()
    try:
        push_date = datetime.datetime.strptime(pushed_at, '%Y-%m-%dT%H:%M:%SZ')
    except:
        push_date = now

    popularity_score = (math.log10(stars + 1) * 20) + (math.log10(forks + 1) * 10)
    denominator = forks + open_issues
    quality_index = (forks / denominator * 100) if denominator > 0 else 0
    
    # Matematiksel olarak düzeltilmiş zaman sönümleme (Çarpanlı)
    inactivity_days = (now - push_date).days
    if inactivity_days <= 30:
        decay_multiplier = 1.0
    elif inactivity_days <= 180:
        decay_multiplier = 0.5
    else:
        decay_multiplier = 0.1

    final_score = round(((popularity_score * 0.4) + (quality_index * 0.6)) * decay_multiplier, 2)
    dev_index = run_sensitivity_analysis(repo)

    return {
        "score": final_score,
        "quality": round(quality_index, 2),
        "explanation": "Dinamik" if inactivity_days < 30 else "Standart",
        "pushed_date": pushed_at[:10],
        "created_date": repo.get('created_at', "")[:10],
        "tag": "ELİT" if final_score > 65 else ("STABİL" if final_score > 35 else "RİSKLİ"),
        "sensitivity": dev_index
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
        cache_hit = conn.execute("SELECT data FROM cache WHERE keyword=?", (keyword,)).fetchone()
        
        if cache_hit:
            full_pool = json.loads(cache_hit['data'])
            all_results = full_pool['all_results']
            validation = run_academic_validation(all_results)
            total_found_github = full_pool['total_count']
        else:
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
                        "tag": analysis['tag'],
                        "sensitivity": analysis['sensitivity']
                    })

            all_analyzed_results.sort(key=lambda x: x['score'], reverse=True)
            validation = run_academic_validation(all_analyzed_results)
            
            cache_save = {"all_results": all_analyzed_results, "total_count": total_found_github}
            conn.execute("INSERT OR REPLACE INTO cache (keyword, data, timestamp) VALUES (?, ?, ?)",
                         (keyword, json.dumps(cache_save), datetime.datetime.now().isoformat()))
            conn.execute("UPDATE global_stats SET value = value + 1 WHERE key = 'total_searches'")
            conn.commit()
            all_results = all_analyzed_results

        start = (requested_page - 1) * per_page
        return jsonify({
            "results": all_results[start:start+per_page],
            "total_count": total_found_github,
            "pages": math.ceil(len(all_results) / per_page),
            "current_page": requested_page,
            "academic_metrics": validation
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
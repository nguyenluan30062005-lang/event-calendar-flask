from flask import Flask, request, render_template, jsonify
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# SỬA LỖI QUAN TRỌNG: Xác định đúng đường dẫn database trên Azure
def get_db_path():
    # Trên Azure, lưu database trong /home để dữ liệu không bị mất
    if 'HOME' in os.environ:  # Môi trường Azure có biến này
        return '/home/events.db'
    else:
        return 'events.db'  # Dùng cho local

def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.close()

init_db()

# Lấy kết nối đến database
def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # Giúp truy vấn trả về dictionary
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def add_event():
    try:
        date = request.form['event_date']
        desc = request.form['description']
        
        conn = get_db_connection()
        conn.execute("INSERT INTO events (event_date, description) VALUES (?, ?)", (date, desc))
        conn.commit()
        conn.close()
        
        # Trả về JSON (phù hợp hơn cho frontend)
        return jsonify({
            'success': True,
            'message': f'✅ Sự kiện đã lưu cho ngày {date}!',
            'date': date,
            'description': desc
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API MỚI: Lấy tất cả sự kiện (đã sắp xếp)
@app.route('/api/events')
def get_all_events():
    conn = get_db_connection()
    cursor = conn.execute('''
        SELECT id, event_date, description 
        FROM events 
        ORDER BY event_date DESC, created_at DESC
    ''')
    
    events = []
    for row in cursor.fetchall():
        events.append({
            'id': row['id'],
            'date': row['event_date'],
            'description': row['description']
        })
    
    conn.close()
    return jsonify(events)

# API MỚI: Lấy sự kiện theo tháng
@app.route('/api/events/month/<year_month>')
def get_events_by_month(year_month):
    conn = get_db_connection()
    cursor = conn.execute('''
        SELECT event_date, description 
        FROM events 
        WHERE strftime('%Y-%m', event_date) = ?
        ORDER BY event_date
    ''', (year_month,))
    
    events = []
    for row in cursor.fetchall():
        events.append({
            'date': row['event_date'],
            'description': row['description']
        })
    
    conn.close()
    return jsonify(events)

# API MỚI: Xóa sự kiện
@app.route('/api/events/delete/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '🗑️ Đã xóa sự kiện'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# API MỚI: Health check (cho Azure monitor)
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'event-calendar-flask'})

# Route cũ của bạn (giữ để tương thích)
@app.route('/view', methods=['GET'])
def view_event():
    date = request.args.get('event_date')
    conn = get_db_connection()
    cursor = conn.execute("SELECT description FROM events WHERE event_date = ?", (date,))
    events = cursor.fetchall()
    conn.close()
    
    html = f"<h3>Sự kiện ngày {date}</h3><ul>"
    for e in events:
        html += f"<li>{e[0]}</li>"
    html += "</ul><a href='/'>🏠 Quay lại</a>"
    return html

# KHỞI CHẠY ỨNG DỤNG
if __name__ == '__main__':
    # Azure cung cấp PORT qua biến môi trường
    port = int(os.environ.get('PORT', 5000))
    # CHÚ Ý: Trên production KHÔNG dùng debug=True
    app.run(host='0.0.0.0', port=port, debug=False)

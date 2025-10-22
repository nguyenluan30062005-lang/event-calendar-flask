from flask import Flask, request, render_template
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('events.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT NOT NULL,
            description TEXT NOT NULL
        )
    ''')
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def add_event():
    date = request.form['event_date']
    desc = request.form['description']
    conn = sqlite3.connect('events.db')
    conn.execute("INSERT INTO events (event_date, description) VALUES (?, ?)", (date, desc))
    conn.commit()
    conn.close()
    return f"Sự kiện đã lưu cho ngày {date}! <a href='/'>Quay lại</a>"

@app.route('/view', methods=['GET'])
def view_event():
    date = request.args.get('event_date')
    conn = sqlite3.connect('events.db')
    cursor = conn.execute("SELECT description FROM events WHERE event_date = ?", (date,))
    events = cursor.fetchall()
    conn.close()
    html = f"<h3>Sự kiện ngày {date}</h3><ul>"
    for e in events:
        html += f"<li>{e[0]}</li>"
    html += "</ul><a href='/'>Quay lại</a>"
    return html

if __name__ == '__main__':
    app.run()

from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
import sqlite3
import os
import tempfile
from datetime import timedelta

app = Flask(__name__)
# 세션 설정 수정
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = tempfile.gettempdir()
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 세션 유지 기간 7일
Session(app)

def get_db():
    db = sqlite3.connect('users.db')
    db.row_factory = sqlite3.Row
    return db

# 데이터베이스 초기화
def init_db():
    if not os.path.exists('users.db'):
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT UNIQUE NOT NULL,
                quest1_completed INTEGER DEFAULT 0,
                quest2_completed INTEGER DEFAULT 0,
                quest3_completed INTEGER DEFAULT 0,
                quest4_completed INTEGER DEFAULT 0,
                quest5_completed INTEGER DEFAULT 0
            )
        ''')
        db.commit()
        db.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def login():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM users')
    existing_users = cursor.fetchone()['count'] > 0
    
    if request.method == 'POST':
        nickname = request.form['nickname']
        cursor.execute('SELECT * FROM users WHERE nickname = ?', (nickname,))
        user = cursor.fetchone()
        
        if user is None:
            cursor.execute('''
                INSERT INTO users (nickname, quest1_completed, quest2_completed, 
                quest3_completed, quest4_completed, quest5_completed) 
                VALUES (?, 0, 0, 0, 0, 0)
            ''', (nickname,))
            db.commit()
            cursor.execute('SELECT * FROM users WHERE nickname = ?', (nickname,))
            user = cursor.fetchone()
        
        session.permanent = True  # 세션 영구 저장 설정
        session['user_id'] = user['id']
        db.close()
        return redirect(url_for('quests'))
    
    return render_template('login.html', existing_users=existing_users)

@app.route('/quests')
def quests():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    
    environmental_quests = [
        "일회용품 사용하지 않기",
        "재활용품 분리배출하기",
        "물 절약하기",
        "전기 절약하기",
        "대중교통 이용하기"
    ]
    
    quest_status = [
        user['quest1_completed'],
        user['quest2_completed'],
        user['quest3_completed'],
        user['quest4_completed'],
        user['quest5_completed']
    ]
    
    completed_count = sum(quest_status)
    progress = (completed_count / 5) * 100
    db.close()
    
    return render_template('quests.html', 
                         nickname=user['nickname'],
                         quests=environmental_quests,
                         quest_status=quest_status,
                         progress=progress,
                         all_completed=(completed_count == 5))

@app.route('/complete_quest/<int:quest_id>')
def complete_quest(quest_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if quest_id < 1 or quest_id > 5:
        return redirect(url_for('quests'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute(f'UPDATE users SET quest{quest_id}_completed = 1 WHERE id = ?', 
                  (session['user_id'],))
    db.commit()
    db.close()
    
    return redirect(url_for('quests'))

@app.route('/thanks')
def thanks():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT SUM(quest1_completed + quest2_completed + quest3_completed + quest4_completed + quest5_completed) as total FROM users WHERE id = ?', (session['user_id'],))
    completed_count = cursor.fetchone()['total']
    db.close()
    
    if completed_count < 5:
        return redirect(url_for('quests'))
        
    return render_template('thanks.html')

if __name__ == '__main__':
    app.run(debug=True)
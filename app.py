import os
import uuid
import json
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Renderなどの本番環境では環境変数 'DATABASE_URL' がセットされる
# ローカル環境ではそのまま 'sqlite:///schedule.db' を使用する
database_url = os.environ.get('DATABASE_URL', 'sqlite:///schedule.db')
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# データベースのモデル定義
class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.String(8), primary_key=True)
    title = db.Column(db.String(200))
    dates = db.Column(db.Text)

class Answer(db.Model):
    __tablename__ = 'answers'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(8), db.ForeignKey('events.id'))
    participant_name = db.Column(db.String(100))
    answers_json = db.Column(db.Text)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/event/<event_id>')
def event_page(event_id):
    return render_template('index.html')

@app.route('/api/events', methods=['POST'])
def create_event():
    data = request.json
    dates = data.get('dates', [])
    title = data.get('title', '無題のイベント')
    
    event_id = uuid.uuid4().hex[:8]
    
    new_event = Event(id=event_id, title=title, dates=json.dumps(dates))
    db.session.add(new_event)
    db.session.commit()
    
    return jsonify({'id': event_id})

@app.route('/api/events/<event_id>', methods=['GET'])
def get_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({'error': 'Not found'}), 404
        
    answers_rows = Answer.query.filter_by(event_id=event_id).all()
    
    event_data = {
        'id': event.id,
        'title': event.title,
        'dates': json.loads(event.dates)
    }
    
    answers = []
    for r in answers_rows:
        answers.append({
            'id': r.id,
            'participant_name': r.participant_name,
            'answers': json.loads(r.answers_json)
        })
        
    return jsonify({'event': event_data, 'answers': answers})

@app.route('/api/events/<event_id>/answers', methods=['POST'])
def submit_answer(event_id):
    data = request.json
    name = data.get('participant_name')
    answers_dict = data.get('answers', {})
    
    existing = Answer.query.filter_by(event_id=event_id, participant_name=name).first()
    
    if existing:
        existing.answers_json = json.dumps(answers_dict)
    else:
        new_answer = Answer(event_id=event_id, participant_name=name, answers_json=json.dumps(answers_dict))
        db.session.add(new_answer)
        
    db.session.commit()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    with app.app_context():
        # テーブルが存在しない場合のみ作成
        db.create_all()
    # ローカル開発用サーバーの起動
    app.run(debug=True, port=3000)

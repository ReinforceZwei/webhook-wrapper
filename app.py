from flask import Flask, request, jsonify
import sqlite3
import requests

DB_FILENAME = 'data.db'
DB_SCHEMA = """
create table if not exists "application" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" text NOT NULL UNIQUE,
    "webhook_url" text NOT NULL
);
"""
class ApiDatabase:
    def __init__(self):
        self._db = sqlite3.connect(DB_FILENAME, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._cur = self._db.cursor()
        self._cur.execute(DB_SCHEMA)
        self._db.commit()
    
    def _fetch_all(self):
        return [dict(row) for row in self._cur.fetchall()]
    
    def list_app(self):
        sql = 'SELECT * FROM application'
        self._cur.execute(sql)
        return self._fetch_all()
    
    def get_app(self, name):
        sql = 'SELECT * FROM application WHERE name = ?'
        self._cur.execute(sql, name)
        return self._cur.fetchone()
    
    def add_app(self, name, webhook):
        sql = 'INSERT INTO application(name,webhook_url) VALUES(?,?)'
        self._cur.execute(sql, (name, webhook))
        self._db.commit()
        return
    
    def delete_app(self, name):
        sql = 'DELETE FROM application WHERE name = ?'
        self._cur.execute(sql, name)
        self._db.commit()
        return
    
    def update_app(self, name, webhook):
        sql = 'UPDATE application SET webhook_url = ? WHERE name = ?'
        self._cur.execute(sql, (webhook, name))
        self._db.commit()
        return

def post_webhook(url, name, content):
    return

app = Flask(__name__)
db = ApiDatabase()

@app.route("/")
def index():
    return "Will be control panel"

@app.route("/list")
def list_app():
    return jsonify(db.list_app())

@app.route("/add", methods=['POST'])
def add_app():
    name = request.values.get("name", "", type=str)
    webhook = request.values.get("webhook", "", type=str)
    if name and webhook:
        db.add_app(name, webhook)
    return "OK"

@app.route("/delete/<str:name>", methods=['DELETE'])
def delete_app(name):
    db.delete_app(name)
    return "OK"

@app.route("/send/<str:name>")
def execute_webhook(name):
    if request.method == 'GET':
        content = request.args.get('content', '', type=str)
    elif request.method == 'POST':
        content = request.values.get('content', '', type=str)
    w = db.get_app(name)
    if w:
        url = w['webhook_url']
        requests.post()

app.run()

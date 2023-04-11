from flask import Flask, redirect, render_template, request, jsonify, url_for, send_from_directory
import sqlite3
import requests

DB_FILENAME = 'db/data.db'
DB_SCHEMA = """
create table if not exists "application" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" text NOT NULL,
    "webhook_id" integer,
    FOREIGN KEY ("webhook_id") REFERENCES "webhook" ("id") ON DELETE SET NULL
);
create table if not exists "webhook" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" text NOT NULL,
    "url" text NOT NULL,
    "template" text NOT NULL DEFAULT '{"username":"$name","content":"$content"}'
);
"""
class ApiDatabase:
    def __init__(self):
        self._db = sqlite3.connect(DB_FILENAME, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._cur = self._db.cursor()
        self._cur.executescript(DB_SCHEMA)
        self._db.commit()
    
    def _fetch_all(self):
        return [dict(row) for row in self._cur.fetchall()]
    
    def list_app(self):
        sql = 'SELECT a.*,b.name as webhook_name FROM application as a JOIN webhook as b ON webhook_id = b.id'
        self._cur.execute(sql)
        return self._fetch_all()
    
    def list_webhook(self):
        sql = 'SELECT * FROM webhook'
        self._cur.execute(sql)
        return self._fetch_all()

    def get_app(self, id):
        sql = 'SELECT a.id as id,a.name as name,b.url as webhook_url,b.template as template FROM application as a JOIN webhook as b ON webhook_id = b.id WHERE a.id = ?'
        self._cur.execute(sql, (id,))
        return self._cur.fetchone()
    
    def get_webhook(self, id):
        sql = 'SELECT * FROM webhook WHERE id = ?'
        self._cur.execute(sql, (id,))
        return self._cur.fetchone()
    
    def add_app(self, name, webhook_id) -> int:
        sql = 'INSERT INTO application(name,webhook_id) VALUES(?,?)'
        self._cur.execute(sql, (name, webhook_id))
        self._db.commit()
        return self._cur.lastrowid
    
    def add_webhook(self, name, url, template) -> int:
        if template:
            sql = 'INSERT INTO webhook(name,url,template) VALUES(?,?,?)'
            self._cur.execute(sql, (name, url, template))
        else:
            # FIXME: Dont set default on db
            sql = 'INSERT INTO webhook(name,url) VALUES(?,?)'
            self._cur.execute(sql, (name, url))
        self._db.commit()
        return self._cur.lastrowid
    
    def delete_app(self, id):
        sql = 'DELETE FROM application WHERE id = ?'
        self._cur.execute(sql, (id,))
        self._db.commit()
        return
    
    def delete_webhook(self, id):
        sql = 'DELETE FROM webhook WHERE id = ?'
        self._cur.execute(sql, (id,))
        self._db.commit()
        return
    
    def update_app(self, id, name, webhook_id):
        sql = 'UPDATE application SET webhook_id = ?, name = ? WHERE id = ?'
        self._cur.execute(sql, (webhook_id, name, id))
        self._db.commit()
        return
    
    def update_webhook(self, id, name, url, template):
        sql = 'UPDATE webhook SET url = ?, name = ?, template = ? WHERE id = ?'
        self._cur.execute(sql, (url, name, template, id))
        self._db.commit()
        return

def post_webhook(url, template, name, content):
    #BODY_TEMPLATE = '{"username":"$name","content":"$content"}'
    b = template.replace('$name', name.replace('"', '\\"')).replace('$content', content.replace('"', '\\"'))
    b = b.encode('utf-8')
    r = requests.post(url, b, headers={'content-type': 'application/json'})
    return r.status_code == 200

app = Flask(__name__)
db = ApiDatabase()

@app.route("/")
def index():
    return redirect(url_for('dashboard'))

# @app.route("/static/<path:path>")
# def static(path):
#     return send_from_directory("static", path)

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        t = request.values.get('type')
        if t == 'app':
            a = request.values.get('action')
            id = request.values.get('id')
            name = request.values.get('name')
            webhook_id = request.values.get('webhook_id')
            if a == 'create':
                db.add_app(name, webhook_id)
            elif a == 'update':
                db.update_app(id, name, webhook_id)
            elif a == 'delete':
                db.delete_app(id)
        elif t == 'webhook':
            a = request.values.get('action')
            id = request.values.get('id')
            name = request.values.get('name')
            url = request.values.get('url')
            template = request.values.get('template')
            if a == 'create':
                db.add_webhook(name, url, None)
            elif a == 'update':
                db.update_webhook(id, name, url, template)
            elif a == 'delete':
                db.delete_webhook(id)
        return redirect(url_for('dashboard'))
    a = db.list_app()
    w = db.list_webhook()
    return render_template('dashboard.html', app=a, webhook=w)

@app.route("/app/list")
def list_app():
    return jsonify(db.list_app())

@app.route("/app/add", methods=['POST'])
def add_app():
    name = request.values.get("name", "", type=str)
    webhook_id = request.values.get("webhook_id", "", type=int)
    if name and webhook_id:
        if db.get_webhook(webhook_id):
            id = db.add_app(name, webhook_id)
            return str(id), 201
        else:
            return "Not Found", 404
    else:
        return "Bad Request", 400

@app.route("/app/delete/<int:id>", methods=['DELETE'])
def delete_app(id):
    db.delete_app(id)
    return "OK"

@app.route("/app/update/<int:id>", methods=['POST', 'UPDATE'])
def update_app(id):
    name = request.values.get("name", "", type=str)
    webhook_id = request.values.get("webhook_id", "", type=int)
    if name and webhook_id:
        db.update_app(id, name, webhook_id)
        return "OK"
    else:
        return "Bad Request", 400

@app.route("/webhook/list")
def list_webhook():
    return jsonify(db.list_webhook())

@app.route("/webhook/add", methods=['POST'])
def add_webhook():
    name = request.values.get("name", "", type=str)
    url = request.values.get("url", "", type=str)
    if name and url:
        id = db.add_webhook(name, url, None)
        return str(id), 201
    else:
        return "Bad Request", 400

@app.route("/webhook/delete/<int:id>")
def delete_webhook(id):
    db.delete_webhook(id)
    return "OK"

@app.route("/webhook/update/<int:id>", methods=['POST', 'UPDATE'])
def update_webhook(id):
    name = request.values.get("name", "", type=str)
    url = request.values.get("url", "", type=str)
    template = request.values.get("template", "", type=str)
    if name and url and template:
        db.update_webhook(id, name, url, template)
        return "OK"
    else:
        return "Bad Request", 400

@app.route("/send/<int:id>", methods=['GET', 'POST'])
def execute_webhook(id):
    if request.method == 'GET':
        content = request.args.get('content', '', type=str)
    elif request.method == 'POST':
        content = request.values.get('content', '', type=str)
    w = db.get_app(id)
    if w:
        if w['webhook_url']:
            url = w['webhook_url']
            post_webhook(url, w['template'], w['name'], content)
            return "OK"
        else:
            return "Bad Webhook ID", 400
    else:
        return "Not Found", 404
    
if __name__ == "__main__":
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(host='0.0.0.0')

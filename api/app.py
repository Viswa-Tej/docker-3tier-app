from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import os, time, logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)
CORS(app)

def get_db():
    for attempt in range(5):
        try:
            return psycopg2.connect(
                host=os.environ["DB_HOST"],
                database=os.environ["DB_NAME"],
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"]
            )
        except Exception as e:
            logger.warning(f"DB not ready, retry {attempt+1}/5: {e}")
            time.sleep(3)
    raise Exception("Cannot connect to database after 5 retries")

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            done BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close(); conn.close()
    logger.info("Database table ready")

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "api"}), 200

@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, title, done, created_at FROM tasks ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return jsonify([{"id": r[0], "title": r[1], "done": r[2], "created_at": str(r[3])} for r in rows])

@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title required"}), 400
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title) VALUES (%s) RETURNING id", (title,))
    tid = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return jsonify({"id": tid, "title": title, "done": False}), 201

@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def update_task(task_id):
    data = request.get_json()
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE tasks SET done=%s WHERE id=%s", (data.get("done", False), task_id))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"id": task_id, "done": data.get("done", False)})

@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_db(); cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"deleted": task_id})

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)

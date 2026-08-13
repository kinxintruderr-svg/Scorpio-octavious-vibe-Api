
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, request, jsonify, g
import jwt
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("JWT_SECRET", "CHANGE_THIS_IN_PRODUCTION")
DB = os.environ.get("DB_PATH", "scorpio.db")

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc=None):
    c = g.pop("db", None)
    if c: c.close()

def init_db():
    c = db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL,
      password_hash TEXT,
      google_id TEXT UNIQUE,
      role TEXT NOT NULL DEFAULT 'user',
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS wallets(
      user_id INTEGER PRIMARY KEY,
      usd_cents INTEGER NOT NULL DEFAULT 0,
      btc REAL NOT NULL DEFAULT 0,
      eth REAL NOT NULL DEFAULT 0,
      usdt REAL NOT NULL DEFAULT 0,
      FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS posts(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      media_url TEXT NOT NULL,
      media_type TEXT NOT NULL,
      caption TEXT DEFAULT '',
      created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS reels(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      video_url TEXT NOT NULL,
      caption TEXT DEFAULT '',
      views INTEGER NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS likes(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      post_id INTEGER,
      reel_id INTEGER,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS comments(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      post_id INTEGER,
      reel_id INTEGER,
      body TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS transactions(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      type TEXT NOT NULL,
      asset TEXT NOT NULL,
      amount REAL NOT NULL,
      status TEXT NOT NULL,
      reference TEXT,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS payout_requests(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      method TEXT NOT NULL,
      destination TEXT NOT NULL,
      amount_cents INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending',
      created_at TEXT NOT NULL
    );
    """)
    c.commit()

def token_for(user):
    payload = {
      "sub": user["id"],
      "role": user["role"],
      "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")

def auth_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        h=request.headers.get("Authorization","")
        if not h.startswith("Bearer "):
            return jsonify(error="Authentication required"),401
        try:
            p=jwt.decode(h[7:], app.config["SECRET_KEY"], algorithms=["HS256"])
        except Exception:
            return jsonify(error="Invalid or expired token"),401
        u=db().execute("SELECT * FROM users WHERE id=?", (p["sub"],)).fetchone()
        if not u: return jsonify(error="User not found"),401
        g.user=u
        return fn(*args, **kwargs)
    return wrapper

@app.route("/api/health")
def health():
    return jsonify(ok=True, service="Scorpio Octavious Vibe backend")

@app.post("/api/auth/register")
def register():
    data=request.get_json(force=True)
    name=(data.get("name") or "").strip()
    email=(data.get("email") or "").strip().lower()
    password=data.get("password") or ""
    if not name or not email or len(password)<8:
        return jsonify(error="Name, email and an 8+ character password are required"),400
    c=db()
    try:
        cur=c.execute(
          "INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)",
          (name,email,generate_password_hash(password),datetime.now(timezone.utc).isoformat())
        )
        uid=cur.lastrowid
        c.execute("INSERT INTO wallets(user_id) VALUES(?)",(uid,))
        c.commit()
    except sqlite3.IntegrityError:
        return jsonify(error="Email already registered"),409
    u=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
    return jsonify(token=token_for(u), user={"id":uid,"name":name,"email":email})

@app.post("/api/auth/login")
def login():
    data=request.get_json(force=True)
    email=(data.get("email") or "").strip().lower()
    password=data.get("password") or ""
    u=db().execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
    if not u or not u["password_hash"] or not check_password_hash(u["password_hash"],password):
        return jsonify(error="Invalid email or password"),401
    return jsonify(token=token_for(u),user={"id":u["id"],"name":u["name"],"email":u["email"]})

@app.post("/api/auth/google")
def google():
    # Production: verify the Google ID token server-side with Google's official library,
    # then create/link the user. Never trust an email supplied by the client alone.
    return jsonify(error="Google OAuth backend is not configured yet"),501

@app.get("/api/me")
@auth_required
def me():
    u=g.user
    return jsonify(id=u["id"],name=u["name"],email=u["email"],role=u["role"])

@app.get("/api/wallet")
@auth_required
def wallet():
    w=db().execute("SELECT * FROM wallets WHERE user_id=?",(g.user["id"],)).fetchone()
    return jsonify(usd=f"{w['usd_cents']/100:.2f}",btc=w["btc"],eth=w["eth"],usdt=w["usdt"])

@app.get("/api/transactions")
@auth_required
def transactions():
    rows=db().execute(
      "SELECT id,type,asset,amount,status,reference,created_at FROM transactions WHERE user_id=? ORDER BY id DESC",
      (g.user["id"],)
    ).fetchall()
    return jsonify(items=[dict(r) for r in rows])

@app.post("/api/posts")
@auth_required
def create_post():
    data=request.get_json(force=True)
    media=(data.get("media_url") or "").strip()
    typ=data.get("media_type") or "image"
    if not media or typ not in ("image","video"):
        return jsonify(error="media_url and media_type=image|video required"),400
    c=db()
    c.execute("INSERT INTO posts(user_id,media_url,media_type,caption,created_at) VALUES(?,?,?,?,?)",
      (g.user["id"],media,typ,data.get("caption",""),datetime.now(timezone.utc).isoformat()))
    c.commit()
    return jsonify(ok=True),201

@app.get("/api/feed")
@auth_required
def feed():
    rows=db().execute("""
      SELECT p.id,p.media_url,p.media_type,p.caption,p.created_at,u.name
      FROM posts p JOIN users u ON u.id=p.user_id
      ORDER BY p.id DESC LIMIT 50
    """).fetchall()
    return jsonify(items=[dict(r) for r in rows])

@app.post("/api/reels")
@auth_required
def create_reel():
    data=request.get_json(force=True)
    url=(data.get("video_url") or "").strip()
    if not url: return jsonify(error="video_url required"),400
    c=db()
    c.execute("INSERT INTO reels(user_id,video_url,caption,created_at) VALUES(?,?,?,?)",
      (g.user["id"],url,data.get("caption",""),datetime.now(timezone.utc).isoformat()))
    c.commit()
    return jsonify(ok=True),201

@app.get("/api/reels")
@auth_required
def list_reels():
    rows=db().execute("""
      SELECT r.id,r.video_url,r.caption,r.views,r.created_at,u.name
      FROM reels r JOIN users u ON u.id=r.user_id
      ORDER BY r.id DESC LIMIT 50
    """).fetchall()
    return jsonify(items=[dict(r) for r in rows])

@app.post("/api/payouts")
@auth_required
def payout():
    data=request.get_json(force=True)
    method=data.get("method")
    destination=(data.get("destination") or "").strip()
    cents=int(data.get("amount_cents") or 0)
    if method not in ("paypal","bank") or not destination or cents<=0:
        return jsonify(error="method=paypal|bank, destination and positive amount_cents required"),400
    # This creates a request only. A real payout provider must be connected before money moves.
    c=db()
    c.execute("""INSERT INTO payout_requests(user_id,method,destination,amount_cents,status,created_at)
                 VALUES(?,?,?,?,?,?)""",
              (g.user["id"],method,destination,cents,"pending",datetime.now(timezone.utc).isoformat()))
    c.commit()
    return jsonify(ok=True,status="pending"),201

@app.get("/api/admin/summary")
@auth_required
def admin_summary():
    if g.user["role"]!="admin": return jsonify(error="Admin only"),403
    c=db()
    users=c.execute("SELECT COUNT(*) n FROM users").fetchone()["n"]
    payouts=c.execute("SELECT COUNT(*) n FROM payout_requests WHERE status='pending'").fetchone()["n"]
    return jsonify(registered_users=users,pending_payouts=payouts)

with app.app_context():
    init_db()

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT","8080")))

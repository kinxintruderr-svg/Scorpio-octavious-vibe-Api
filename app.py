
import os
import sqlite3
import hashlib
import hmac
import re
import secrets
import json
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Flask, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

============================================================

SCORPIO OCTAVIOUS VIBE API

Monetization + Wallet Foundation

============================================================

app = Flask(name)

============================================================

CONFIGURATION

============================================================

JWT_SECRET = os.environ.get("JWT_SECRET")

if not JWT_SECRET:
JWT_SECRET = "CHANGE_THIS_IN_RENDER"

TAPJOY_SECRET = os.environ.get("TAPJOY_SECRET", "")

TAPJOY_APP_ID = os.environ.get(
"TAPJOY_APP_ID",
"20c83360-1d38-4acc-bdeb-356931d020af"
)

TAPJOY_PLACEMENT_ID = os.environ.get(
"TAPJOY_PLACEMENT_ID",
"e9924a33-8737-44fd-8ba5-22db9dcddc54"
)

DB_PATH = os.environ.get("DB_PATH", "scorpio.db")

SOV_ASSET = "SOV"
FEE_PERCENT = 10

MIN_WITHDRAWAL_CENTS = int(
os.environ.get("MIN_WITHDRAWAL_CENTS", "100")
)

MAX_WITHDRAWAL_CENTS = int(
os.environ.get("MAX_WITHDRAWAL_CENTS", "1000000")
)

app.config["SECRET_KEY"] = JWT_SECRET
app.config["JSON_SORT_KEYS"] = False

============================================================

DATABASE

============================================================

def db():
if "db" not in g:
g.db = sqlite3.connect(
DB_PATH,
timeout=30,
check_same_thread=False
)

g.db.row_factory = sqlite3.Row  
    g.db.execute("PRAGMA foreign_keys = ON")  
    g.db.execute("PRAGMA journal_mode = WAL")  

return g.db

@app.teardown_appcontext
def close_db(exc=None):
connection = g.pop("db", None)

if connection is not None:  
    connection.close()

def now_iso():
return datetime.now(timezone.utc).isoformat()

def init_db():

connection = db()  

connection.executescript(  
    """  
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
        sov REAL NOT NULL DEFAULT 0,  
        btc REAL NOT NULL DEFAULT 0,  
        eth REAL NOT NULL DEFAULT 0,  
        usdt REAL NOT NULL DEFAULT 0,  
        updated_at TEXT NOT NULL,  
        FOREIGN KEY(user_id)  
            REFERENCES users(id)  
            ON DELETE CASCADE  
    );  

    CREATE TABLE IF NOT EXISTS posts(  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        user_id INTEGER NOT NULL,  
        media_url TEXT NOT NULL,  
        media_type TEXT NOT NULL,  
        caption TEXT DEFAULT '',  
        created_at TEXT NOT NULL,  
        FOREIGN KEY(user_id)  
            REFERENCES users(id)  
            ON DELETE CASCADE  
    );  

    CREATE TABLE IF NOT EXISTS reels(  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        user_id INTEGER NOT NULL,  
        video_url TEXT NOT NULL,  
        caption TEXT DEFAULT '',  
        views INTEGER NOT NULL DEFAULT 0,  
        created_at TEXT NOT NULL,  
        FOREIGN KEY(user_id)  
            REFERENCES users(id)  
            ON DELETE CASCADE  
    );  

    CREATE TABLE IF NOT EXISTS likes(  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        user_id INTEGER NOT NULL,  
        post_id INTEGER,  
        reel_id INTEGER,  
        created_at TEXT NOT NULL,  
        FOREIGN KEY(user_id)  
            REFERENCES users(id)  
            ON DELETE CASCADE  
    );  

    CREATE TABLE IF NOT EXISTS comments(  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        user_id INTEGER NOT NULL,  
        post_id INTEGER,  
        reel_id INTEGER,  
        body TEXT NOT NULL,  
        created_at TEXT NOT NULL,  
        FOREIGN KEY(user_id)  
            REFERENCES users(id)  
            ON DELETE CASCADE  
    );  

    CREATE TABLE IF NOT EXISTS transactions(  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        user_id INTEGER NOT NULL,  
        type TEXT NOT NULL,  
        asset TEXT NOT NULL,  
        amount REAL NOT NULL,  
        fee REAL NOT NULL DEFAULT 0,  
        net_amount REAL NOT NULL DEFAULT 0,  
        status TEXT NOT NULL,  
        reference TEXT,  
        description TEXT,  
        created_at TEXT NOT NULL,  
        FOREIGN KEY(user_id)  
            REFERENCES users(id)  
            ON DELETE CASCADE  
    );  

    CREATE TABLE IF NOT EXISTS payout_requests(  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        user_id INTEGER NOT NULL,  
        method TEXT NOT NULL,  
        destination TEXT NOT NULL,  
        amount_cents INTEGER NOT NULL,  
        fee_cents INTEGER NOT NULL DEFAULT 0,  
        net_amount_cents INTEGER NOT NULL DEFAULT 0,  
        status TEXT NOT NULL DEFAULT 'pending',  
        created_at TEXT NOT NULL,  
        updated_at TEXT,  
        FOREIGN KEY(user_id)  
            REFERENCES users(id)  
            ON DELETE CASCADE  
    );  

    CREATE TABLE IF NOT EXISTS tapjoy_rewards(  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        tapjoy_id TEXT UNIQUE NOT NULL,  
        user_id TEXT NOT NULL,  
        currency REAL NOT NULL,  
        verifier TEXT,  
        raw_reference TEXT,  
        created_at TEXT NOT NULL  
    );  

    CREATE TABLE IF NOT EXISTS offerwall_events(  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        provider TEXT NOT NULL,  
        event_id TEXT,  
        user_id TEXT,  
        amount REAL NOT NULL DEFAULT 0,  
        status TEXT NOT NULL DEFAULT 'received',  
        payload TEXT,  
        created_at TEXT NOT NULL  
    );  

    CREATE TABLE IF NOT EXISTS admin_fees(  
        id INTEGER PRIMARY KEY AUTOINCREMENT,  
        user_id INTEGER NOT NULL,  
        source TEXT NOT NULL,  
        amount REAL NOT NULL,  
        asset TEXT NOT NULL,  
        reference TEXT,  
        created_at TEXT NOT NULL  
    );  

    CREATE INDEX IF NOT EXISTS idx_transactions_user  
    ON transactions(user_id);  

    CREATE INDEX IF NOT EXISTS idx_transactions_created  
    ON transactions(created_at);  

    CREATE INDEX IF NOT EXISTS idx_payout_user  
    ON payout_requests(user_id);  

    CREATE INDEX IF NOT EXISTS idx_tapjoy_user  
    ON tapjoy_rewards(user_id);  

    CREATE INDEX IF NOT EXISTS idx_offerwall_provider  
    ON offerwall_events(provider);  

    CREATE INDEX IF NOT EXISTS idx_posts_created  
    ON posts(created_at);  

    CREATE INDEX IF NOT EXISTS idx_reels_created  
    ON reels(created_at);  
    """  
)  

# ========================================================  
# SAFE MIGRATIONS  
# ========================================================  

wallet_columns = {  
    row["name"]  
    for row in connection.execute(  
        "PRAGMA table_info(wallets)"  
    ).fetchall()  
}  

if "sov" not in wallet_columns:  
    connection.execute(  
        "ALTER TABLE wallets ADD COLUMN sov REAL NOT NULL DEFAULT 0"  
    )  

if "updated_at" not in wallet_columns:  
    connection.execute(  
        "ALTER TABLE wallets ADD COLUMN updated_at TEXT"  
    )  

    connection.execute(  
        "UPDATE wallets SET updated_at=? "  
        "WHERE updated_at IS NULL",  
        (now_iso(),)  
    )  

transaction_columns = {  
    row["name"]  
    for row in connection.execute(  
        "PRAGMA table_info(transactions)"  
    ).fetchall()  
}  

if "fee" not in transaction_columns:  
    connection.execute(  
        "ALTER TABLE transactions "  
        "ADD COLUMN fee REAL NOT NULL DEFAULT 0"  
    )  

if "net_amount" not in transaction_columns:  
    connection.execute(  
        "ALTER TABLE transactions "  
        "ADD COLUMN net_amount REAL NOT NULL DEFAULT 0"  
    )  

if "description" not in transaction_columns:  
    connection.execute(  
        "ALTER TABLE transactions "  
        "ADD COLUMN description TEXT"  
    )  

payout_columns = {  
    row["name"]  
    for row in connection.execute(  
        "PRAGMA table_info(payout_requests)"  
    ).fetchall()  
}  

if "fee_cents" not in payout_columns:  
    connection.execute(  
        "ALTER TABLE payout_requests "  
        "ADD COLUMN fee_cents INTEGER NOT NULL DEFAULT 0"  
    )  

if "net_amount_cents" not in payout_columns:  
    connection.execute(  
        "ALTER TABLE payout_requests "  
        "ADD COLUMN net_amount_cents INTEGER NOT NULL DEFAULT 0"  
    )  

if "updated_at" not in payout_columns:  
    connection.execute(  
        "ALTER TABLE payout_requests "  
        "ADD COLUMN updated_at TEXT"  
    )  

connection.commit()

============================================================

AUTHENTICATION

============================================================

def token_for(user):

payload = {  
    "sub": int(user["id"]),  
    "role": user["role"],  
    "iat": datetime.now(timezone.utc),  
    "exp": datetime.now(timezone.utc)  
    + timedelta(days=7)  
}  

return jwt.encode(  
    payload,  
    app.config["SECRET_KEY"],  
    algorithm="HS256"  
)

def auth_required(fn):

@wraps(fn)  
def wrapper(*args, **kwargs):  

    header = request.headers.get(  
        "Authorization",  
        ""  
    )  

    if not header.startswith("Bearer "):  
        return jsonify(  
            error="Authentication required"  
        ), 401  

    token = header[7:].strip()  

    try:  

        payload = jwt.decode(  
            token,  
            app.config["SECRET_KEY"],  
            algorithms=["HS256"]  
        )  

        user_id = int(payload["sub"])  

    except Exception:  

        return jsonify(  
            error="Invalid or expired token"  
        ), 401  

    user = db().execute(  
        """  
        SELECT *  
        FROM users  
        WHERE id=?  
        """,  
        (user_id,)  
    ).fetchone()  

    if not user:  
        return jsonify(  
            error="User not found"  
        ), 401  

    g.user = user  

    return fn(*args, **kwargs)  

return wrapper

def admin_required(fn):

@wraps(fn)  
@auth_required  
def wrapper(*args, **kwargs):  

    if g.user["role"] != "admin":  
        return jsonify(  
            error="Admin only"  
        ), 403  

    return fn(*args, **kwargs)  

return wrapper

============================================================

HELPERS

============================================================

EMAIL_REGEX = re.compile(
r"^[^@\s]+@[^@\s]+.[^@\s]+$"
)

def valid_email(email):
return bool(EMAIL_REGEX.match(email))

def json_body():

data = request.get_json(silent=True)  

if not isinstance(data, dict):  
    return {}  

return data

def safe_float(value, default=0):

try:  
    return float(value)  
except (TypeError, ValueError):  
    return default

def make_reference(prefix="SOV"):

return (  
    f"{prefix}_"  
    f"{secrets.token_hex(12)}"  
)

============================================================

HEALTH

============================================================

@app.get("/")
def index():

return jsonify(  
    service="Scorpio Octavious Vibe API",  
    status="online",  
    version="3.0.0",  
    monetization=True  
)

@app.get("/api/health")
def health():

try:  

    db().execute(  
        "SELECT 1"  
    ).fetchone()  

    return jsonify(  
        ok=True,  
        service="Scorpio Octavious Vibe backend",  
        database="connected",  
        monetization=True,  
        tapjoy_configured=bool(TAPJOY_SECRET)  
    )  

except Exception as exc:  

    return jsonify(  
        ok=False,  
        database="error",  
        error=str(exc)  
    ), 500

============================================================

AUTH - REGISTER

============================================================

@app.post("/api/auth/register")
def register():

data = json_body()  

name = str(  
    data.get("name") or ""  
).strip()  

email = str(  
    data.get("email") or ""  
).strip().lower()  

password = str(  
    data.get("password") or ""  
)  

if not name:  
    return jsonify(  
        error="Name is required"  
    ), 400  

if not valid_email(email):  
    return jsonify(  
        error="Valid email is required"  
    ), 400  

if len(password) < 8:  
    return jsonify(  
        error="Password must contain at least 8 characters"  
    ), 400  

connection = db()  

try:  

    cursor = connection.execute(  
        """  
        INSERT INTO users(  
            name,  
            email,  
            password_hash,  
            created_at  
        )  
        VALUES(?,?,?,?)  
        """,  
        (  
            name,  
            email,  
            generate_password_hash(password),  
            now_iso()  
        )  
    )  

    user_id = cursor.lastrowid  

    connection.execute(  
        """  
        INSERT INTO wallets(  
            user_id,  
            updated_at  
        )  
        VALUES(?,?)  
        """,  
        (  
            user_id,  
            now_iso()  
        )  
    )  

    connection.commit()  

except sqlite3.IntegrityError:  

    connection.rollback()  

    return jsonify(  
        error="Email already registered"  
    ), 409  

user = connection.execute(  
    """  
    SELECT *  
    FROM users  
    WHERE id=?  
    """,  
    (user_id,)  
).fetchone()  

return jsonify(  
    ok=True,  
    token=token_for(user),  
    user={  
        "id": user_id,  
        "name": name,  
        "email": email,  
        "role": user["role"]  
    }  
), 201

============================================================

AUTH - LOGIN

============================================================

@app.post("/api/auth/login")
def login():

data = json_body()  

email = str(  
    data.get("email") or ""  
).strip().lower()  

password = str(  
    data.get("password") or ""  
)  

user = db().execute(  
    """  
    SELECT *  
    FROM users  
    WHERE email=?  
    """,  
    (email,)  
).fetchone()  

if (  
    not user  
    or not user["password_hash"]  
    or not check_password_hash(  
        user["password_hash"],  
        password  
    )  
):  

    return jsonify(  
        error="Invalid email or password"  
    ), 401  

return jsonify(  
    ok=True,  
    token=token_for(user),  
    user={  
        "id": user["id"],  
        "name": user["name"],  
        "email": user["email"],  
        "role": user["role"]  
    }  
)

@app.post("/api/auth/google")
def google():

return jsonify(  
    error="Google OAuth backend is not configured yet"  
), 501

============================================================

USER

============================================================

@app.get("/api/me")
@auth_required
def me():

user = g.user  

return jsonify(  
    id=user["id"],  
    name=user["name"],  
    email=user["email"],  
    role=user["role"],  
    created_at=user["created_at"]  
)

============================================================

WALLET

============================================================

@app.get("/api/wallet")
@auth_required
def wallet():

wallet_row = db().execute(  
    """  
    SELECT *  
    FROM wallets  
    WHERE user_id=?  
    """,  
    (g.user["id"],)  
).fetchone()  

if not wallet_row:  
    return jsonify(  
        error="Wallet not found"  
    ), 404  

return jsonify(  
    user_id=g.user["id"],  
    sov=float(wallet_row["sov"]),  
    usd=f"{wallet_row['usd_cents'] / 100:.2f}",  
    btc=float(wallet_row["btc"]),  
    eth=float(wallet_row["eth"]),  
    usdt=float(wallet_row["usdt"]),  
    updated_at=wallet_row["updated_at"]  
)

============================================================

CREDIT SOV REWARD

============================================================

def credit_sov_reward(
user_id,
amount,
reference,
description="Reward"
):

amount = float(amount)  

if amount <= 0:  
    raise ValueError(  
        "Reward amount must be positive"  
    )  

connection = db()  

wallet = connection.execute(  
    """  
    SELECT *  
    FROM wallets  
    WHERE user_id=?  
    """,  
    (user_id,)  
).fetchone()  

if not wallet:  
    raise ValueError(  
        "Wallet not found"  
    )  

connection.execute(  
    """  
    UPDATE wallets  
    SET sov=sov+?,  
        updated_at=?  
    WHERE user_id=?  
    """,  
    (  
        amount,  
        now_iso(),  
        user_id  
    )  
)  

connection.execute(  
    """  
    INSERT INTO transactions(  
        user_id,  
        type,  
        asset,  
        amount,  
        fee,  
        net_amount,  
        status,  
        reference,  
        description,  
        created_at  
    )  
    VALUES(?,?,?,?,?,?,?,?,?,?)  
    """,  
    (  
        user_id,  
        "reward",  
        SOV_ASSET,  
        amount,  
        0,  
        amount,  
        "completed",  
        reference,  
        description,  
        now_iso()  
    )  
)  

connection.commit()

============================================================

TAPJOY VERIFICATION

============================================================

def tapjoy_verify(
tapjoy_id,
snuid,
currency,
verifier
):

if not TAPJOY_SECRET:  
    return False  

message = (  
    f"{tapjoy_id}:"  
    f"{snuid}:"  
    f"{currency}:"  
    f"{TAPJOY_SECRET}"  
)  

expected = hashlib.md5(  
    message.encode("utf-8")  
).hexdigest()  

return hmac.compare_digest(  
    expected.lower(),  
    str(verifier).lower()  
)

============================================================

TAPJOY CALLBACK

============================================================

@app.route(
"/api/tapjoy/callback",
methods=["GET", "POST"]
)
def tapjoy_callback():

# --------------------------------------------------------  
# Accept GET query parameters.  
# --------------------------------------------------------  

if request.method == "GET":  

    data = request.args.to_dict()  

else:  

    data = {}  

    if request.form:  
        data.update(request.form.to_dict())  

    json_data = request.get_json(  
        silent=True  
    )  

    if isinstance(json_data, dict):  
        data.update(json_data)  

tapjoy_id = str(  
    data.get("id")  
    or data.get("tapjoy_id")  
    or ""  
).strip()  

snuid = str(  
    data.get("snuid")  
    or data.get("user_id")  
    or ""  
).strip()  

currency_raw = (  
    data.get("currency")  
    or data.get("amount")  
    or "0"  
)  

verifier = str(  
    data.get("verifier")  
    or ""  
).strip()  

if not tapjoy_id:  
    return jsonify(  
        error="Missing Tapjoy transaction ID"  
    ), 400  

if not snuid:  
    return jsonify(  
        error="Missing user ID"  
    ), 400  

try:  
    currency = float(currency_raw)  
except (TypeError, ValueError):  
    return jsonify(  
        error="Invalid currency amount"  
    ), 400  

if currency <= 0:  
    return jsonify(  
        error="Invalid reward amount"  
    ), 400  

if not verifier:  
    return jsonify(  
        error="Missing verifier"  
    ), 400  

# --------------------------------------------------------  
# Verify Tapjoy signature.  
# --------------------------------------------------------  

if not tapjoy_verify(  
    tapjoy_id,  
    snuid,  
    currency_raw,  
    verifier  
):  

    return jsonify(  
        error="Invalid Tapjoy verifier"  
    ), 403  

connection = db()  

# --------------------------------------------------------  
# DUPLICATE PROTECTION  
# --------------------------------------------------------  

existing = connection.execute(  
        """  
        SELECT id  
        FROM tapjoy_rewards  
        WHERE tapjoy_id=?  
        """,  
        (tapjoy_id,)  
    ).fetchone()  
  
    if existing:  
  
        return jsonify(  
            ok=True,  
            duplicate=True,  
            message="Reward already processed"  
        ), 200  
  
    # --------------------------------------------------------  
    # Find SOV user.  
    #  
    # snuid should contain the SOV account/user ID.  
    # --------------------------------------------------------  
  
    user = None  
  
    if snuid.isdigit():  
  
        user = connection.execute(  
            """  
            SELECT *  
            FROM users  
            WHERE id=?  
            """,  
            (int(snuid),)  
        ).fetchone()  
  
    if not user:  
  
        user = connection.execute(  
            """  
            SELECT *  
            FROM users  
            WHERE email=?  
            """,  
            (snuid.lower(),)  
        ).fetchone()  
  
    if not user:  
  
        return jsonify(  
            error="SOV user not found"  
        ), 404  
  
    # --------------------------------------------------------  
    # Store callback first.  
    # UNIQUE tapjoy_id protects against duplicate callbacks.  
    # --------------------------------------------------------  
  
    try:  
  
        connection.execute(  
            """  
            INSERT INTO tapjoy_rewards(  
                tapjoy_id,  
                user_id,  
                currency,  
                verifier,  
                raw_reference,  
                created_at  
            )  
            VALUES(?,?,?,?,?,?)  
            """,  
            (  
                tapjoy_id,  
                str(user["id"]),  
                currency,  
                verifier,  
                json.dumps(data),  
                now_iso()  
            )  
        )  
  
        # ----------------------------------------------------  
        # Credit full Tapjoy reward.  
        # NO 10% fee here.  
        # ----------------------------------------------------  
  
        connection.execute(  
            """  
            UPDATE wallets  
            SET sov=sov+?,  
                updated_at=?  
            WHERE user_id=?  
            """,  
            (  
                currency,  
                now_iso(),  
                user["id"]  
            )  
        )  
  
        reference = (  
            f"TAPJOY_{tapjoy_id}"  
        )  
  
        connection.execute(  
            """  
            INSERT INTO transactions(  
                user_id,  
                type,  
                asset,  
                amount,  
                fee,  
                net_amount,  
                status,  
                reference,  
                description,  
                created_at  
            )  
            VALUES(?,?,?,?,?,?,?,?,?,?)  
            """,  
            (  
                user["id"],  
                "reward",  
                SOV_ASSET,  
                currency,  
                0,  
                currency,  
                "completed",  
                reference,  
                "Tapjoy reward",  
                now_iso()  
            )  
        )  
  
        connection.execute(  
            """  
            INSERT INTO offerwall_events(  
                provider,  
                event_id,  
                user_id,  
                amount,  
                status,  
                payload,  
                created_at  
            )  
            VALUES(?,?,?,?,?,?,?)  
            """,  
            (  
                "tapjoy",  
                tapjoy_id,  
                str(user["id"]),  
                currency,  
                "credited",  
                json.dumps(data),  
                now_iso()  
            )  
        )  
  
        connection.commit()  
  
    except sqlite3.IntegrityError:  
  
        connection.rollback()  
  
        return jsonify(  
            ok=True,  
            duplicate=True,  
            message="Reward already processed"  
        ), 200  
  
    except Exception as exc:  
  
        connection.rollback()  
  
        return jsonify(  
            error="Reward processing failed",  
            details=str(exc)  
        ), 500  
  
    return jsonify(  
        ok=True,  
        rewarded=True,  
        provider="tapjoy",  
        transaction_id=tapjoy_id,  
        user_id=user["id"],  
        asset=SOV_ASSET,  
        amount=currency,  
        fee=0,  
        status="credited"  
    ), 200  
  
  
# ============================================================  
# REWARD HISTORY  
# ============================================================  
  
@app.get("/api/rewards")  
@auth_required  
def rewards():  
  
    rows = db().execute(  
        """  
        SELECT *  
        FROM transactions  
        WHERE user_id=?  
        AND type='reward'  
        ORDER BY id DESC  
        LIMIT 200  
        """,  
        (g.user["id"],)  
    ).fetchall()  
  
    return jsonify(  
        rewards=[  
            dict(row)  
            for row in rows  
        ]  
    )  
  
  
# ============================================================  
# SOV TRANSFER  
# ============================================================  
  
@app.post("/api/wallet/send")  
@auth_required  
def send_sov():  
  
    data = json_body()  
  
    recipient_value = str(  
        data.get("recipient")  
        or data.get("user_id")  
        or data.get("email")  
        or ""  
    ).strip()  
  
    amount = safe_float(  
        data.get("amount"),  
        0  
    )  
  
    if amount <= 0:  
        return jsonify(  
            error="Amount must be greater than zero"  
        ), 400  
  
    if not recipient_value:  
        return jsonify(  
            error="Recipient is required"  
        ), 400  
  
    connection = db()  
  
    # --------------------------------------------------------  
    # Find recipient  
    # --------------------------------------------------------  
  
    recipient = None  
  
    if recipient_value.isdigit():  
  
        recipient = connection.execute(  
            """  
            SELECT *  
            FROM users  
            WHERE id=?  
            """,  
            (int(recipient_value),)  
        ).fetchone()  
  
    if not recipient:  
  
        recipient = connection.execute(  
            """  
            SELECT *  
            FROM users  
            WHERE email=?  
            """,  
            (recipient_value.lower(),)  
        ).fetchone()  
  
    if not recipient:  
  
        return jsonify(  
            error="Recipient not found"  
        ), 404  
  
    if recipient["id"] == g.user["id"]:  
  
        return jsonify(  
            error="Cannot send to yourself"  
        ), 400  
  
    fee = amount * (  
        FEE_PERCENT / 100  
    )  
  
    total = amount + fee  
  
    # --------------------------------------------------------  
    # Atomic wallet update  
    # --------------------------------------------------------  
  
    try:  
  
        connection.execute(  
            "BEGIN IMMEDIATE"  
        )  
  
        sender_wallet = connection.execute(  
            """  
            SELECT sov  
            FROM wallets  
            WHERE user_id=?  
            """,  
            (g.user["id"],)  
        ).fetchone()  
  
        if not sender_wallet:  
  
            connection.rollback()  
  
            return jsonify(  
                error="Sender wallet not found"  
            ), 404  
  
        if float(sender_wallet["sov"]) < total:  
  
            connection.rollback()  
  
            return jsonify(  
                error="Insufficient SOV balance",  
                required=total,  
                balance=float(sender_wallet["sov"])  
            ), 400  
  
        connection.execute(  
            """  
            UPDATE wallets  
            SET sov=sov-?,  
                updated_at=?  
            WHERE user_id=?  
            """,  
            (  
                total,  
                now_iso(),  
                g.user["id"]  
            )  
        )  
  
        connection.execute(  
            """  
            UPDATE wallets  
            SET sov=sov+?,  
                updated_at=?  
            WHERE user_id=?  
            """,  
            (  
                amount,  
                now_iso(),  
                recipient["id"]  
            )  
        )  
  
        reference = make_reference(  
            "SEND"  
        )  
  
        connection.execute(  
            """  
            INSERT INTO transactions(  
                user_id,  
                type,  
                asset,  
                amount,  
                fee,  
                net_amount,  
                status,  
                reference,  
                description,  
                created_at  
            )  
            VALUES(?,?,?,?,?,?,?,?,?,?)  
            """,  
            (  
                g.user["id"],  
                "send",  
                SOV_ASSET,  
                amount,  
                fee,  
                amount,  
                "completed",  
                reference,  
                f"Sent to user {recipient['id']}",  
                now_iso()  
            )  
        )  
  
        connection.execute(  
            """  
            INSERT INTO transactions(  
                user_id,  
                type,  
                asset,  
                amount,  
                fee,  
                net_amount,  
                status,  
                reference,  
                description,  
                created_at  
            )  
            VALUES(?,?,?,?,?,?,?,?,?,?)  
            """,  
            (  
                recipient["id"],  
                "receive",  
                SOV_ASSET,  
                amount,  
                0,  
                amount,  
                "completed",  
                reference,  
                f"Received from user {g.user['id']}",  
                now_iso()  
            )  
        )  
  
        # ----------------------------------------------------  
        # Admin receives 10% fee.  
        # ----------------------------------------------------  
  
        connection.execute(  
            """  
            INSERT INTO admin_fees(  
                user_id,  
                source,  
                amount,  
                asset,  
                reference,  
                created_at  
            )  
            VALUES(?,?,?,?,?,?)  
            """,  
            (  
                g.user["id"],  
                "sov_transfer",  
                fee,  
                SOV_ASSET,  
                reference,  
                now_iso()  
            )  
        )  
  
        connection.commit()  
  
    except Exception as exc:  
  
        connection.rollback()  
  
        return jsonify(  
            error="Transfer failed",  
            details=str(exc)  
        ), 500  
  
    return jsonify(  
        ok=True,  
        reference=reference,  
        asset=SOV_ASSET,  
        amount=amount,  
        fee=fee,  
        total_debited=total,  
        recipient_id=recipient["id"],  
        status="completed"  
    )  
  
  
# ============================================================  
# TRANSACTION HISTORY  
# ============================================================  
  
@app.get("/api/wallet/history")  
@auth_required  
def wallet_history():  
  
    rows = db().execute(  
        """  
        SELECT *  
        FROM transactions  
        WHERE user_id=?  
        ORDER BY id DESC  
        LIMIT 200  
        """,  
        (g.user["id"],)  
    ).fetchall()  
  
    return jsonify(  
        transactions=[  
            dict(row)  
            for row in rows  
        ]  
    )  
  
  
# ============================================================  
# WITHDRAWAL REQUEST  
# ============================================================  
  
@app.post("/api/wallet/withdraw")  
@auth_required  
def withdrawal():  
  
    data = json_body()  
  
    amount = safe_float(  
        data.get("amount"),  
        0  
    )  
  
    method = str(  
        data.get("method")  
        or data.get("asset")  
        or ""  
    ).strip()  
  
    destination = str(  
        data.get("destination")  
        or data.get("address")  
        or ""  
    ).strip()  
  
    if amount <= 0:  
  
        return jsonify(  
            error="Invalid withdrawal amount"  
        ), 400  
  
    if not method:  
  
        return jsonify(  
            error="Withdrawal method is required"  
        ), 400  
  
    if not destination:  
  
        return jsonify(  
            error="Destination is required"  
        ), 400  
  
    # --------------------------------------------------------  
    # SOV withdrawal is represented as a decimal amount.  
    # We use 6 decimal places internally for validation.  
    # --------------------------------------------------------  
  
    if amount < 0.000001:  
  
        return jsonify(  
            error="Withdrawal amount too small"  
        ), 400  
  
    connection = db()  
  
    try:  
  
        connection.execute(  
            "BEGIN IMMEDIATE"  
        )  
  
        wallet = connection.execute(  
            """  
            SELECT sov  
            FROM wallets  
            WHERE user_id=?  
            """,  
            (g.user["id"],)  
        ).fetchone()  
  
        if not wallet:  
  
            connection.rollback()  
  
            return jsonify(  
                error="Wallet not found"  
            ), 404  
  
        balance = float(  
            wallet["sov"]  
        )  
  
        fee = amount * (  
            FEE_PERCENT / 100  
        )  
  
        total = amount + fee  
  
        if balance < total:  
  
            connection.rollback()  
  
            return jsonify(  
                error="Insufficient SOV balance",  
                balance=balance,  
                requested=amount,  
                fee=fee,  
                total_required=total  
            ), 400  
  
        # ----------------------------------------------------  
        # Reserve the complete withdrawal + fee.  
        # ----------------------------------------------------  
  
        connection.execute(  
            """  
            UPDATE wallets  
            SET sov=sov-?,  
                updated_at=?  
            WHERE user_id=?  
            """,  
            (  
                total,  
                now_iso(),  
                g.user["id"]  
            )  
        )  
  
        amount_cents = int(  
            round(amount * 100)  
        )  
  
        fee_cents = int(  
            round(fee * 100)  
        )  
  
        net_cents = int(  
            round(amount * 100)  
        )  
  
        reference = make_reference(  
            "WD"  
        )  
  
        cursor = connection.execute(  
            """  
            INSERT INTO payout_requests(  
                user_id,  
                method,  
                destination,  
                amount_cents,  
                fee_cents,  
                net_amount_cents,  
                status,  
                created_at,  
                updated_at  
            )  
            VALUES(?,?,?,?,?,?,?,?,?)  
            """,  
            (  
                g.user["id"],  
                method,  
                destination,  
                amount_cents,  
                fee_cents,  
                net_cents,  
                "pending",  
                now_iso(),  
                now_iso()  
            )  
        )  
  
        payout_id = cursor.lastrowid  
  
        connection.execute(  
            """  
            INSERT INTO transactions(  
                user_id,  
                type,  
                asset,  
                amount,  
                fee,  
                net_amount,  
                status,  
                reference,  
                description,  
                created_at  
            )  
            VALUES(?,?,?,?,?,?,?,?,?,?)  
            """,  
            (  
                g.user["id"],  
                "withdrawal",  
                SOV_ASSET,  
                amount,  
                fee,  
                amount,  
                "pending",  
                reference,  
                f"Withdrawal request #{payout_id}",  
                now_iso()  
            )  
        )  
  
        connection.execute(  
            """  
            INSERT INTO admin_fees(  
                user_id,  
                source,  
                amount,  
                asset,  
                reference,  
                created_at  
            )  
            VALUES(?,?,?,?,?,?)  
            """,  
            (  
                g.user["id"],  
                "withdrawal",  
                fee,  
                SOV_ASSET,  
                reference,  
                now_iso()  
            )  
        )  
  
        connection.commit()  
  
    except Exception as exc:  
  
        connection.rollback()  
  
        return jsonify(  
            error="Withdrawal request failed",  
            details=str(exc)  
        ), 500  
  
    return jsonify(  
        ok=True,  
        payout_id=payout_id,  
        reference=reference,  
        asset=SOV_ASSET,  
        requested_amount=amount,  
        fee=fee,  
        net_amount=amount,  
        total_reserved=total,  
        status="pending"  
    ), 201  
  
  
# ============================================================  
# USER WITHDRAWAL HISTORY  
# ============================================================  
  
@app.get("/api/wallet/withdrawals")  
@auth_required  
def withdrawal_history():  
  
    rows = db().execute(  
        """  
        SELECT  
            id,  
            method,  
            destination,  
            amount_cents,  
            fee_cents,  
            net_amount_cents,  
            status,  
            created_at,  
            updated_at  
        FROM payout_requests  
        WHERE user_id=?  
        ORDER BY id DESC  
        LIMIT 100  
        """,  
        (g.user["id"],)  
    ).fetchall()  
  
    return jsonify(  
        withdrawals=[  
            dict(row)  
            for row in rows  
        ]  
    )  
  
  
# ============================================================  
# POSTS  
# ============================================================  
  
@app.post("/api/posts")  
@auth_required  
def create_post():  
  
    data = json_body()  
  
    media_url = str(  
        data.get("media_url")  
        or ""  
    ).strip()  
  
    media_type = str(  
        data.get("media_type")  
        or "image"  
    ).strip()  
  
    caption = str(  
        data.get("caption")  
        or ""  
    )  
  
    if not media_url:  
  
        return jsonify(  
            error="media_url is required"  
        ), 400  
  
    connection = db()  
  
    cursor = connection.execute(  
        """  
        INSERT INTO posts(  
            user_id,  
            media_url,  
            media_type,  
            caption,  
            created_at  
        )  
        VALUES(?,?,?,?,?)  
        """,  
        (  
            g.user["id"],  
            media_url,  
            media_type,  
            caption,  
            now_iso()  
        )  
    )  
  
    connection.commit()  
  
    return jsonify(  
        ok=True,  
        post_id=cursor.lastrowid  
    ), 201  
  
  
@app.get("/api/posts")  
def posts():  
  
    rows = db().execute(  
        """  
        SELECT  
            p.*,  
            u.name AS user_name  
        FROM posts p  
        JOIN users u  
        ON u.id=p.user_id  
        ORDER BY p.id DESC  
        LIMIT 100  
        """  
    ).fetchall()  
  
    return jsonify(  
        posts=[  
            dict(row)  
            for row in rows  
        ]  
    )  
  
  
# ============================================================  
# REELS  
# ============================================================  
  
@app.post("/api/reels")  
@auth_required  
def create_reel():  
  
    data = json_body()  
  
    video_url = str(  
        data.get("video_url")  
        or ""  
    ).strip()  
  
    caption = str(  
        data.get("caption")  
        or ""  
    )  
  
    if not video_url:  
  
        return jsonify(  
            error="video_url is required"  
        ), 400  
  
    connection = db()  
  
    cursor = connection.execute(  
        """  
        INSERT INTO reels(  
            user_id,  
            video_url,  
            caption,  
            created_at  
        )  
        VALUES(?,?,?,?)  
        """,  
        (  
            g.user["id"],  
            video_url,  
            caption,  
            now_iso()  
        )  
    )  
  
    connection.commit()  
  
    return jsonify(  
        ok=True,  
        reel_id=cursor.lastrowid  
    ), 201  
  
  
@app.get("/api/reels")  
def reels():  
  
    rows = db().execute(  
        """  
        SELECT  
            r.*,  
            u.name AS user_name  
        FROM reels r  
        JOIN users u  
        ON u.id=r.user_id  
        ORDER BY r.id DESC  
        LIMIT 100  
        """  
    ).fetchall()  
  
    return jsonify(  
        reels=[  
            dict(row)  
            for row in rows  
        ]  
    )  
  
  
@app.post("/api/reels/<int:reel_id>/view")  
def reel_view(reel_id):  
  
    connection = db()  
  
    reel = connection.execute(  
        """  
        SELECT id  
        FROM reels  
        WHERE id=?  
        """,  
        (reel_id,)  
    ).fetchone()  
  
    if not reel:  
  
        return jsonify(  
            error="Reel not found"  
        ), 404  
  
    connection.execute(  
        """  
        UPDATE reels  
        SET views=views+1  
        WHERE id=?  
        """,  
        (reel_id,)  
    )  
  
    connection.commit()  
  
    return jsonify(  
        ok=True  
    )  
  
  
# ============================================================  
# LIKES  
# ============================================================  
  
@app.post("/api/posts/<int:post_id>/like")  
@auth_required  
def like_post(post_id):  
  
    connection = db()  
  
    post = connection.execute(  
        """  
        SELECT id  
        FROM posts  
        WHERE id=?  
        """,  
        (post_id,)  
    ).fetchone()  
  
    if not post:  
  
        return jsonify(  
            error="Post not found"  
        ), 404  
  
    existing = connection.execute(  
        """  
        SELECT id  
        FROM likes  
        WHERE user_id=?  
        AND post_id=?  
        """,  
        (  
            g.user["id"],  
            post_id  
        )  
    ).fetchone()  
  
    if existing:  
  
        return jsonify(  
            ok=True,  
            liked=True,  
            already_liked=True  
        )  
  
    connection.execute(  
        """  
        INSERT INTO likes(  
            user_id,  
            post_id,  
            created_at  
        )  
        VALUES(?,?,?)  
        """,  
        (  
            g.user["id"],  
            post_id,  
            now_iso()  
        )  
    )  
  
    connection.commit()  
  
    return jsonify(  
        ok=True,  
        liked=True  
    )  
  
  
# ============================================================  
# COMMENTS  
# ============================================================  
  
@app.post("/api/posts/<int:post_id>/comments")  
@auth_required  
def comment_post(post_id):  
  
    data = json_body()  
  
    body = str(  
        data.get("body")  
        or ""  
    ).strip()  
  
    if not body:  
  
        return jsonify(  
            error="Comment cannot be empty"  
        ), 400  
  
    if len(body) > 2000:  
  
        return jsonify(  
            error="Comment is too long"  
        ), 400  
  
    connection = db()  
  
    post = connection.execute(  
        """  
        SELECT id  
        FROM posts  
        WHERE id=?  
        """,  
        (post_id,)  
    ).fetchone()  
  
    if not post:  
  
        return jsonify(  
            error="Post not found"  
        ), 404  
  
    cursor = connection.execute(  
        """  
        INSERT INTO comments(  
            user_id,  
            post_id,  
            body,  
            created_at  
        )  
        VALUES(?,?,?,?)  
        """,  
        (  
            g.user["id"],  
            post_id,  
            body,  
            now_iso()  
        )  
    )  
  
    connection.commit()  
  
    return jsonify(  
        ok=True,  
        comment_id=cursor.lastrowid  
    ), 201  
  
  
@app.get("/api/posts/<int:post_id>/comments")  
def post_comments(post_id):  
  
    rows = db().execute(  
        """  
        SELECT  
            c.id,  
            c.body,  
            c.created_at,  
            u.id AS user_id,  
            u.name AS user_name  
        FROM comments c  
        JOIN users u  
        ON u.id=c.user_id  
        WHERE c.post_id=?  
        ORDER BY c.id ASC  
        """,  
        (post_id,)  
    ).fetchall()  
  
    return jsonify(  
        comments=[  
            dict(row)  
            for row in rows  
        ]  
    )  
  
  
# ============================================================  
# OFFERWALL EVENTS  
# ============================================================  
  
@app.post("/api/offerwall/event")  
@auth_required  
def offerwall_event():  
  
    data = json_body()  
  
    provider = str(  
        data.get("provider")  
        or ""  
    ).strip()  
  
    event_id = str(  
        data.get("event_id")  
        or data.get("id")  
        or ""  
    ).strip()  
  
    amount = safe_float(  
        data.get("amount"),  
        0  
    )  
  
    if not provider:  
  
        return jsonify(  
            error="Provider is required"  
        ), 400  
  
    connection = db()  
  
    cursor = connection.execute(  
        """  
        INSERT INTO offerwall_events(  
            provider,  
            event_id,  
            user_id,  
            amount,  
            status,  
            payload,  
            created_at  
        )  
        VALUES(?,?,?,?,?,?,?)  
        """,  
        (  
            provider,  
            event_id,  
            str(g.user["id"]),  
            amount,  
            "received",  
            json.dumps(data),  
            now_iso()  
        )  
    )  
  
    connection.commit()  
  
    return jsonify(  
        ok=True,  
        event_id=cursor.lastrowid,  
        status="received"  
    ), 201  
  
  
# ============================================================  
# ADMIN - STATISTICS  
# ============================================================  
  
@app.get("/api/admin/stats")  
@admin_required  
def admin_stats():  
  
    connection = db()  
  
    users = connection.execute(  
        "SELECT COUNT(*) AS count FROM users"  
    ).fetchone()["count"]  
  
    rewards = connection.execute(  
        """  
        SELECT COALESCE(SUM(amount),0) AS total  
        FROM tapjoy_rewards  
        """  
    ).fetchone()["total"]  
  
    fees = connection.execute(  
        """  
        SELECT COALESCE(SUM(amount),0) AS total  
        FROM admin_fees  
        """  
    ).fetchone()["total"]  
  
    pending = connection.execute(  
        """  
        SELECT COUNT(*) AS count  
        FROM payout_requests  
        WHERE status='pending'  
        """  
    ).fetchone()["count"]  
  
    events = connection.execute(  
        """  
        SELECT COUNT(*) AS count  
        FROM offerwall_events  
        """  
    ).fetchone()["count"]  
  
    return jsonify(  
        users=int(users),  
        tapjoy_rewards=float(rewards),  
        admin_fees=float(fees),  
        pending_withdrawals=int(pending),  
        offerwall_events=int(events)  
    )  
  
  
# ============================================================  
# ADMIN - USERS  
# ============================================================  
  
@app.get("/api/admin/users")  
@admin_required  
def admin_users():  
  
    rows = db().execute(  
        """  
        SELECT  
            u.id,  
            u.name,  
            u.email,  
            u.role,  
            u.created_at,  
            COALESCE(w.sov,0) AS sov  
        FROM users u  
        LEFT JOIN wallets w  
        ON w.user_id=u.id  
        ORDER BY u.id DESC  
        LIMIT 500  
        """  
    ).fetchall()  
  
    return jsonify(  
        users=[  
            dict(row)  
            for row in rows  
        ]  
    )  
  
  
# ============================================================  
# ADMIN - WITHDRAWALS  
# ============================================================  
  
@app.get("/api/admin/withdrawals")  
@admin_required  
def admin_withdrawals():  
  
    rows = db().execute(  
        """  
        SELECT  
            p.*,  
            u.name AS user_name,  
            u.email  
        FROM payout_requests p  
        JOIN users u  
        ON u.id=p.user_id  
        ORDER BY p.id DESC  
        LIMIT 500  
        """  
    ).fetchall()  
  
    return jsonify(  
        withdrawals=[  
            dict(row)  
            for row in rows  
        ]  
    )  
  
  
# ============================================================  
# ADMIN - UPDATE WITHDRAWAL STATUS  
# ============================================================  
  
@app.post(  
    "/api/admin/withdrawals/<int:payout_id>/status"  
)  
@admin_required  
def update_withdrawal_status(payout_id):  
  
    data = json_body()  
  
    status = str(  
        data.get("status")  
        or ""  
    ).strip().lower()  
  
    allowed = {  
        "pending",  
        "under_review",  
        "approved",  
        "sent",  
        "completed",  
        "rejected"  
    }  
  
    if status not in allowed:  
  
        return jsonify(  
            error="Invalid status",  
            allowed=sorted(allowed)  
        ), 400  
  
    connection = db()  
  
    payout = connection.execute(  
        """  
        SELECT *  
        FROM payout_requests  
        WHERE id=?  
        """,  
        (payout_id,)  
    ).fetchone()  
  
    if not payout:  
  
        return jsonify(  
            error="Withdrawal not found"  
        ), 404  
  
    old_status = payout["status"]  
  
    # --------------------------------------------------------  
    # If rejected after funds were reserved,  
    # return requested amount + fee to wallet.  
    # --------------------------------------------------------  
  
    if (  
        status == "rejected"  
        and old_status not in {  
            "rejected",  
            "completed"  
        }  
    ):  
  
        refund = (  
            payout["amount_cents"]  
            + payout["fee_cents"]  
        ) / 100.0  
  
        try:  
  
            connection.execute(  
                "BEGIN IMMEDIATE"  
            )  
  
            connection.execute(  
                """  
                UPDATE wallets  
                SET sov=sov+?,  
                    updated_at=?  
                WHERE user_id=?  
                """,  
                (  
                    refund,  
                    now_iso(),  
                    payout["user_id"]  
                )  
            )  
  
            connection.execute(  
                """  
                UPDATE payout_requests  
                SET status=?,  
                    updated_at=?  
                WHERE id=?  
                """,  
                (  
                    status,  
                    now_iso(),  
                    payout_id  
                )  
            )  
  
            connection.execute(  
                """  
                INSERT INTO transactions(  
                    user_id,  
                    type,  
                    asset,  
                    amount,  
                    fee,  
                    net_amount,  
                    status,  
                    reference,  
                    description,  
                    created_at  
                )  
                VALUES(?,?,?,?,?,?,?,?,?,?)  
                """,  
                (  
                    payout["user_id"],  
                    "withdrawal_refund",  
                    SOV_ASSET,  
                    refund,  
                    0,  
                    refund,  
                    "completed",  
                    f"WD_REFUND_{payout_id}",  
                    "Rejected withdrawal refund",  
                    now_iso()  
                )  
            )  
  
            connection.commit()  
  
        except Exception as exc:  
  
            connection.rollback()  
  
            return jsonify(  
                error="Refund failed",  
                details=str(exc)  
            ), 500  
  
    else:  
  
        connection.execute(  
            """  
            UPDATE payout_requests  
            SET status=?,  
                updated_at=?  
            WHERE id=?  
            """,  
            (  
                status,  
                now_iso(),  
                payout_id  
            )  
        )  
  
        connection.commit()  
  
    return jsonify(  
        ok=True,  
        payout_id=payout_id,  
        old_status=old_status,  
        status=status  
    )  
  
  
# ============================================================  
# ADMIN - TRANSACTIONS  
# ============================================================  
  
@app.get("/api/admin/transactions")  
@admin_required  
def admin_transactions():  
  
    rows = db().execute(  
        """  
        SELECT  
            t.*,  
            u.name AS user_name,  
            u.email  
        FROM transactions t  
        JOIN users u  
        ON u.id=t.user_id  
        ORDER BY t.id DESC  
        LIMIT 1000  
        """  
    ).fetchall()  
  
    return jsonify(  
        transactions=[  
            dict(row)  
            for row in rows  
        ]  
    )  
  
  
# ============================================================  
# ADMIN - TAPJOY REWARDS  
# ============================================================  
  
@app.get("/api/admin/rewards")  
@admin_required  
def admin_rewards():  
  
    rows = db().execute(  
        """  
        SELECT  
            t.*,  
            u.name,  
            u.email  
        FROM tapjoy_rewards t  
        LEFT JOIN users u  
        ON CAST(t.user_id AS INTEGER)=u.id  
        ORDER BY t.id DESC  
        LIMIT 1000  
        """  
    ).fetchall()  
  
    return jsonify(  
        rewards=[  
            dict(row)  
            for row in rows  
        ]  
    )  
  
  
# ============================================================  
# ADMIN - FEES  
# ============================================================  
  
@app.get("/api/admin/fees")  
@admin_required  
def admin_fees():  
  
    rows = db().execute(  
        """  
        SELECT  
            f.*,  
            u.name,  
            u.email  
        FROM admin_fees f  
        JOIN users u  
        ON u.id=f.user_id  
        ORDER BY f.id DESC  
        LIMIT 1000  
        """  
    ).fetchall()  
  
    total = db().execute(  
        """  
        SELECT COALESCE(SUM(amount),0) AS total  
        FROM admin_fees  
        """  
    ).fetchone()["total"]  
  
    return jsonify(  
        total=float(total),  
        fees=[  
            dict(row)  
            for row in rows  
        ]  
    )  
  
  
# ============================================================  
# ADMIN - OFFERWALL EVENTS  
# ============================================================  
  
@app.get("/api/admin/offerwall/events")  
@admin_required  
def admin_offerwall_events():  
  
    rows = db().execute(  
        """  
        SELECT *  
        FROM offerwall_events  
        ORDER BY id DESC  
        LIMIT 1000  
        """  
    ).fetchall()  
  
    return jsonify(  
        events=[  
            dict(row)  
            for row in rows  
        ]  
    )  
  
  
# ============================================================  
# STARTUP  
# ============================================================  
  
with app.app_context():  
    init_db()  
  
  
if __name__ == "__main__":  
  
    port = int(  
        os.environ.get(  
            "PORT",  
            "5000"  
        )  
    )  
  
    app.run(  
        host="0.0.0.0",  
        port=port  
    )  

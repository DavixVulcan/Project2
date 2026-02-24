import sqlite3
from concurrent import futures

import grpc
from werkzeug.security import check_password_hash

import auth_pb2
import auth_pb2_grpc


DB_PATH = "users.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
      )
    """)
    conn.commit()
    conn.close()


def get_user(username: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row  # (id, username, password_hash) or None


class AuthService(auth_pb2_grpc.AuthServiceServicer):
    def CheckLogin(self, request, context):
        username = request.username.strip()
        password = request.password

        if not username or not password:
            return auth_pb2.CheckLoginResponse(ok=False, message="Missing username or password")

        row = get_user(username)
        if not row:
            return auth_pb2.CheckLoginResponse(ok=False, message="Invalid credentials")

        user_id, _, pw_hash = row
        if check_password_hash(pw_hash, password):
            return auth_pb2.CheckLoginResponse(ok=True, user_id=str(user_id), message="OK")

        return auth_pb2.CheckLoginResponse(ok=False, message="Invalid credentials")


def serve(host="0.0.0.0", port=50051):
    init_db()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthService(), server)

    server.add_insecure_port(f"{host}:{port}")  # Use TLS creds in production
    server.start()
    print(f"Auth gRPC server listening on {host}:{port}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
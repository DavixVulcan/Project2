from flask import Flask, render_template, request, redirect, url_for, session, flash
import grpc

import auth_pb2
import auth_pb2_grpc

app = Flask(__name__)
app.secret_key = "change-this"

AUTH_TARGET = "microservice-userauth:50051"


def check_login_via_grpc(username: str, password: str):
    # You can reuse the channel globally for efficiency; this is simplest.
    with grpc.insecure_channel(AUTH_TARGET) as channel:
        stub = auth_pb2_grpc.AuthServiceStub(channel)
        resp = stub.CheckLogin(auth_pb2.CheckLoginRequest(username=username, password=password))
        return resp


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/login")
def login():
    username = request.form.get("user", "")
    password = request.form.get("password", "")

    resp = check_login_via_grpc(username, password)
    if resp.ok:
        session["user"] = username
        session["user_id"] = resp.user_id
        return redirect(url_for("index"))

    flash(resp.message or "Login failed")
    return redirect(url_for("index"))


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
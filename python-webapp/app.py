from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import grpc
import os

import auth_pb2
import auth_pb2_grpc

import productlisting_pb2
import productlisting_pb2_grpc

PRODUCTS_GRPC_TARGET = os.environ.get("PRODUCTS_GRPC_TARGET", "microservice-productlisting:50052")

# (optional) create one channel and reuse it
_products_channel = grpc.insecure_channel(PRODUCTS_GRPC_TARGET)
_products_stub = productlisting_pb2_grpc.ProductListingServiceStub(_products_channel)

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

@app.get("/products")
def products():
    return render_template("products.html")


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

@app.get("/api/items")
def api_items_grpc():
    sort = request.args.get("sort", "")
    featured = request.args.get("featured", "false").lower() == "true"
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    type_filter = request.args.get("type", "")

    resp = _products_stub.ListItems(productlisting_pb2.ListItemsRequest(
        sort=sort,
        featured_only=featured,
        type=type_filter,
        limit=limit,
        offset=offset,
    ))

    # Convert protobuf -> JSON for the browser
    return jsonify([
        {
            "id": it.id,
            "title": it.title,
            "price": it.price,
            "image_url": it.image_url,
            "isFeatured": it.is_featured,
        }
        for it in resp.items
    ])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
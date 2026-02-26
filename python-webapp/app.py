from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import grpc
import os

import auth_pb2
import auth_pb2_grpc

import productlisting_pb2
import productlisting_pb2_grpc

import usercarts_pb2
import usercarts_pb2_grpc

import orders_pb2
import orders_pb2_grpc

PRODUCTS_GRPC_TARGET = os.environ.get("PRODUCTS_GRPC_TARGET", "microservice-productlisting:50052")

# (optional) create one channel and reuse it
_products_channel = grpc.insecure_channel(PRODUCTS_GRPC_TARGET)
_products_stub = productlisting_pb2_grpc.ProductListingServiceStub(_products_channel)

CARTS_GRPC_TARGET = os.environ.get("CARTS_GRPC_TARGET", "microservice-usercarts:50053")
_carts_channel = grpc.insecure_channel(CARTS_GRPC_TARGET)
_carts_stub = usercarts_pb2_grpc.UserCartsServiceStub(_carts_channel)

ORDERS_GRPC_TARGET = os.environ.get("ORDERS_GRPC_TARGET", "microservice-orders:50054")
_orders_channel = grpc.insecure_channel(ORDERS_GRPC_TARGET)
_orders_stub = orders_pb2_grpc.OrdersServiceStub(_orders_channel)

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

@app.get("/listing")
def listing_page():
    return render_template("listing.html")

@app.get("/cart")
def cart_page():
    return render_template("cart.html")

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

@app.get("/api/listing")
def api_listing():
    try:
        item_id = int(request.args.get("id", ""))
    except ValueError:
        return jsonify({"error": "id must be an integer"}), 400

    resp = _products_stub.GetItem(productlisting_pb2.GetItemRequest(id=item_id))

    if not resp.found:
        return jsonify({"found": False}), 404

    it = resp.item
    return jsonify({
        "found": True,
        "item": {
            "id": it.id,
            "title": it.title,
            "price": it.price,
            "image_url": it.image_url,
            "isFeatured": it.is_featured,
            "type": it.type,  # include if you have it
        }
    })

@app.post("/api/cart/add")
def api_cart_add():
    # Require login
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"ok": False, "message": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    try:
        item_id = int(data.get("item_id", 0))
        quantity = int(data.get("quantity", 1))
    except ValueError:
        return jsonify({"ok": False, "message": "Invalid payload"}), 400

    resp = _carts_stub.AddToCart(usercarts_pb2.AddToCartRequest(
        user_id=str(user_id),
        item_id=item_id,
        quantity=quantity,
    ))

    return jsonify({"ok": resp.ok, "message": resp.message}), (200 if resp.ok else 400)

@app.get("/api/cart")
def api_cart():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"ok": False, "message": "Not logged in"}), 401

    cart = _carts_stub.GetCart(usercarts_pb2.GetCartRequest(user_id=str(user_id)))

    items = []
    total = 0.0

    for ci in cart.items:
        # product info
        pr = _products_stub.GetItem(productlisting_pb2.GetItemRequest(id=ci.item_id))
        if not pr.found:
            continue
        p = pr.item
        line_total = float(p.price) * int(ci.quantity)
        total += line_total
        items.append({
            "id": p.id,
            "title": p.title,
            "price": float(p.price),
            "qty": int(ci.quantity),
            "image_url": p.image_url,
            "line_total": line_total,
        })

    return jsonify({"ok": True, "items": items, "total": total})

@app.post("/api/order/place")
def api_place_order():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"ok": False, "message": "Not logged in"}), 401

    resp = _orders_stub.PlaceOrder(orders_pb2.PlaceOrderRequest(user_id=str(user_id)))
    return jsonify({"ok": resp.ok, "message": resp.message}), (200 if resp.ok else 400)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
const grid = document.getElementById("cartGrid");
const totalEl = document.getElementById("total");
const statusEl = document.getElementById("status");
const placeBtn = document.getElementById("placeOrder");

async function loadCart() {
  statusEl.textContent = "Loading...";
  grid.innerHTML = "";

  const res = await fetch("/api/cart");
  if (!res.ok) {
    statusEl.textContent = "Please log in.";
    return;
  }
  const data = await res.json();

  if (!data.ok) {
    statusEl.textContent = data.message || "Failed to load cart";
    return;
  }

  for (const it of data.items) {
    const card = document.createElement("div");
    card.className = "card";

    // Build dropdown options: All + 1..qty
    const options = ['<option value="all" selected>All</option>']
      .concat(Array.from({ length: it.qty }, (_, i) => `<option value="${i + 1}">${i + 1}</option>`))
      .join("");

    card.innerHTML = `
      <a href="/listing?id=${it.id}"><img src="${it.image_url}" alt=""></a>
      <div class="title"></div>
      <div>$${it.price.toFixed(2)} × ${it.qty}</div>
      <div><strong>$${it.line_total.toFixed(2)}</strong></div>

      <div class="row">
        <label>
          Remove:
          <select class="removeQty">
            ${options}
          </select>
        </label>
        <button class="removeBtn" type="button">Remove</button>
      </div>
    `;

    card.querySelector(".title").textContent = it.title;

    const selectEl = card.querySelector(".removeQty");
    const btnEl = card.querySelector(".removeBtn");

    btnEl.addEventListener("click", async () => {
      statusEl.textContent = "Removing...";

      const val = selectEl.value;
      const payload =
        val === "all"
          ? { item_id: it.id, remove_all: true }
          : { item_id: it.id, remove_all: false, quantity: Number(val) };

      const r = await fetch("/api/cart/remove", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const resp = await r.json().catch(() => ({ ok: false, message: "Bad response" }));
      statusEl.textContent = resp.ok ? "Updated" : (resp.message || "Failed");

      await loadCart();
    });

    grid.appendChild(card);
  }

  totalEl.textContent = `$${Number(data.total).toFixed(2)}`;
  statusEl.textContent = data.items.length ? "" : "Cart is empty.";
}

placeBtn.addEventListener("click", async () => {
  statusEl.textContent = "Placing order...";
  const res = await fetch("/api/order/place", { method: "POST" });
  const data = await res.json().catch(() => ({ ok: false, message: "Bad response" }));

  statusEl.textContent = data.ok ? "Order placed! (cart cleared)" : (data.message || "Failed");
  if (data.ok) await loadCart();
});

loadCart();
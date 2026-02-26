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
    card.innerHTML = `
      <img src="${it.image_url}" alt="">
      <div class="title"></div>
      <div>$${it.price.toFixed(2)} × ${it.qty}</div>
      <div><strong>$${it.line_total.toFixed(2)}</strong></div>
    `;
    card.querySelector(".title").textContent = it.title;
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

async function loadCart() {
  const target = document.getElementById("cart-items");
  const token = localStorage.getItem("access_token");

  if (!target) return;

  if (!token) {
    target.innerHTML = `
      <p>Please log in to view your cart.</p>
      <a href="login.html" class="btn">Login</a>
    `;
    return;
  }

  try {
    const response = await fetch(`${API_URL}/cart`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Unable to load cart");
    }

    const cart = await response.json();

    if (!Array.isArray(cart) || cart.length === 0) {
      target.innerHTML = `
        <h2>Your cart is empty</h2>
        <p>Explore our latest collection.</p>
        <a href="shop.html" class="btn">Continue Shopping</a>
      `;
      return;
    }

    const money = (amount) => `$${Number(amount).toFixed(2)}`;

    const cartTotal = cart.reduce((total, item) => {
      const price = Number(
        item.variant.price ?? item.variant.product.base_price
      );

      return total + price * item.quantity;
    }, 0);

    target.innerHTML = `
      <div class="cart-list">
        ${cart
          .map((item) => {
            const product = item.variant.product;
            const variant = item.variant;

            const price = Number(
              variant.price ?? product.base_price
            );

            const subtotal = price * item.quantity;
            const image = product.images?.[0]?.url;

            return `
              <div
                class="cart-item"
                data-item-id="${item.id}"
                style="padding:24px 0;border-bottom:1px solid #ddd;"
              >
                ${
                  image
                    ? `<img
                        src="${image}"
                        alt="${product.name}"
                        style="width:130px;max-width:100%;height:auto;"
                      />`
                    : ""
                }

                <h3>${product.name}</h3>

                <p>Size: ${variant.size || "One Size"}</p>
                <p>Color: ${variant.color || "Default"}</p>
                <p>Price: ${money(price)}</p>
                <p>Subtotal: ${money(subtotal)}</p>
                <p>Available stock: ${variant.stock_quantity}</p>

                <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
                  <label for="quantity-${item.id}">Quantity</label>

                  <input
                    id="quantity-${item.id}"
                    type="number"
                    min="1"
                    max="${variant.stock_quantity}"
                    value="${item.quantity}"
                    style="width:75px;padding:8px;"
                  />

                  <button
                    type="button"
                    class="update-cart"
                    data-item-id="${item.id}"
                  >
                    Update
                  </button>

                  <button
                    type="button"
                    class="remove-cart"
                    data-item-id="${item.id}"
                  >
                    Remove
                  </button>
                </div>

                <p class="cart-item-message"></p>
              </div>
            `;
          })
          .join("")}
      </div>

      <div style="padding:24px 0;">
        <h2>Cart Subtotal: ${money(cartTotal)}</h2>
        <p>Shipping and taxes calculated at checkout.</p>
      </div>
    `;

    target.querySelectorAll(".update-cart").forEach((button) => {
      button.addEventListener("click", async () => {
        const itemId = button.dataset.itemId;
        const itemElement = button.closest(".cart-item");
        const quantityInput = itemElement.querySelector("input");
        const message = itemElement.querySelector(".cart-item-message");

        const quantity = Number(quantityInput.value);
        const maxStock = Number(quantityInput.max);

        if (
          !Number.isInteger(quantity) ||
          quantity < 1 ||
          quantity > maxStock
        ) {
          message.textContent = "Invalid quantity";
          return;
        }

        try {
          button.disabled = true;

          const response = await fetch(`${API_URL}/cart/${itemId}`, {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ quantity }),
          });

          if (!response.ok) {
            throw new Error("Unable to update quantity");
          }

          await loadCart();
        } catch (error) {
          message.textContent = error.message;
          button.disabled = false;
        }
      });
    });

    target.querySelectorAll(".remove-cart").forEach((button) => {
      button.addEventListener("click", async () => {
        const itemId = button.dataset.itemId;
        const itemElement = button.closest(".cart-item");
        const message = itemElement.querySelector(".cart-item-message");

        try {
          button.disabled = true;

          const response = await fetch(`${API_URL}/cart/${itemId}`, {
            method: "DELETE",
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error("Unable to remove item");
          }

          await loadCart();
        } catch (error) {
          message.textContent = error.message;
          button.disabled = false;
        }
      });
    });
  } catch (error) {
    target.textContent = error.message;
  }
}

loadCart();

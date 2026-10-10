
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const message = document.getElementById("auth-message");

if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        body: new URLSearchParams(new FormData(loginForm)),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed");
      }

      localStorage.setItem("access_token", data.access_token);
      location.href = "account.html";
    } catch (error) {
      if (message) message.textContent = error.message;
    }
  });
}

if (registerForm) {
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    try {
      const data = Object.fromEntries(new FormData(registerForm));

      const response = await fetch(`${API_URL}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (!response.ok) {
        const detail = result.detail;
        const errorMessage = Array.isArray(detail)
          ? detail.map((error) => error.msg).join(", ")
          : detail || "Registration failed";

        throw new Error(errorMessage);
      }

      location.href = "login.html";
    } catch (error) {
      if (message) message.textContent = error.message;
    }
  });
}

async function loadAccount() {
  const panel = document.getElementById("account-panel");
  const ordersPanel = document.getElementById("orders-panel");
  const ordersList = document.getElementById("orders-list");

  if (!panel) return;

  const token = localStorage.getItem("access_token");

  if (!token) {
    panel.innerHTML = `
      <h2>Please log in</h2>
      <p>Log in to view your account and orders.</p>
      <a href="login.html" class="btn">Login</a>
    `;
    return;
  }

  try {
    const response = await fetch(`${API_URL}/auth/me`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Your session has expired. Please log in again.");
    }

    const user = await response.json();

    panel.replaceChildren();

    const heading = document.createElement("h2");
    heading.textContent = user.username;

    const email = document.createElement("p");
    email.textContent = user.email;

    const logoutButton = document.createElement("button");
    logoutButton.id = "logout";
    logoutButton.className = "btn";
    logoutButton.textContent = "Logout";

    logoutButton.addEventListener("click", () => {
      localStorage.removeItem("access_token");
      location.href = "login.html";
    });

    panel.append(heading, email, logoutButton);

    if (ordersPanel && ordersList) {
      ordersPanel.hidden = false;
      await loadOrders(token, ordersList);
    }
    const wishlistPanel = document.getElementById("wishlist-panel");
    const wishlistList = document.getElementById("wishlist-list");

    if (wishlistPanel && wishlistList) {
      wishlistPanel.hidden = false;
      await loadWishlist(token, wishlistList);
    }
  } catch (error) {
    panel.replaceChildren();

    const errorText = document.createElement("p");
    errorText.textContent = error.message;

    const loginLink = document.createElement("a");
    loginLink.href = "login.html";
    loginLink.className = "btn";
    loginLink.textContent = "Login";

    panel.append(errorText, loginLink);

    if (ordersPanel) ordersPanel.hidden = true;
  }
}

async function loadOrders(token, target) {
  try {
    const response = await fetch(`${API_URL}/orders`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Unable to load order history");
    }

    const orders = await response.json();

    if (!Array.isArray(orders) || orders.length === 0) {
      target.textContent = "You haven't placed any orders yet.";
      return;
    }

    target.replaceChildren();

    for (const order of orders) {
      const card = document.createElement("div");

      card.style.padding = "20px 0";
      card.style.borderBottom = "1px solid #ddd";

      const heading = document.createElement("h3");
      heading.textContent = `Order ${order.order_number}`;

      const date = document.createElement("p");
      date.textContent = `Placed: ${order.created_at
          ? new Date(order.created_at).toLocaleDateString()
          : "Date unavailable"
        }`;

      const status = document.createElement("p");
      status.textContent = `Status: ${order.status ?? "Pending"}`;

      const total = document.createElement("p");
      total.textContent = `Total: $${Number(order.total).toFixed(2)}`;

      card.append(heading, date, status, total);

      if (Array.isArray(order.items)) {
        const itemsHeading = document.createElement("h4");
        itemsHeading.textContent = "Items";
        card.append(itemsHeading);

        const itemList = document.createElement("ul");

        for (const item of order.items) {
          const listItem = document.createElement("li");

          listItem.textContent = `${item.product_name
            } (${item.size || "One Size"}) × ${item.quantity
            } — $${(
              Number(item.unit_price) * item.quantity
            ).toFixed(2)}`;

          itemList.append(listItem);
        }

        card.append(itemList);
      }

      target.append(card);
    }
  } catch (error) {
    target.textContent = error.message;
  }
}

loadAccount();

async function loadWishlist(token, target) {
  try {
    const response = await fetch(`${API_URL}/wishlist`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error("Unable to load wishlist");
    }

    const wishlist = await response.json();

    target.replaceChildren();

    if (!Array.isArray(wishlist) || wishlist.length === 0) {
      target.textContent = "Your wishlist is empty.";
      return;
    }

    for (const item of wishlist) {
      const product = item.product;

      if (!product) continue;

      const card = document.createElement("div");
      card.style.padding = "20px 0";
      card.style.borderBottom = "1px solid #ddd";

      const image = document.createElement("img");
      image.src = product.images?.[0]?.url || "";
      image.alt = product.name;
      image.style.width = "140px";
      image.style.maxWidth = "100%";
      image.style.display = "block";
      image.style.marginBottom = "15px";

      const heading = document.createElement("h3");
      heading.textContent = product.name;

      const price = document.createElement("p");
      price.textContent = `$${Number(product.base_price).toFixed(2)}`;

      const link = document.createElement("a");
      link.href = `product.html?slug=${encodeURIComponent(product.slug)}`;
      link.className = "btn";
      link.textContent = "View Product";

      const removeButton = document.createElement("button");
      removeButton.type = "button";
      removeButton.textContent = "Remove";
      removeButton.className = "btn";
      removeButton.style.marginLeft = "10px";

      removeButton.addEventListener("click", async () => {
        try {
          const removeResponse = await fetch(
            `${API_URL}/wishlist/${product.id}`,
            {
              method: "DELETE",
              headers: {
                Authorization: `Bearer ${token}`,
              },
            }
          );

          if (!removeResponse.ok) {
            throw new Error("Unable to remove product");
          }

          await loadWishlist(token, target);
        } catch (error) {
          alert(error.message);
        }
      });

      card.append(heading, price);

      if (product.images?.[0]?.url) {
        card.prepend(image);
      }

      card.append(link, removeButton);
      target.append(card);
    }
  } catch (error) {
    target.textContent = error.message;
  }
}
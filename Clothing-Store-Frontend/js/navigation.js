
const accessToken = localStorage.getItem("access_token");

const navigation = document.querySelector(".site-header nav");

if (navigation) {
  navigation.replaceChildren();

  const links = [
    { name: "Shop", href: "shop.html" },
    {
      name: accessToken ? "Account" : "Login",
      href: accessToken ? "account.html" : "login.html",
    },
    { name: "Cart", href: "cart.html" },
  ];

  for (const link of links) {
    const anchor = document.createElement("a");
    anchor.href = link.href;
    anchor.textContent = link.name;

    if (link.name === "Cart") {
      anchor.id = "nav-cart";
    }

    navigation.append(anchor);
  }

  if (accessToken) {
    const logoutButton = document.createElement("button");
    logoutButton.type = "button";
    logoutButton.textContent = "Logout";
    logoutButton.className = "nav-logout";

    logoutButton.addEventListener("click", () => {
      localStorage.removeItem("access_token");
      location.href = "login.html";
    });

    navigation.append(logoutButton);
  }
}

async function updateCartCounter() {
  const cartLink = document.getElementById("nav-cart");

  if (!cartLink) return;

  const token = localStorage.getItem("access_token");

  if (!token) {
    cartLink.textContent = "Cart";
    return;
  }

  try {
    const response = await fetch(`${API_URL}/cart`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      cartLink.textContent = "Cart";
      return;
    }

    const items = await response.json();

    const count = items.reduce(
      (total, item) => total + item.quantity,
      0
    );

    cartLink.textContent = count > 0 ? `Cart (${count})` : "Cart";
  } catch (error) {
    cartLink.textContent = "Cart";
  }
}

updateCartCounter();

window.addEventListener("pageshow", updateCartCounter);

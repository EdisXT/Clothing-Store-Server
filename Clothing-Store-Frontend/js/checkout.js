
const checkoutForm = document.getElementById("checkout-form");

async function checkoutRequest(url, options, token) {
  const response = await fetch(`${API_URL}${url}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    const detail = data.detail;

    const errorMessage = Array.isArray(detail)
      ? detail.map((error) => error.msg).join(", ")
      : detail || "Request failed";

    throw new Error(errorMessage);
  }

  return data;
}

if (checkoutForm) {
  checkoutForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = document.getElementById("checkout-message");
    const button = document.getElementById("place-order");
    const confirmation = document.getElementById("order-confirmation");
    const token = localStorage.getItem("access_token");

    message.textContent = "";

    if (!token) {
      message.textContent = "Please log in before checkout.";
      return;
    }

    const formData = Object.fromEntries(
      new FormData(checkoutForm).entries()
    );

    const address = {
      label: "Home",
      full_name: formData.full_name,
      line1: formData.line1,
      line2: formData.line2 || null,
      city: formData.city,
      state: formData.state,
      postal_code: formData.postal_code,
      country: "US",
      phone: formData.phone || null,
      is_default: false,
    };

    const couponCode = formData.coupon_code?.trim() || null;

    button.disabled = true;
    button.textContent = "Processing...";

    try {
      const savedAddress = await checkoutRequest(
        "/addresses",
        {
          method: "POST",
          body: JSON.stringify(address),
        },
        token
      );

      const order = await checkoutRequest(
        "/orders/checkout",
        {
          method: "POST",
          body: JSON.stringify({
            address_id: savedAddress.id,
            coupon_code: couponCode,
          }),
        },
        token
      );

      checkoutForm.hidden = true;
      confirmation.hidden = false;

      confirmation.replaceChildren();

      const heading = document.createElement("h2");
      heading.textContent = "Order Placed Successfully!";

      const orderNumber = document.createElement("p");
      orderNumber.textContent = `Order Number: ${order.order_number}`;

      const total = document.createElement("p");
      total.textContent = `Order Total: $${Number(order.total).toFixed(2)}`;

      const paymentStatus = document.createElement("p");
      paymentStatus.textContent =
        "Test order created. No payment has been processed.";

      const shopLink = document.createElement("a");
      shopLink.href = "shop.html";
      shopLink.className = "btn";
      shopLink.textContent = "Continue Shopping";

      confirmation.append(
        heading,
        orderNumber,
        total,
        paymentStatus,
        shopLink
      );
    } catch (error) {
      message.textContent = error.message;
    } finally {
      button.disabled = false;
      button.textContent = "Place Order";
    }
  });
}

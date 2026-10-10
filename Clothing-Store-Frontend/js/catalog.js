async function loadProducts() {
  const target = document.querySelector(
    "#product-grid, #featured-products"
  );

  if (!target) {
    return;
  }

  try {
    const response = await fetch(`${API_URL}/catalog/products`);

    if (!response.ok) {
      throw new Error("Unable to load products");
    }

    const data = await response.json();

    const products = Array.isArray(data)
      ? data
      : data.products || [];

    target.innerHTML = products
      .map(
        (product) => `
          <a
            class="product-card"
            href="product.html?slug=${encodeURIComponent(product.slug)}"
          >
            <div class="product-image">
              Product image
            </div>

            <div class="product-copy">
              <strong>${product.name}</strong>
            </div>
          </a>
        `
      )
      .join("");
  } catch (error) {
    target.innerHTML = `<p>${error.message}</p>`;
  }
}

loadProducts();

const slug = new URLSearchParams(location.search).get("slug");

async function loadProduct() {
  const container = document.getElementById("product-detail");

  if (!container || !slug) return;

  try {
    const response = await fetch(
      `${API_URL}/catalog/products/${encodeURIComponent(slug)}`
    );

    if (!response.ok) {
      throw new Error("Product not found");
    }

    const product = await response.json();
    const variants = (product.variants || []).filter(
      (variant) => variant.is_active
    );

    const images = (product.images || []).filter(
      (image) => image.url && !image.url.includes("placehold.co")
    );

    const imageUrl = images[0]?.url || "";

    const colors = [
      ...new Set(variants.map((variant) => variant.color || "Default")),
    ];

    const price = Number(product.base_price).toFixed(2);

    const comparePrice = product.compare_at_price
      ? Number(product.compare_at_price).toFixed(2)
      : null;

    container.innerHTML = `
      <div class="product-gallery"></div>

      <div class="product-information">
        <h1></h1>

        <div class="product-pricing">
          <strong>$${price}</strong>
          ${
            comparePrice
              ? `<del style="margin-left:12px;color:gray;">$${comparePrice}</del>`
              : ""
          }
        </div>

        <p id="product-description"></p>

        <h3>Select Color</h3>
        <div id="color-options" style="display:flex;gap:10px;flex-wrap:wrap;"></div>

        <h3>Select Size</h3>
        <div id="size-options" style="display:flex;gap:10px;flex-wrap:wrap;"></div>

        <p id="stock-message" role="status">Select a color and size</p>

        <label for="quantity">Quantity</label>
        <input
          id="quantity"
          type="number"
          min="1"
          value="1"
          style="display:block;width:80px;padding:10px;margin:12px 0;"
        />

        <button id="add-to-cart" type="button" disabled>
          ADD TO CART
        </button>

        <button
          id="wishlist-button"
          type="button"
          style="margin-left:12px;padding:10px 16px;cursor:pointer;"
        >
          ♡ Add to Wishlist
        </button>

        <p id="cart-message" role="status"></p>
        <p id="wishlist-message" role="status"></p>
      </div>
    `;

    container.querySelector("h1").textContent = product.name;

    container.querySelector("#product-description").textContent =
      product.description || "";

    const gallery = container.querySelector(".product-gallery");

    if (imageUrl) {
      const image = document.createElement("img");
      image.src = imageUrl;
      image.alt = images[0].alt_text || product.name;
      image.style.width = "100%";
      image.style.height = "auto";
      image.style.objectFit = "cover";
      gallery.append(image);
    } else {
      gallery.hidden = true;
      container.style.display = "block";
    }

    const colorOptions = container.querySelector("#color-options");
    const sizeOptions = container.querySelector("#size-options");
    const stockMessage = container.querySelector("#stock-message");
    const quantityInput = container.querySelector("#quantity");
    const addToCartButton = container.querySelector("#add-to-cart");
    const cartMessage = container.querySelector("#cart-message");
    const wishlistButton = container.querySelector("#wishlist-button");
    const wishlistMessage = container.querySelector("#wishlist-message");

    let selectedColor = null;
    let selectedSize = null;
    let selectedVariant = null;
    let isWishlisted = false;

    function updateSelection() {
      selectedVariant = variants.find(
        (variant) =>
          (variant.color || "Default") === selectedColor &&
          (variant.size || "One Size") === selectedSize
      );

      quantityInput.value = 1;
      cartMessage.textContent = "";

      if (!selectedVariant) {
        stockMessage.textContent = "Select a color and size";
        addToCartButton.disabled = true;
        quantityInput.removeAttribute("max");
        return;
      }

      const stock = selectedVariant.stock_quantity;

      stockMessage.textContent =
        stock > 0 ? `${stock} available` : "Out of stock";

      quantityInput.max = stock;
      addToCartButton.disabled = stock <= 0;
    }

    function renderSizes() {
      sizeOptions.replaceChildren();

      const availableSizes = [
        ...new Set(
          variants
            .filter(
              (variant) => (variant.color || "Default") === selectedColor
            )
            .map((variant) => variant.size || "One Size")
        ),
      ];

      for (const size of availableSizes) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "size-option";
        button.textContent = size;

        const variant = variants.find(
          (item) =>
            (item.color || "Default") === selectedColor &&
            (item.size || "One Size") === size
        );

        button.disabled = !variant || variant.stock_quantity <= 0;

        if (size === selectedSize) {
          button.style.background = "black";
          button.style.color = "white";
        }

        button.addEventListener("click", () => {
          selectedSize = size;
          renderSizes();
          updateSelection();
        });

        sizeOptions.append(button);
      }
    }

    function renderColors() {
      colorOptions.replaceChildren();

      for (const color of colors) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "size-option";
        button.textContent = color;

        if (color === selectedColor) {
          button.style.background = "black";
          button.style.color = "white";
        }

        button.addEventListener("click", () => {
          selectedColor = color;
          selectedSize = null;

          renderColors();
          renderSizes();
          updateSelection();
        });

        colorOptions.append(button);
      }
    }

    renderColors();

    if (colors.length > 0) {
      selectedColor = colors[0];
      renderColors();
      renderSizes();
      updateSelection();
    } else {
      stockMessage.textContent = "Currently unavailable";
    }

    const token = localStorage.getItem("access_token");

    if (token) {
      try {
        const wishlistResponse = await fetch(`${API_URL}/wishlist`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (wishlistResponse.ok) {
          const wishlist = await wishlistResponse.json();

          isWishlisted = wishlist.some(
            (item) => item.product?.id === product.id
          );

          wishlistButton.textContent = isWishlisted
            ? "♥ Remove from Wishlist"
            : "♡ Add to Wishlist";
        }
      } catch (error) {
        wishlistMessage.textContent = "Unable to load wishlist status.";
      }
    }

    addToCartButton.addEventListener("click", async () => {
      if (!selectedVariant) return;

      const quantity = Number(quantityInput.value);

      if (
        !Number.isInteger(quantity) ||
        quantity < 1 ||
        quantity > selectedVariant.stock_quantity
      ) {
        cartMessage.textContent = "Invalid quantity";
        return;
      }

      const currentToken = localStorage.getItem("access_token");

      if (!currentToken) {
        cartMessage.textContent = "Please log in before adding to cart.";
        return;
      }

      try {
        addToCartButton.disabled = true;

        const cartResponse = await fetch(`${API_URL}/cart`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${currentToken}`,
          },
          body: JSON.stringify({
            variant_id: selectedVariant.id,
            quantity,
          }),
        });

        if (!cartResponse.ok) {
          const errorData = await cartResponse.json().catch(() => null);
          throw new Error(
            typeof errorData?.detail === "string"
              ? errorData.detail
              : "Unable to add item to cart"
          );
        }

        cartMessage.textContent = "Added to cart successfully!";

        if (typeof updateNavigation === "function") {
          updateNavigation();
        }
      } catch (error) {
        cartMessage.textContent = error.message;
      } finally {
        addToCartButton.disabled = selectedVariant.stock_quantity <= 0;
      }
    });

    wishlistButton.addEventListener("click", async () => {
      const currentToken = localStorage.getItem("access_token");

      if (!currentToken) {
        wishlistMessage.textContent = "Please log in to use your wishlist.";
        return;
      }

      wishlistButton.disabled = true;
      wishlistMessage.textContent = "";

      try {
        const wishlistResponse = await fetch(
          `${API_URL}/wishlist/${product.id}`,
          {
            method: isWishlisted ? "DELETE" : "POST",
            headers: {
              Authorization: `Bearer ${currentToken}`,
            },
          }
        );

        if (!wishlistResponse.ok) {
          throw new Error("Unable to update wishlist");
        }

        isWishlisted = !isWishlisted;

        wishlistButton.textContent = isWishlisted
          ? "♥ Remove from Wishlist"
          : "♡ Add to Wishlist";

        wishlistMessage.textContent = isWishlisted
          ? "Product added to your wishlist!"
          : "Product removed from your wishlist!";
      } catch (error) {
        wishlistMessage.textContent = error.message;
      } finally {
        wishlistButton.disabled = false;
      }
    });
  } catch (error) {
    container.textContent = error.message;
  }
}

loadProduct();

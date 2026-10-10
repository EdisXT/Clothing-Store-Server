
const adminMessage = document.getElementById("admin-message");
const adminDashboard = document.getElementById("admin-dashboard");
const adminProducts = document.getElementById("admin-products");
const adminOrders = document.getElementById("admin-orders");

const token = localStorage.getItem("access_token");

function formatMoney(value) {
    return `$${Number(value).toFixed(2)}`;
}

function showAdminMessage(text) {
    adminMessage.textContent = text;
}

async function adminRequest(path, options = {}) {
    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers: {
            Authorization: `Bearer ${token}`,
            ...(options.headers || {}),
        },
    });

    if (!response.ok) {
        let detail = "Request failed";

        try {
            const data = await response.json();
            if (typeof data.detail === "string") {
                detail = data.detail;
            }
        } catch { }

        throw new Error(detail);
    }

    return response.status === 204 ? null : response.json();
}


function showEditProductForm(product, row, editButton) {
    const existingForm = row.querySelector(".edit-product-form");

    if (existingForm) {
        existingForm.remove();
        editButton.textContent = "Edit Product";
        return;
    }

    const form = document.createElement("form");
    form.className = "edit-product-form";
    form.style.display = "grid";
    form.style.gap = "12px";
    form.style.marginTop = "20px";

    function addField(labelText, name, value, type = "text") {
        const label = document.createElement("label");
        label.textContent = labelText;

        const input = document.createElement("input");
        input.className = "input";
        input.name = name;
        input.type = type;
        input.value = value ?? "";

        if (type === "number") {
            input.step = "0.01";
            if (name === "base_price") {
                input.min = "0.01";
                input.required = true;
            }
        }

        label.append(input);
        form.append(label);
    }

    addField("Product Name", "name", product.name);
    addField("Description", "description", product.description);
    addField("Price ($)", "base_price", product.base_price, "number");
    addField(
        "Compare At Price ($)",
        "compare_at_price",
        product.compare_at_price,
        "number"
    );

    const featuredLabel = document.createElement("label");
    const featuredInput = document.createElement("input");
    featuredInput.type = "checkbox";
    featuredInput.name = "is_featured";
    featuredInput.checked = product.is_featured;

    featuredLabel.append(featuredInput, " Featured Product");
    form.append(featuredLabel);

    const saveButton = document.createElement("button");
    saveButton.type = "submit";
    saveButton.className = "btn";
    saveButton.textContent = "Save Changes";

    const feedback = document.createElement("p");
    feedback.setAttribute("role", "status");

    form.append(saveButton, feedback);
    row.append(form);

    editButton.textContent = "Close Editor";

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const data = new FormData(form);

        const payload = {
            name: String(data.get("name")).trim(),
            description: String(data.get("description")).trim(),
            base_price: String(data.get("base_price")),
            compare_at_price: String(data.get("compare_at_price")).trim() || null,
            is_featured: data.has("is_featured"),
        };

        if (!payload.name || Number(payload.base_price) <= 0) {
            feedback.textContent = "Enter a valid product name and price.";
            return;
        }

        try {
            saveButton.disabled = true;
            feedback.textContent = "Saving changes...";

            await adminRequest(`/catalog/products/${product.id}`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            await loadAdminProducts();
        } catch (error) {
            feedback.textContent = error.message;
            saveButton.disabled = false;
        }
    });
}


async function loadAdminProducts() {
    const products = await adminRequest("/catalog/admin/products");

    if (!Array.isArray(products)) {
        throw new Error("Unexpected product response");
    }

    document.getElementById("total-products").textContent = products.length;

    adminProducts.replaceChildren();

    if (products.length === 0) {
        adminProducts.textContent = "No products available.";
        return;
    }

    for (const product of products) {
        const row = document.createElement("div");
        row.style.padding = "18px 0";
        row.style.borderBottom = "1px solid #ddd";

        const name = document.createElement("h3");
        name.textContent = product.name;

        const price = document.createElement("p");
        price.textContent = `Price: ${formatMoney(product.base_price)}`;

        const link = document.createElement("a");
        link.href = `product.html?slug=${encodeURIComponent(product.slug)}`;
        link.textContent = "View Product";
        link.className = "btn";

        const editButton = document.createElement("button");
        editButton.type = "button";
        editButton.className = "btn";
        editButton.textContent = "Edit Product";

        editButton.addEventListener("click", () => {
            showEditProductForm(product, row, editButton);
        });

        const visibilityButton = document.createElement("button");
        visibilityButton.type = "button";
        visibilityButton.className = "btn";

        function updateVisibilityDisplay() {
            visibilityButton.textContent = product.is_active
                ? "Hide Product"
                : "Publish Product";

            link.hidden = !product.is_active;
        }

        updateVisibilityDisplay();

        const visibilityFeedback = document.createElement("p");
        visibilityFeedback.setAttribute("role", "status");

        visibilityButton.addEventListener("click", async () => {
            const nextStatus = !product.is_active;

            try {
                visibilityButton.disabled = true;
                visibilityFeedback.textContent = "Updating visibility...";

                await adminRequest(`/catalog/products/${product.id}`, {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        is_active: nextStatus,
                    }),
                });

                product.is_active = nextStatus;
                updateVisibilityDisplay();

                visibilityFeedback.textContent = product.is_active
                    ? "Product published successfully!"
                    : "Product hidden successfully!";
            } catch (error) {
                visibilityFeedback.textContent = error.message;
            } finally {
                visibilityButton.disabled = false;
            }
        });

        row.append(
            name,
            price,
            link,
            editButton,
            visibilityButton,
            visibilityFeedback
        );

        const addVariantButton = document.createElement("button");
        addVariantButton.type = "button";
        addVariantButton.className = "btn";
        addVariantButton.textContent = "Add Size / Color";

        const variantForm = document.createElement("form");
        variantForm.style.display = "none";
        variantForm.style.margin = "20px 0";
        variantForm.style.gap = "12px";

        variantForm.innerHTML = `
  <h4>Add New Variant</h4>

  <label>
    Size
    <input class="input" name="size" placeholder="XXL" required>
  </label>

  <label>
    Color
    <input class="input" name="color" placeholder="Gray" required>
  </label>

  <label>
    Stock Quantity
    <input class="input" name="stock" type="number" min="0" step="1" value="10" required>
  </label>

  <button class="btn" type="submit">Save Variant</button>
  <p class="variant-feedback" role="status"></p>
`;

        addVariantButton.addEventListener("click", () => {
            const isOpen = variantForm.style.display === "grid";

            variantForm.style.display = isOpen ? "none" : "grid";
            addVariantButton.textContent = isOpen
                ? "Add Size / Color"
                : "Close Variant Form";
        });

        variantForm.addEventListener("submit", async (event) => {
            event.preventDefault();

            const data = new FormData(variantForm);

            const size = String(data.get("size")).trim().toUpperCase();
            const color = String(data.get("color")).trim();
            const stock = Number(data.get("stock"));

            const feedback = variantForm.querySelector(".variant-feedback");
            const saveButton = variantForm.querySelector('button[type="submit"]');

            if (!size || !color || !Number.isSafeInteger(stock) || stock < 0) {
                feedback.textContent = "Enter a valid size, color, and stock quantity.";
                return;
            }

            const duplicate = (product.variants || []).some(
                (variant) =>
                    (variant.size || "").toUpperCase() === size &&
                    (variant.color || "").toLowerCase() === color.toLowerCase()
            );

            if (duplicate) {
                feedback.textContent = "This size and color already exist.";
                return;
            }

            const sku = `${product.slug}-${color}-${size}`
                .toUpperCase()
                .replace(/[^A-Z0-9]+/g, "-");

            try {
                saveButton.disabled = true;
                feedback.textContent = "Saving variant...";

                await adminRequest(`/catalog/products/${product.id}/variants`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        sku,
                        size,
                        color,
                        price: null,
                        stock_quantity: stock,
                        is_active: true,
                    }),
                });

                await loadAdminProducts();
            } catch (error) {
                feedback.textContent = error.message;
                saveButton.disabled = false;
            }
        });

        row.append(addVariantButton, variantForm);

        const variantsHeading = document.createElement("h4");
        variantsHeading.textContent = "Inventory by Size";
        row.append(variantsHeading);

        for (const variant of product.variants || []) {
            const inventoryRow = document.createElement("div");

            inventoryRow.style.display = "flex";
            inventoryRow.style.alignItems = "center";
            inventoryRow.style.gap = "12px";
            inventoryRow.style.marginBottom = "12px";
            inventoryRow.style.flexWrap = "wrap";

            const label = document.createElement("span");
            label.textContent = `${variant.size || "One Size"} / ${variant.color || "Default"}`;

            const stockInput = document.createElement("input");
            stockInput.type = "number";
            stockInput.min = "0";
            stockInput.step = "1";
            stockInput.value = variant.stock_quantity;
            stockInput.className = "input";
            stockInput.style.width = "100px";

            const saveButton = document.createElement("button");
            saveButton.type = "button";
            saveButton.className = "btn";
            saveButton.textContent = "Update Stock";

            const feedback = document.createElement("span");
            feedback.setAttribute("role", "status");

            saveButton.addEventListener("click", async () => {
                const quantity = Number(stockInput.value);

                if (!Number.isSafeInteger(quantity) || quantity < 0) {
                    feedback.textContent = "Enter a valid stock quantity.";
                    return;
                }

                try {
                    saveButton.disabled = true;
                    feedback.textContent = "Saving...";

                    await adminRequest(`/admin/inventory/${variant.id}`, {
                        method: "PATCH",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({
                            stock_quantity: quantity,
                        }),
                    });

                    variant.stock_quantity = quantity;
                    feedback.textContent = "Stock updated successfully!";
                } catch (error) {
                    feedback.textContent = error.message;
                } finally {
                    saveButton.disabled = false;
                }
            });

            const toggleButton = document.createElement("button");
            toggleButton.type = "button";
            toggleButton.className = "btn";

            function updateVariantDisplay() {
                toggleButton.textContent = variant.is_active
                    ? "Disable Variant"
                    : "Enable Variant";

                label.textContent = `${variant.size || "One Size"} / ${variant.color || "Default"
                    } ${variant.is_active ? "(Active)" : "(Disabled)"}`;
            }

            updateVariantDisplay();

            toggleButton.addEventListener("click", async () => {
                const nextStatus = !variant.is_active;

                try {
                    toggleButton.disabled = true;
                    feedback.textContent = "Updating variant...";

                    const updatedVariant = await adminRequest(
                        `/catalog/variants/${variant.id}`,
                        {
                            method: "PATCH",
                            headers: {
                                "Content-Type": "application/json",
                            },
                            body: JSON.stringify({
                                is_active: nextStatus,
                            }),
                        }
                    );

                    variant.is_active = updatedVariant.is_active;

                    updateVariantDisplay();

                    feedback.textContent = variant.is_active
                        ? "Variant enabled successfully!"
                        : "Variant disabled successfully!";
                } catch (error) {
                    feedback.textContent = error.message;
                } finally {
                    toggleButton.disabled = false;
                }
            });

            inventoryRow.append(
                label,
                stockInput,
                saveButton,
                toggleButton,
                feedback
            );

            row.append(inventoryRow);
        }

        adminProducts.append(row);
    }
}

async function loadAdminOrders() {
    const orders = await adminRequest("/admin/orders");

    if (!Array.isArray(orders)) {
        throw new Error("Unexpected orders response");
    }

    document.getElementById("total-orders").textContent = orders.length;

    document.getElementById("pending-orders").textContent = orders.filter(
        (order) => order.status === "pending"
    ).length;

    adminOrders.replaceChildren();

    if (orders.length === 0) {
        adminOrders.textContent = "No customer orders yet.";
        return;
    }

    for (const order of orders) {
        const row = document.createElement("div");
        row.style.padding = "20px 0";
        row.style.borderBottom = "1px solid #ddd";

        const heading = document.createElement("h3");
        heading.textContent = `Order ${order.order_number}`;

        const customer = document.createElement("p");
        customer.textContent = `Order ID: ${order.id}`;

        const total = document.createElement("p");
        total.textContent = `Total: ${formatMoney(order.total)}`;

        const status = document.createElement("p");
        status.textContent = `Status: ${order.status}`;

        row.append(heading, customer, total, status);

        const statusLabel = document.createElement("label");
        statusLabel.textContent = "Update Order Status";

        const statusSelect = document.createElement("select");
        statusSelect.className = "input";
        statusSelect.style.margin = "12px 0";

        const statuses = [
            "pending",
            "processing",
            "shipped",
            "delivered",
            "cancelled",
        ];

        for (const value of statuses) {
            const option = document.createElement("option");
            option.value = value;
            option.textContent = value.charAt(0).toUpperCase() + value.slice(1);
            statusSelect.append(option);
        }

        statusSelect.value = order.status;

        const updateButton = document.createElement("button");
        updateButton.type = "button";
        updateButton.className = "btn";
        updateButton.textContent = "Update Status";

        const feedback = document.createElement("p");
        feedback.setAttribute("role", "status");

        updateButton.addEventListener("click", async () => {
            try {
                updateButton.disabled = true;
                feedback.textContent = "Updating...";

                await adminRequest(`/admin/orders/${order.id}`, {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        status: statusSelect.value,
                    }),
                });

                order.status = statusSelect.value;
                status.textContent = `Status: ${order.status}`;
                feedback.textContent = "Order status updated successfully!";

                await loadAdminOrders();
            } catch (error) {
                feedback.textContent = error.message;
            } finally {
                updateButton.disabled = false;
            }
        });

        row.append(statusLabel, statusSelect, updateButton, feedback);
        adminOrders.append(row);
    }
}

async function loadAdminDashboard() {
    if (!token) {
        showAdminMessage("Please log in to access the admin dashboard.");
        return;
    }

    try {
        const user = await adminRequest("/auth/me");

        if (!user.is_admin) {
            showAdminMessage("Access denied. Administrator account required.");
            return;
        }

        adminDashboard.hidden = false;
        adminMessage.hidden = true;

        const results = await Promise.allSettled([
            loadAdminProducts(),
            loadAdminOrders(),
        ]);

        if (results[0].status === "rejected") {
            adminProducts.textContent = results[0].reason.message;
        }

        if (results[1].status === "rejected") {
            adminOrders.textContent = results[1].reason.message;
        }
    } catch (error) {
        adminDashboard.hidden = true;
        adminMessage.hidden = false;
        showAdminMessage(error.message);
    }
}

loadAdminDashboard();


const createProductForm = document.getElementById("create-product-form");
const createProductMessage = document.getElementById("create-product-message");

if (createProductForm) {
    createProductForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const submitButton = createProductForm.querySelector(
            'button[type="submit"]'
        );

        const formData = new FormData(createProductForm);

        const name = String(formData.get("name")).trim();
        const slug = String(formData.get("slug")).trim().toLowerCase();
        const color = String(formData.get("color")).trim();

        const sizes = [
            ...new Set(
                String(formData.get("sizes"))
                    .split(",")
                    .map((size) => size.trim().toUpperCase())
                    .filter(Boolean)
            ),
        ];

        const stockQuantity = Number(formData.get("stock_quantity"));

        if (!sizes.length || !Number.isSafeInteger(stockQuantity) || stockQuantity < 0) {
            createProductMessage.textContent = "Enter valid sizes and stock.";
            return;
        }

        const comparePrice = String(formData.get("compare_at_price")).trim();
        const categoryId = String(formData.get("category_id")).trim();
        const collectionId = String(formData.get("collection_id")).trim();
        const imageUrl = String(formData.get("image_url")).trim();

        const product = {
            name,
            slug,
            description: String(formData.get("description")).trim(),
            base_price: String(formData.get("base_price")),
            compare_at_price: comparePrice || null,
            gender: String(formData.get("gender")) || null,
            category_id: categoryId ? Number(categoryId) : null,
            collection_id: collectionId ? Number(collectionId) : null,
            is_active: true,
            is_featured: formData.has("is_featured"),
            variants: sizes.map((size) => ({
                sku: `${slug}-${color}-${size}`
                    .toUpperCase()
                    .replace(/[^A-Z0-9]+/g, "-"),
                size,
                color,
                price: null,
                stock_quantity: stockQuantity,
                is_active: true,
            })),
            images: imageUrl
                ? [
                    {
                        url: imageUrl,
                        alt_text: name,
                        position: 1,
                    },
                ]
                : [],
        };

        try {
            submitButton.disabled = true;
            createProductMessage.textContent = "Creating product...";

            await adminRequest("/catalog/products", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(product),
            });

            createProductMessage.textContent = "Product created successfully!";
            createProductForm.reset();

            await loadAdminProducts();
        } catch (error) {
            createProductMessage.textContent = error.message;
        } finally {
            submitButton.disabled = false;
        }
    });
}


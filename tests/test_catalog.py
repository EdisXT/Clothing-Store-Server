def category_payload():
    return {"name": "T-Shirts", "slug": "t-shirts"}


def collection_payload():
    return {
        "name": "Summer Drop",
        "slug": "summer-drop",
        "description": "Summer 2026 collection",
        "is_featured": True,
    }


def product_payload(category_id=None, collection_id=None):
    return {
        "name": "Heavyweight Graphic Tee",
        "slug": "heavyweight-graphic-tee",
        "description": "Premium heavyweight cotton graphic tee",
        "base_price": "45.00",
        "compare_at_price": "55.00",
        "gender": "unisex",
        "category_id": category_id,
        "collection_id": collection_id,
        "is_active": True,
        "is_featured": True,
        "variants": [
            {
                "sku": "HGT-BLK-M",
                "size": "M",
                "color": "Black",
                "price": "45.00",
                "stock_quantity": 10,
                "is_active": True,
            },
            {
                "sku": "HGT-BLK-L",
                "size": "L",
                "color": "Black",
                "price": "45.00",
                "stock_quantity": 8,
                "is_active": True,
            },
        ],
        "images": [],
    }


def test_public_can_get_categories(client):
    response = client.get("/catalog/categories")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_public_can_get_collections(client):
    response = client.get("/catalog/collections")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_customer_cannot_create_category(authorized_client):
    response = authorized_client.post("/catalog/categories", json=category_payload())

    assert response.status_code == 403


def test_customer_cannot_create_collection(authorized_client):
    response = authorized_client.post("/catalog/collections", json=collection_payload())

    assert response.status_code == 403


def test_customer_cannot_create_product(authorized_client):
    response = authorized_client.post("/catalog/products", json=product_payload())

    assert response.status_code == 403


def test_admin_can_create_category(admin_client):
    response = admin_client.post("/catalog/categories", json=category_payload())

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "T-Shirts"
    assert data["slug"] == "t-shirts"


def test_admin_can_create_collection(admin_client):
    response = admin_client.post("/catalog/collections", json=collection_payload())

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Summer Drop"
    assert data["is_featured"] is True


def test_admin_can_create_product_with_variants(admin_client):
    category_response = admin_client.post(
        "/catalog/categories", json={"name": "Hoodies", "slug": "hoodies"}
    )

    collection_response = admin_client.post(
        "/catalog/collections",
        json={
            "name": "Fall Drop",
            "slug": "fall-drop",
            "description": "Fall collection",
            "is_featured": True,
        },
    )

    assert category_response.status_code == 201
    assert collection_response.status_code == 201

    response = admin_client.post(
        "/catalog/products",
        json=product_payload(
            category_response.json()["id"], collection_response.json()["id"]
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Heavyweight Graphic Tee"
    assert data["slug"] == "heavyweight-graphic-tee"
    assert data["category"]["slug"] == "hoodies"
    assert data["collection"]["slug"] == "fall-drop"

    assert len(data["variants"]) == 2
    assert data["variants"][0]["stock_quantity"] >= 0


def test_public_can_get_products(admin_client, client):
    response = admin_client.post(
        "/catalog/products", json={**product_payload(), "slug": "public-product"}
    )

    assert response.status_code == 201

    response = client.get("/catalog/products")

    assert response.status_code == 200

    products = response.json()

    assert len(products) >= 1

    assert any(product["slug"] == "public-product" for product in products)


def test_public_can_get_product_by_slug(admin_client, client):
    response = admin_client.post(
        "/catalog/products", json={**product_payload(), "slug": "slug-test-product"}
    )

    assert response.status_code == 201

    response = client.get("/catalog/products/slug-test-product")

    assert response.status_code == 200
    assert response.json()["slug"] == "slug-test-product"


def test_unknown_product_returns_404(client):
    response = client.get("/catalog/products/product-that-does-not-exist")

    assert response.status_code == 404


def test_search_products(admin_client, client):
    response = admin_client.post(
        "/catalog/products",
        json={
            **product_payload(),
            "name": "Dragon Graphic Hoodie",
            "slug": "dragon-graphic-hoodie",
        },
    )

    assert response.status_code == 201

    response = client.get("/catalog/products", params={"q": "Dragon"})

    assert response.status_code == 200

    products = response.json()

    assert any(product["slug"] == "dragon-graphic-hoodie" for product in products)


def test_filter_product_by_size_and_color(admin_client, client):
    response = admin_client.post(
        "/catalog/products", json={**product_payload(), "slug": "filter-product"}
    )

    assert response.status_code == 201

    response = client.get("/catalog/products", params={"size": "M", "color": "Black"})

    assert response.status_code == 200

    products = response.json()

    assert any(product["slug"] == "filter-product" for product in products)


def test_filter_products_by_price(admin_client, client):
    response = admin_client.post(
        "/catalog/products",
        json={
            **product_payload(),
            "slug": "price-filter-product",
            "base_price": "75.00",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/catalog/products", params={"min_price": 70, "max_price": 80}
    )

    assert response.status_code == 200

    products = response.json()

    assert any(product["slug"] == "price-filter-product" for product in products)


def test_admin_can_update_product(admin_client):
    create_response = admin_client.post(
        "/catalog/products", json={**product_payload(), "slug": "update-product"}
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    response = admin_client.patch(
        f"/catalog/products/{product_id}",
        json={"name": "Updated Product", "base_price": "60.00", "is_featured": False},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Product"
    assert float(data["base_price"]) == 60.00
    assert data["is_featured"] is False


def test_customer_cannot_update_product(admin_client, client, user_data):
    # Admin creates the product
    create_response = admin_client.post(
        "/catalog/products",
        json={**product_payload(), "slug": "protected-update-product"},
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    # Create normal customer
    register_response = client.post("/auth/register", json=user_data)

    assert register_response.status_code == 201

    # Login as normal customer
    login_response = client.post(
        "/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]},
    )

    assert login_response.status_code == 200

    customer_token = login_response.json()["access_token"]

    # Normal customer tries admin-only product update
    response = client.patch(
        f"/catalog/products/{product_id}",
        json={"name": "Hacked Product"},
        headers={"Authorization": f"Bearer {customer_token}"},
    )

    assert response.status_code == 403


def test_update_unknown_product_returns_404(admin_client):
    response = admin_client.patch(
        "/catalog/products/999999", json={"name": "Does Not Exist"}
    )

    assert response.status_code == 404


def test_inactive_product_hidden(admin_client, client):
    create_response = admin_client.post(
        "/catalog/products",
        json={**product_payload(), "slug": "inactive-product", "is_active": False},
    )

    assert create_response.status_code == 201

    response = client.get("/catalog/products/inactive-product")

    assert response.status_code == 404

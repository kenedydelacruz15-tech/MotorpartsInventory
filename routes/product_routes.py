from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from routes.user_routes import role_required
from database import get_db_connection


# Creates the Blueprint for product management.
product_bp = Blueprint(
    "products",
    __name__,
    url_prefix="/api/products"
)


# Gets all products belonging to the logged-in user's store.
@product_bp.route("/", methods=["GET"])
@jwt_required()
def get_products():

    # Gets the logged-in user's role and store ID from the JWT token.
    claims = get_jwt()
    user_role = claims.get("role")
    store_id = claims.get("store_id")

    # Prevents the system ADMIN from managing store products.
    if user_role == "ADMIN":
        return jsonify({
            "error": "ADMIN does not manage store products."
        }), 403

    # Prevents access when the user is not assigned to a store.
    if not store_id:
        return jsonify({
            "error": "Your account is not assigned to a store."
        }), 400

    # Gets optional search and filter values from the URL.
    search = request.args.get("search", "").strip()
    category_id = request.args.get("category_id", "").strip()

    connection = None
    cursor = None

    try:

        # Gets a database connection from the connection pool.
        connection = get_db_connection()

        # Creates a cursor that returns rows as dictionaries.
        cursor = connection.cursor(dictionary=True)

        # Gets products and their category names from the user's store.
        sql = """
            SELECT
                p.product_id,
                p.product_name,
                p.sku,
                p.part_number,
                p.brand,
                p.category_id,
                c.category_name,
                p.selling_price,
                p.reorder_level,
                p.description,
                p.store_id,
                p.created_at
            FROM products p
            INNER JOIN categories c
                ON p.category_id = c.category_id
            WHERE p.store_id = %s
        """

        params = [store_id]

        # Searches products using multiple important product fields.
        if search:
            sql += """
                AND (
                    p.product_name LIKE %s
                    OR p.sku LIKE %s
                    OR p.part_number LIKE %s
                    OR p.brand LIKE %s
                    OR c.category_name LIKE %s
                )
            """

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value,
                search_value,
                search_value,
                search_value
            ])

        # Filters products by category when a category ID is provided.
        if category_id:
            sql += " AND p.category_id = %s"
            params.append(category_id)

        # Shows the newest products first.
        sql += " ORDER BY p.product_id DESC"

        # Executes the product query.
        cursor.execute(sql, tuple(params))

        products = cursor.fetchall()

        return jsonify(products), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        # Closes the database cursor.
        if cursor:
            cursor.close()

        # Returns the database connection to the pool.
        if connection:
            connection.close()


# Gets one product belonging to the logged-in user's store.
@product_bp.route("/<int:product_id>", methods=["GET"])
@jwt_required()
def get_product(product_id):

    # Gets the logged-in user's role and store ID from the JWT token.
    claims = get_jwt()
    user_role = claims.get("role")
    store_id = claims.get("store_id")

    # Prevents the system ADMIN from accessing store products.
    if user_role == "ADMIN":
        return jsonify({
            "error": "ADMIN does not manage store products."
        }), 403

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a cursor that returns rows as dictionaries.
        cursor = connection.cursor(dictionary=True)

        # Gets the product only when it belongs to the user's store.
        cursor.execute("""
            SELECT
                p.product_id,
                p.product_name,
                p.sku,
                p.part_number,
                p.brand,
                p.category_id,
                c.category_name,
                p.selling_price,
                p.reorder_level,
                p.description,
                p.store_id,
                p.created_at
            FROM products p
            INNER JOIN categories c
                ON p.category_id = c.category_id
            WHERE p.product_id = %s
            AND p.store_id = %s
        """, (
            product_id,
            store_id
        ))

        product = cursor.fetchone()

        # Returns an error when the product does not belong to the store.
        if not product:
            return jsonify({
                "error": "Product not found."
            }), 404

        return jsonify(product), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        # Closes the database cursor.
        if cursor:
            cursor.close()

        # Returns the database connection to the pool.
        if connection:
            connection.close()


# Allows the OWNER to create a product in their store.
@product_bp.route("/", methods=["POST"])
@role_required("OWNER")
def create_product():

    # Gets the JSON data sent by the OWNER.
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required."
        }), 400

    # Gets and cleans the required product information.
    product_name = data.get("product_name", "").strip()
    sku = data.get("sku", "").strip()
    category_id = data.get("category_id")

    # Gets the optional product information.
    part_number = data.get("part_number", "").strip()
    brand = data.get("brand", "").strip()
    description = data.get("description", "").strip()

    # Gets the product price and reorder level.
    selling_price = data.get("selling_price", 0)
    reorder_level = data.get("reorder_level", 10)

    # Requires the important product fields.
    if not product_name or not sku or not category_id:
        return jsonify({
            "error": "Product name, SKU, and category are required."
        }), 400

    # Checks that the selling price is valid.
    try:
        selling_price = float(selling_price)

        if selling_price < 0:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Selling price must be a valid positive number."
        }), 400

    # Checks that the reorder level is valid.
    try:
        reorder_level = int(reorder_level)

        if reorder_level < 0:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Reorder level must be a valid positive number."
        }), 400

    # Gets the OWNER's store ID from the JWT token.
    store_id = get_jwt().get("store_id")

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a cursor that returns rows as dictionaries.
        cursor = connection.cursor(dictionary=True)

        # Checks whether the selected category belongs to the OWNER's store.
        cursor.execute("""
            SELECT category_id
            FROM categories
            WHERE category_id = %s
            AND store_id = %s
            AND is_active = TRUE
        """, (
            category_id,
            store_id
        ))

        category = cursor.fetchone()

        # Prevents using a category from another store.
        if not category:
            return jsonify({
                "error": "Category not found or does not belong to your store."
            }), 400

        # Checks whether the SKU already exists in the same store.
        cursor.execute("""
            SELECT product_id
            FROM products
            WHERE sku = %s
            AND store_id = %s
        """, (
            sku,
            store_id
        ))

        existing_product = cursor.fetchone()

        # Prevents duplicate SKUs inside the same store.
        if existing_product:
            return jsonify({
                "error": "SKU already exists in your store."
            }), 409

        # Closes the dictionary cursor.
        cursor.close()

        # Creates a normal cursor for inserting the product.
        cursor = connection.cursor()

        # Inserts the product into the OWNER's store.
        cursor.execute("""
            INSERT INTO products (
                product_name,
                sku,
                part_number,
                brand,
                category_id,
                selling_price,
                reorder_level,
                description,
                store_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            product_name,
            sku,
            part_number if part_number else None,
            brand if brand else None,
            category_id,
            selling_price,
            reorder_level,
            description if description else None,
            store_id
        ))

        # Gets the ID of the newly created product.
        product_id = cursor.lastrowid

        # Creates the inventory record with zero stock.
        cursor.execute("""
            INSERT INTO inventory (
                product_id,
                stock_quantity,
                store_id
            )
            VALUES (%s, 0, %s)
        """, (
            product_id,
            store_id
        ))

        # Saves the product and inventory record.
        connection.commit()

        return jsonify({
            "message": "Product created successfully.",
            "product_id": product_id
        }), 201

    except Exception as e:

        # Cancels unfinished database changes.
        if connection:
            connection.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        # Closes the database cursor.
        if cursor:
            cursor.close()

        # Returns the database connection to the pool.
        if connection:
            connection.close()


# Allows the OWNER to update a product belonging to their store.
@product_bp.route("/<int:product_id>", methods=["PUT"])
@role_required("OWNER")
def update_product(product_id):

    # Gets the JSON data sent by the OWNER.
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required."
        }), 400

    # Gets the updated product information.
    product_name = data.get("product_name", "").strip()
    sku = data.get("sku", "").strip()
    category_id = data.get("category_id")

    # Gets the optional updated product information.
    part_number = data.get("part_number", "").strip()
    brand = data.get("brand", "").strip()
    description = data.get("description", "").strip()

    # Gets the updated price and reorder level.
    selling_price = data.get("selling_price", 0)
    reorder_level = data.get("reorder_level", 10)

    # Requires the important product fields.
    if not product_name or not sku or not category_id:
        return jsonify({
            "error": "Product name, SKU, and category are required."
        }), 400

    # Checks that the selling price is valid.
    try:
        selling_price = float(selling_price)

        if selling_price < 0:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Selling price must be a valid positive number."
        }), 400

    # Checks that the reorder level is valid.
    try:
        reorder_level = int(reorder_level)

        if reorder_level < 0:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Reorder level must be a valid positive number."
        }), 400

    # Gets the OWNER's store ID from the JWT token.
    store_id = get_jwt().get("store_id")

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Checks whether the product belongs to the OWNER's store.
        cursor.execute("""
            SELECT product_id
            FROM products
            WHERE product_id = %s
            AND store_id = %s
        """, (
            product_id,
            store_id
        ))

        product = cursor.fetchone()

        # Prevents updating a product from another store.
        if not product:
            return jsonify({
                "error": "Product not found in your store."
            }), 404

        # Checks whether the selected category belongs to the same store.
        cursor.execute("""
            SELECT category_id
            FROM categories
            WHERE category_id = %s
            AND store_id = %s
            AND is_active = TRUE
        """, (
            category_id,
            store_id
        ))

        category = cursor.fetchone()

        # Prevents assigning the product to another store's category.
        if not category:
            return jsonify({
                "error": "Category not found in your store."
            }), 400

        # Checks for duplicate SKUs inside the same store.
        cursor.execute("""
            SELECT product_id
            FROM products
            WHERE sku = %s
            AND store_id = %s
            AND product_id != %s
        """, (
            sku,
            store_id,
            product_id
        ))

        duplicate_sku = cursor.fetchone()

        # Prevents duplicate SKUs.
        if duplicate_sku:
            return jsonify({
                "error": "SKU already exists in your store."
            }), 409

        # Closes the dictionary cursor.
        cursor.close()

        # Creates a normal cursor.
        cursor = connection.cursor()

        # Updates the product.
        cursor.execute("""
            UPDATE products
            SET
                product_name = %s,
                sku = %s,
                part_number = %s,
                brand = %s,
                category_id = %s,
                selling_price = %s,
                reorder_level = %s,
                description = %s
            WHERE product_id = %s
            AND store_id = %s
        """, (
            product_name,
            sku,
            part_number if part_number else None,
            brand if brand else None,
            category_id,
            selling_price,
            reorder_level,
            description if description else None,
            product_id,
            store_id
        ))

        # Saves the updated product.
        connection.commit()

        return jsonify({
            "message": "Product updated successfully."
        }), 200

    except Exception as e:

        # Cancels unfinished database changes.
        if connection:
            connection.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        # Closes the database cursor.
        if cursor:
            cursor.close()

        # Returns the database connection to the pool.
        if connection:
            connection.close()


# Allows the OWNER to permanently delete a product from their store.
@product_bp.route("/<int:product_id>", methods=["DELETE"])
@role_required("OWNER")
def delete_product(product_id):

    # Gets the OWNER's store ID from the JWT token.
    store_id = get_jwt().get("store_id")

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a database cursor.
        cursor = connection.cursor()

        # Deletes the product only when it belongs to the OWNER's store.
        cursor.execute("""
            DELETE FROM products
            WHERE product_id = %s
            AND store_id = %s
        """, (
            product_id,
            store_id
        ))

        # Returns an error when the product does not exist in the store.
        if cursor.rowcount == 0:
            return jsonify({
                "error": "Product not found in your store."
            }), 404

        # Saves the deletion.
        connection.commit()

        return jsonify({
            "message": "Product deleted successfully."
        }), 200

    except Exception as e:

        # Cancels unfinished database changes.
        if connection:
            connection.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        # Closes the database cursor.
        if cursor:
            cursor.close()

        # Returns the connection to the pool.
        if connection:
            connection.close()
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt

from routes.user_routes import role_required
from database import get_db_connection


# Creates the Blueprint for stock-in operations.
stock_in_bp = Blueprint(
    "stock_in",
    __name__,
    url_prefix="/api/stock-in"
)


# Adds stock to a product and records the movement.
@stock_in_bp.route("/", methods=["POST"])
@role_required("OWNER", "STAFF")
def create_stock_in():

    # Gets the JSON data sent by the user.
    data = request.get_json()

    # Stops the request when no JSON body was provided.
    if not data:
        return jsonify({
            "error": "Request body is required."
        }), 400

    # Gets the product ID.
    product_id = data.get("product_id")

    # Gets the quantity being added.
    quantity = data.get("quantity")

    # Gets the optional supplier ID.
    supplier_id = data.get("supplier_id")

    # Gets the optional reference number.
    reference_number = data.get("reference_number", "").strip()

    # Gets the optional remarks.
    remarks = data.get("remarks", "").strip()

    # Requires a product ID and quantity.
    if not product_id or quantity is None:
        return jsonify({
            "error": "Product ID and quantity are required."
        }), 400

    # Validates the product ID.
    try:
        product_id = int(product_id)

        if product_id <= 0:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Product ID must be a valid number."
        }), 400

    # Validates the quantity.
    try:
        quantity = int(quantity)

        if quantity <= 0:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Quantity must be greater than zero."
        }), 400

    # Validates the supplier ID when a supplier was provided.
    if supplier_id is not None:

        try:
            supplier_id = int(supplier_id)

            if supplier_id <= 0:
                raise ValueError

        except (ValueError, TypeError):
            return jsonify({
                "error": "Supplier ID must be a valid number."
            }), 400

    # Gets the logged-in user's store ID from the JWT token.
    store_id = get_jwt().get("store_id")

    # Prevents stock transactions when the user has no assigned store.
    if not store_id:
        return jsonify({
            "error": "You are not assigned to a store."
        }), 403

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Starts a database transaction.
        connection.start_transaction()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Checks whether the product belongs to the logged-in user's store.
        cursor.execute("""
            SELECT product_id, product_name
            FROM products
            WHERE product_id = %s
            AND store_id = %s
        """, (
            product_id,
            store_id
        ))

        # Gets the product.
        product = cursor.fetchone()

        # Stops the transaction when the product belongs to another store
        # or does not exist.
        if not product:
            connection.rollback()

            return jsonify({
                "error": "Product not found in your store."
            }), 404

        # Checks whether the selected supplier belongs to the same store.
        # This is only checked when a supplier ID was provided.
        if supplier_id is not None:

            cursor.execute("""
                SELECT supplier_id, supplier_name
                FROM suppliers
                WHERE supplier_id = %s
                AND store_id = %s
                AND deleted_at IS NULL
            """, (
                supplier_id,
                store_id
            ))

            # Gets the supplier.
            supplier = cursor.fetchone()

            # Prevents Store A from using a supplier belonging to Store B.
            if not supplier:
                connection.rollback()

                return jsonify({
                    "error": "Supplier not found or does not belong to your store."
                }), 404

        # Gets the current inventory quantity.
        cursor.execute("""
            SELECT inventory_id, stock_quantity
            FROM inventory
            WHERE product_id = %s
            AND store_id = %s
        """, (
            product_id,
            store_id
        ))

        # Gets the inventory record.
        inventory = cursor.fetchone()

        # Stops when the inventory record does not exist.
        if not inventory:
            connection.rollback()

            return jsonify({
                "error": "Inventory record not found for this product."
            }), 404

        # Stores the quantity before the stock-in transaction.
        previous_quantity = inventory["stock_quantity"]

        # Calculates the new quantity.
        new_quantity = previous_quantity + quantity

        # Closes the dictionary cursor.
        cursor.close()
        cursor = None

        # Creates a normal cursor.
        cursor = connection.cursor()

        # Records the stock-in transaction.
        cursor.execute("""
            INSERT INTO stock_in (
                product_id,
                quantity,
                supplier_id,
                reference_number,
                remarks,
                store_id
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            product_id,
            quantity,
            supplier_id,
            reference_number if reference_number else None,
            remarks if remarks else None,
            store_id
        ))

        # Gets the ID of the stock-in transaction.
        stock_in_id = cursor.lastrowid

        # Updates the current inventory quantity.
        cursor.execute("""
            UPDATE inventory
            SET stock_quantity = %s
            WHERE product_id = %s
            AND store_id = %s
        """, (
            new_quantity,
            product_id,
            store_id
        ))

        # Records the transaction in stock movement history.
        cursor.execute("""
            INSERT INTO stock_movements (
                product_id,
                movement_type,
                quantity,
                previous_quantity,
                new_quantity,
                reference_type,
                reference_id,
                remarks,
                store_id
            )
            VALUES (
                %s,
                'STOCK_IN',
                %s,
                %s,
                %s,
                'STOCK_IN',
                %s,
                %s,
                %s
            )
        """, (
            product_id,
            quantity,
            previous_quantity,
            new_quantity,
            stock_in_id,
            remarks if remarks else None,
            store_id
        ))

        # Saves all database changes permanently.
        connection.commit()

        return jsonify({
            "message": "Stock added successfully.",
            "stock_in_id": stock_in_id,
            "product_id": product_id,
            "supplier_id": supplier_id,
            "previous_quantity": previous_quantity,
            "added_quantity": quantity,
            "new_quantity": new_quantity
        }), 201

    except Exception as e:

        # Cancels all database changes when an unexpected error occurs.
        if connection:
            connection.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        # Closes the database cursor.
        if cursor:
            cursor.close()

        # Returns the database connection.
        if connection:
            connection.close()
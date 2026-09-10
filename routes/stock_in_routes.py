from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt

from routes.user_routes import role_required
from database import get_db_connection


stock_in_bp = Blueprint(
    "stock_in",
    __name__,
    url_prefix="/api/stock-in"
)


@stock_in_bp.route("/", methods=["POST"])
@role_required("OWNER", "STAFF")
def create_stock_in():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required."
        }), 400

    product_id = data.get("product_id")
    quantity = data.get("quantity")
    supplier_id = data.get("supplier_id")

    if not product_id or quantity is None:
        return jsonify({
            "error": "Product ID and quantity are required."
        }), 400

    try:
        product_id = int(product_id)

        if product_id <= 0:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Product ID must be a valid number."
        }), 400

    try:
        quantity = int(quantity)

        if quantity <= 0:
            raise ValueError

    except (ValueError, TypeError):
        return jsonify({
            "error": "Quantity must be greater than zero."
        }), 400

    if supplier_id is not None:

        try:
            supplier_id = int(supplier_id)

            if supplier_id <= 0:
                raise ValueError

        except (ValueError, TypeError):
            return jsonify({
                "error": "Supplier ID must be a valid number."
            }), 400

    store_id = get_jwt().get("store_id")

    if not store_id:
        return jsonify({
            "error": "You are not assigned to a store."
        }), 403

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        connection.start_transaction()

        cursor = connection.cursor(dictionary=True)

        # Check product belongs to this store
        cursor.execute("""
            SELECT product_id, product_name
            FROM products
            WHERE product_id = %s
            AND store_id = %s
        """, (
            product_id,
            store_id
        ))

        product = cursor.fetchone()

        if not product:
            connection.rollback()

            return jsonify({
                "error": "Product not found in your store."
            }), 404

        # Check supplier belongs to this store
        if supplier_id is not None:

            cursor.execute("""
                SELECT supplier_id, supplier_name
                FROM suppliers
                WHERE supplier_id = %s
                AND store_id = %s
            """, (
                supplier_id,
                store_id
            ))

            supplier = cursor.fetchone()

            if not supplier:
                connection.rollback()

                return jsonify({
                    "error": "Supplier not found or does not belong to your store."
                }), 404

        # Get current inventory
        cursor.execute("""
            SELECT inventory_id, stock_quantity
            FROM inventory
            WHERE product_id = %s
            AND store_id = %s
            FOR UPDATE
        """, (
            product_id,
            store_id
        ))

        inventory = cursor.fetchone()

        if not inventory:
            connection.rollback()

            return jsonify({
                "error": "Inventory record not found for this product."
            }), 404

        previous_quantity = inventory["stock_quantity"]
        new_quantity = previous_quantity + quantity

        cursor.close()
        cursor = connection.cursor()

        # Insert stock-in record
        cursor.execute("""
            INSERT INTO stock_in (
                product_id,
                quantity,
                supplier_id,
                store_id
            )
            VALUES (%s, %s, %s, %s)
        """, (
            product_id,
            quantity,
            supplier_id,
            store_id
        ))

        stock_in_id = cursor.lastrowid

        # Update inventory
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

        # Record stock movement
        cursor.execute("""
            INSERT INTO stock_movements (
                product_id,
                movement_type,
                quantity,
                previous_quantity,
                new_quantity,
                reference_id,
                store_id
            )
            VALUES (
                %s,
                'STOCK_IN',
                %s,
                %s,
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
            store_id
        ))

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

        if connection:
            connection.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()
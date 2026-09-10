from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from database import get_db_connection
from routes.user_routes import role_required


sales_bp = Blueprint("sales", __name__, url_prefix="/api/sales")


@sales_bp.route("/", methods=["POST"])
@role_required("OWNER", "STAFF")
def create_sale():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required."
        }), 400

    items = data.get("items")

    if not isinstance(items, list) or len(items) == 0:
        return jsonify({
            "error": "At least one product is required."
        }), 400

    payment_method = str(
        data.get("payment_method", "CASH")
    ).strip().upper()

    if not payment_method:
        payment_method = "CASH"

    try:
        payment_amount = Decimal(
            str(data.get("payment_amount", "0"))
        )
    except (InvalidOperation, TypeError):
        return jsonify({
            "error": "Invalid payment amount."
        }), 400

    if payment_amount < 0:
        return jsonify({
            "error": "Payment amount cannot be negative."
        }), 400

    user_id = int(get_jwt_identity())
    claims = get_jwt()

    store_id = claims.get("store_id")

    if not store_id:
        return jsonify({
            "error": "Your account is not assigned to a store."
        }), 403

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        connection.start_transaction()

        prepared_items = []
        product_ids = set()

        for item in items:

            try:
                product_id = int(item.get("product_id"))
                quantity = int(item.get("quantity"))
            except (TypeError, ValueError):
                connection.rollback()

                return jsonify({
                    "error": "Product ID and quantity must be valid numbers."
                }), 400

            if product_id in product_ids:
                connection.rollback()

                return jsonify({
                    "error": f"Product {product_id} appears more than once."
                }), 400

            product_ids.add(product_id)

            if quantity <= 0:
                connection.rollback()

                return jsonify({
                    "error": "Quantity must be greater than zero."
                }), 400

            cursor.execute("""
                SELECT
                    p.product_id,
                    p.product_name,
                    p.sku,
                    p.selling_price,
                    i.stock_quantity
                FROM products p
                INNER JOIN inventory i
                    ON i.product_id = p.product_id
                    AND i.store_id = p.store_id
                WHERE p.product_id = %s
                  AND p.store_id = %s
                FOR UPDATE
            """, (
                product_id,
                store_id
            ))

            product = cursor.fetchone()

            if not product:
                connection.rollback()

                return jsonify({
                    "error": f"Product {product_id} was not found in your store."
                }), 404

            current_stock = int(product["stock_quantity"])

            if quantity > current_stock:
                connection.rollback()

                return jsonify({
                    "error": (
                        f"Insufficient stock for "
                        f"{product['product_name']}. "
                        f"Available stock: {current_stock}."
                    )
                }), 400

            unit_price = Decimal(
                str(product["selling_price"])
            )

            subtotal = unit_price * quantity

            prepared_items.append({
                "product_id": product_id,
                "product_name": product["product_name"],
                "sku": product["sku"],
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": subtotal,
                "previous_quantity": current_stock,
                "new_quantity": current_stock - quantity
            })

        total_sales = sum(
            item["subtotal"]
            for item in prepared_items
        )

        if payment_amount < total_sales:

            connection.rollback()

            return jsonify({
                "error": "Insufficient payment.",
                "total_sales": float(total_sales),
                "payment_amount": float(payment_amount),
                "shortage": float(
                    total_sales - payment_amount
                )
            }), 400

        change_amount = payment_amount - total_sales

        cursor.execute("""
            INSERT INTO sales (
                store_id,
                user_id,
                total_sales,
                payment_amount,
                change_amount,
                payment_method
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            store_id,
            user_id,
            total_sales,
            payment_amount,
            change_amount,
            payment_method
        ))

        sale_id = cursor.lastrowid

        for item in prepared_items:

            cursor.execute("""
                INSERT INTO sale_items (
                    sale_id,
                    product_id,
                    store_id,
                    quantity,
                    unit_price,
                    subtotal
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                sale_id,
                item["product_id"],
                store_id,
                item["quantity"],
                item["unit_price"],
                item["subtotal"]
            ))

            cursor.execute("""
                UPDATE inventory
                SET stock_quantity = %s
                WHERE product_id = %s
                  AND store_id = %s
            """, (
                item["new_quantity"],
                item["product_id"],
                store_id
            ))

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
                    'SALE',
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            """, (
                item["product_id"],
                item["quantity"],
                item["previous_quantity"],
                item["new_quantity"],
                sale_id,
                store_id
            ))

        connection.commit()

        return jsonify({
            "message": "Sale completed successfully.",
            "sale": {
                "sale_id": sale_id,
                "store_id": store_id,
                "user_id": user_id,
                "total_sales": float(total_sales),
                "payment_amount": float(payment_amount),
                "change_amount": float(change_amount),
                "payment_method": payment_method,
                "items": [
                    {
                        "product_id": item["product_id"],
                        "product_name": item["product_name"],
                        "sku": item["sku"],
                        "quantity": item["quantity"],
                        "unit_price": float(item["unit_price"]),
                        "subtotal": float(item["subtotal"])
                    }
                    for item in prepared_items
                ]
            }
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


@sales_bp.route("/", methods=["GET"])
@jwt_required()
def get_sales():

    claims = get_jwt()
    role = claims.get("role")
    store_id = claims.get("store_id")

    if role == "ADMIN":
        return jsonify({
            "error": "ADMIN cannot access store sales."
        }), 403

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                s.sale_id,
                s.store_id,
                s.user_id,
                u.full_name AS cashier,
                s.total_sales,
                s.payment_amount,
                s.change_amount,
                s.payment_method,
                s.sale_date,
                s.status
            FROM sales s
            LEFT JOIN users u
                ON u.user_id = s.user_id
            WHERE s.store_id = %s
            ORDER BY s.sale_date DESC
        """, (
            store_id,
        ))

        sales = cursor.fetchall()

        for sale in sales:

            sale["total_sales"] = float(
                sale["total_sales"]
            )

            sale["payment_amount"] = float(
                sale["payment_amount"]
            )

            sale["change_amount"] = float(
                sale["change_amount"]
            )

        return jsonify({
            "sales": sales
        }), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


@sales_bp.route("/<int:sale_id>", methods=["GET"])
@jwt_required()
def get_sale(sale_id):

    claims = get_jwt()
    role = claims.get("role")
    store_id = claims.get("store_id")

    if role == "ADMIN":
        return jsonify({
            "error": "ADMIN cannot access store sales."
        }), 403

    connection = None
    cursor = None

    try:
        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                s.sale_id,
                s.store_id,
                s.user_id,
                u.full_name AS cashier,
                s.total_sales,
                s.payment_amount,
                s.change_amount,
                s.payment_method,
                s.sale_date,
                s.status
            FROM sales s
            LEFT JOIN users u
                ON u.user_id = s.user_id
            WHERE s.sale_id = %s
              AND s.store_id = %s
        """, (
            sale_id,
            store_id
        ))

        sale = cursor.fetchone()

        if not sale:
            return jsonify({
                "error": "Sale not found."
            }), 404

        cursor.execute("""
            SELECT
                si.sale_item_id,
                si.product_id,
                p.product_name,
                p.sku,
                si.quantity,
                si.unit_price,
                si.subtotal
            FROM sale_items si
            INNER JOIN products p
                ON p.product_id = si.product_id
            WHERE si.sale_id = %s
              AND si.store_id = %s
            ORDER BY si.sale_item_id
        """, (
            sale_id,
            store_id
        ))

        items = cursor.fetchall()

        sale["total_sales"] = float(
            sale["total_sales"]
        )

        sale["payment_amount"] = float(
            sale["payment_amount"]
        )

        sale["change_amount"] = float(
            sale["change_amount"]
        )

        for item in items:

            item["unit_price"] = float(
                item["unit_price"]
            )

            item["subtotal"] = float(
                item["subtotal"]
            )

        sale["items"] = items

        return jsonify({
            "sale": sale
        }), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()

@sales_bp.route(
    "/<int:sale_id>/void",
    methods=["PUT"]
)
@role_required("OWNER")
def void_sale(sale_id):

    store_id = get_jwt().get("store_id")

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # Lock the sale
        cursor.execute("""
            SELECT
                sale_id,
                status
            FROM sales
            WHERE sale_id = %s
            AND store_id = %s
            FOR UPDATE
        """, (
            sale_id,
            store_id
        ))

        sale = cursor.fetchone()

        if not sale:

            return jsonify({
                "error": "Sale not found."
            }), 404

        if sale["status"] == "VOIDED":

            return jsonify({
                "error": "Sale is already voided."
            }), 400

        # Get sale items
        cursor.execute("""
            SELECT
                sale_item_id,
                product_id,
                quantity
            FROM sale_items
            WHERE sale_id = %s
            AND store_id = %s
        """, (
            sale_id,
            store_id
        ))

        items = cursor.fetchall()

        if not items:

            return jsonify({
                "error": "Sale has no items."
            }), 400

        # ---------------------------------------------
        # RESTORE INVENTORY
        # ---------------------------------------------
        for item in items:

            cursor.execute("""
                SELECT
                    inventory_id,
                    stock_quantity
                FROM inventory
                WHERE product_id = %s
                AND store_id = %s
                FOR UPDATE
            """, (
                item["product_id"],
                store_id
            ))

            inventory = cursor.fetchone()

            if not inventory:

                connection.rollback()

                return jsonify({
                    "error":
                        f"Inventory record not found for product {item['product_id']}."
                }), 400

            previous_quantity = inventory[
                "stock_quantity"
            ]

            new_quantity = (
                previous_quantity
                + item["quantity"]
            )

            cursor.execute("""
                UPDATE inventory
                SET stock_quantity = %s
                WHERE inventory_id = %s
                AND store_id = %s
            """, (
                new_quantity,
                inventory["inventory_id"],
                store_id
            ))

            # -----------------------------------------
            # STOCK MOVEMENT
            # -----------------------------------------
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
                item["product_id"],
                item["quantity"],
                previous_quantity,
                new_quantity,
                sale_id,
                store_id
            ))

        # ---------------------------------------------
        # VOID SALE
        # ---------------------------------------------
        cursor.execute("""
            UPDATE sales
            SET status = 'VOIDED'
            WHERE sale_id = %s
            AND store_id = %s
        """, (
            sale_id,
            store_id
        ))

        connection.commit()

        return jsonify({
            "message": "Sale voided successfully and inventory restored."
        }), 200

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
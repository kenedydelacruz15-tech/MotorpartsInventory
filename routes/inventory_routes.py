from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from routes.user_routes import role_required
from database import get_db_connection


inventory_bp = Blueprint(
    "inventory",
    __name__,
    url_prefix="/api/inventory"
)


# =========================================================
# GET INVENTORY
# =========================================================
@inventory_bp.route("/", methods=["GET"])
@jwt_required()
def get_inventory():

    claims = get_jwt()

    role = claims.get("role")
    store_id = claims.get("store_id")

    if role == "ADMIN":
        return jsonify({
            "error": "ADMIN does not manage store inventory."
        }), 403

    if not store_id:
        return jsonify({
            "error": "Your account is not assigned to a store."
        }), 400

    search = request.args.get(
        "search",
        ""
    ).strip()

    status = request.args.get(
        "status",
        "active"
    ).strip().lower()

    if status not in [
        "active",
        "inactive",
        "all"
    ]:
        status = "active"

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        sql = """
            SELECT
                i.inventory_id,
                i.product_id,
                p.product_name,
                p.sku,
                p.part_number,
                p.brand,
                p.selling_price,
                p.reorder_level,
                c.category_id,
                c.category_name,
                i.stock_quantity,
                i.is_active,
                i.store_id,
                i.updated_at
            FROM inventory i

            INNER JOIN products p
                ON i.product_id = p.product_id

            INNER JOIN categories c
                ON p.category_id = c.category_id

            WHERE i.store_id = %s
        """

        params = [store_id]

        if status == "active":

            sql += """
                AND i.is_active = 1
                AND p.is_active = 1
            """

        elif status == "inactive":

            sql += """
                AND i.is_active = 0
            """

        if search:

            sql += """
                AND (
                    p.product_name LIKE %s
                    OR p.sku LIKE %s
                    OR p.brand LIKE %s
                    OR c.category_name LIKE %s
                )
            """

            value = f"%{search}%"

            params.extend([
                value,
                value,
                value,
                value
            ])

        sql += """
            ORDER BY i.inventory_id DESC
        """

        cursor.execute(
            sql,
            tuple(params)
        )

        inventory = cursor.fetchall()

        return jsonify(inventory), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# GET SINGLE INVENTORY
# =========================================================
@inventory_bp.route(
    "/<int:inventory_id>",
    methods=["GET"]
)
@jwt_required()
def get_inventory_item(inventory_id):

    claims = get_jwt()

    role = claims.get("role")
    store_id = claims.get("store_id")

    if role == "ADMIN":

        return jsonify({
            "error": "ADMIN does not manage store inventory."
        }), 403

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute("""
            SELECT
                i.inventory_id,
                i.product_id,
                p.product_name,
                p.sku,
                p.part_number,
                p.brand,
                p.selling_price,
                p.reorder_level,
                c.category_id,
                c.category_name,
                i.stock_quantity,
                i.is_active,
                i.store_id,
                i.updated_at
            FROM inventory i

            INNER JOIN products p
                ON i.product_id = p.product_id

            INNER JOIN categories c
                ON p.category_id = c.category_id

            WHERE i.inventory_id = %s
            AND i.store_id = %s
        """, (
            inventory_id,
            store_id
        ))

        item = cursor.fetchone()

        if not item:

            return jsonify({
                "error": "Inventory record not found."
            }), 404

        return jsonify(item), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =========================================================
# UPDATE INVENTORY
# OWNER ONLY
# =========================================================
@inventory_bp.route(
    "/<int:inventory_id>",
    methods=["PUT"]
)
@role_required("OWNER")
def update_inventory(inventory_id):

    data = request.get_json()

    if not data:

        return jsonify({
            "error": "Request body is required."
        }), 400

    try:

        stock_quantity = int(
            data.get("stock_quantity")
        )

        if stock_quantity < 0:

            raise ValueError

    except (ValueError, TypeError):

        return jsonify({
            "error": "Stock quantity must be a valid non-negative number."
        }), 400

    store_id = get_jwt().get(
        "store_id"
    )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute("""
            SELECT
                inventory_id,
                product_id,
                stock_quantity,
                is_active
            FROM inventory
            WHERE inventory_id = %s
            AND store_id = %s
        """, (
            inventory_id,
            store_id
        ))

        item = cursor.fetchone()

        if not item:

            return jsonify({
                "error": "Inventory record not found."
            }), 404

        previous_quantity = item[
            "stock_quantity"
        ]

        cursor.close()

        cursor = connection.cursor()

        cursor.execute("""
            UPDATE inventory
            SET stock_quantity = %s
            WHERE inventory_id = %s
            AND store_id = %s
        """, (
            stock_quantity,
            inventory_id,
            store_id
        ))

        connection.commit()

        return jsonify({
            "message": "Inventory updated successfully.",
            "previous_quantity":
                previous_quantity,
            "new_quantity":
                stock_quantity
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


# =========================================================
# SOFT DELETE INVENTORY
# =========================================================
@inventory_bp.route(
    "/<int:inventory_id>/deactivate",
    methods=["PUT"]
)
@role_required("OWNER")
def deactivate_inventory(inventory_id):

    store_id = get_jwt().get(
        "store_id"
    )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute("""
            SELECT
                inventory_id,
                product_id,
                stock_quantity,
                is_active
            FROM inventory
            WHERE inventory_id = %s
            AND store_id = %s
        """, (
            inventory_id,
            store_id
        ))

        item = cursor.fetchone()

        if not item:

            return jsonify({
                "error": "Inventory record not found."
            }), 404

        if item["is_active"] == 0:

            return jsonify({
                "error": "Inventory record is already in Trash."
            }), 400

        # Prevent hiding inventory that still has stock
        if item["stock_quantity"] > 0:

            return jsonify({
                "error": "Cannot move inventory to Trash while stock quantity is greater than 0."
            }), 400

        cursor.execute("""
            UPDATE inventory
            SET is_active = 0
            WHERE inventory_id = %s
            AND store_id = %s
        """, (
            inventory_id,
            store_id
        ))

        connection.commit()

        return jsonify({
            "message": "Inventory record moved to Trash."
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


# =========================================================
# RESTORE INVENTORY
# =========================================================
@inventory_bp.route(
    "/<int:inventory_id>/restore",
    methods=["PUT"]
)
@role_required("OWNER")
def restore_inventory(inventory_id):

    store_id = get_jwt().get(
        "store_id"
    )

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute("""
            UPDATE inventory
            SET is_active = 1
            WHERE inventory_id = %s
            AND store_id = %s
            AND is_active = 0
        """, (
            inventory_id,
            store_id
        ))

        if cursor.rowcount == 0:

            return jsonify({
                "error": "Inventory record not found or already active."
            }), 404

        connection.commit()

        return jsonify({
            "message": "Inventory restored successfully."
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
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from database import get_db_connection


# Creates the Blueprint for stock movement history.
stock_movement_bp = Blueprint(
    "stock_movements",
    __name__,
    url_prefix="/api/stock-movements"
)


# Gets all stock movements belonging to the logged-in user's store.
@stock_movement_bp.route("/", methods=["GET"])
@jwt_required()
def get_stock_movements():

    # Gets the logged-in user's JWT information.
    claims = get_jwt()

    # Gets the logged-in user's role.
    user_role = claims.get("role")

    # Gets the logged-in user's store ID.
    store_id = claims.get("store_id")

    # Prevents ADMIN from accessing store movements.
    if user_role == "ADMIN":
        return jsonify({
            "error": "ADMIN does not manage store stock movements."
        }), 403

    # Prevents users without a store from viewing movements.
    if not store_id:
        return jsonify({
            "error": "You are not assigned to a store."
        }), 403

    # Gets the search keyword.
    search = request.args.get("search", "").strip()

    # Gets the product ID filter.
    product_id = request.args.get("product_id", "").strip()

    # Gets the movement type filter.
    movement_type = request.args.get(
        "movement_type",
        ""
    ).strip().upper()

    # Gets the reason filter.
    reference_type = request.args.get(
        "reference_type",
        ""
    ).strip().upper()

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Creates the stock movement query.
        sql = """
            SELECT
                sm.movement_id,
                sm.product_id,
                p.product_name,
                p.sku,
                p.part_number,
                p.brand,
                sm.movement_type,
                sm.quantity,
                sm.previous_quantity,
                sm.new_quantity,
                sm.reference_type,
                sm.reference_id,
                sm.remarks,
                sm.store_id,
                sm.created_at
            FROM stock_movements sm
            INNER JOIN products p
                ON sm.product_id = p.product_id
                AND sm.store_id = p.store_id
            WHERE sm.store_id = %s
        """

        # Stores the SQL parameters.
        params = [store_id]

        # Searches product and movement information.
        if search:

            sql += """
                AND (
                    p.product_name LIKE %s
                    OR p.sku LIKE %s
                    OR p.part_number LIKE %s
                    OR p.brand LIKE %s
                    OR sm.reference_type LIKE %s
                    OR sm.remarks LIKE %s
                )
            """

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
                search_value
            ])

        # Filters movements by product.
        if product_id:

            try:
                product_id = int(product_id)

            except ValueError:
                return jsonify({
                    "error": "Product ID must be a valid number."
                }), 400

            sql += " AND sm.product_id = %s"
            params.append(product_id)

        # Filters movements by type.
        if movement_type:

            if movement_type not in ["STOCK_IN", "STOCK_OUT"]:
                return jsonify({
                    "error": "Movement type must be STOCK_IN or STOCK_OUT."
                }), 400

            sql += " AND sm.movement_type = %s"
            params.append(movement_type)

        # Filters movements by reason.
        if reference_type:

            sql += " AND sm.reference_type = %s"
            params.append(reference_type)

        # Shows the newest movements first.
        sql += " ORDER BY sm.created_at DESC"

        # Executes the query.
        cursor.execute(sql, tuple(params))

        # Gets all matching movements.
        movements = cursor.fetchall()

        return jsonify(movements), 200

    except Exception as e:

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


# Gets one stock movement from the logged-in user's store.
@stock_movement_bp.route("/<int:movement_id>", methods=["GET"])
@jwt_required()
def get_stock_movement(movement_id):

    # Gets the logged-in user's JWT information.
    claims = get_jwt()

    # Gets the logged-in user's role.
    user_role = claims.get("role")

    # Gets the logged-in user's store ID.
    store_id = claims.get("store_id")

    # Prevents ADMIN from accessing store movements.
    if user_role == "ADMIN":
        return jsonify({
            "error": "ADMIN does not manage store stock movements."
        }), 403

    # Prevents users without a store from viewing movements.
    if not store_id:
        return jsonify({
            "error": "You are not assigned to a store."
        }), 403

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Gets the selected movement from the correct store.
        cursor.execute("""
            SELECT
                sm.movement_id,
                sm.product_id,
                p.product_name,
                p.sku,
                p.part_number,
                p.brand,
                sm.movement_type,
                sm.quantity,
                sm.previous_quantity,
                sm.new_quantity,
                sm.reference_type,
                sm.reference_id,
                sm.remarks,
                sm.store_id,
                sm.created_at
            FROM stock_movements sm
            INNER JOIN products p
                ON sm.product_id = p.product_id
                AND sm.store_id = p.store_id
            WHERE sm.movement_id = %s
            AND sm.store_id = %s
        """, (
            movement_id,
            store_id
        ))

        # Gets the selected movement.
        movement = cursor.fetchone()

        # Returns an error when the movement does not exist.
        if not movement:
            return jsonify({
                "error": "Stock movement not found."
            }), 404

        return jsonify(movement), 200

    except Exception as e:

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
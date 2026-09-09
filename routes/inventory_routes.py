from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from database import get_db_connection


# Creates the Blueprint for inventory management.
inventory_bp = Blueprint(
    "inventory",
    __name__,
    url_prefix="/api/inventory"
)


# Gets all inventory records belonging to the logged-in user's store.
@inventory_bp.route("/", methods=["GET"])
@jwt_required()
def get_inventory():

    # Gets the logged-in user's role and store ID from the JWT token.
    claims = get_jwt()
    user_role = claims.get("role")
    store_id = claims.get("store_id")

    # Prevents the system ADMIN from managing store inventory.
    if user_role == "ADMIN":
        return jsonify({
            "error": "ADMIN does not manage store inventory."
        }), 403

    # Prevents access when the user is not assigned to a store.
    if not store_id:
        return jsonify({
            "error": "Your account is not assigned to a store."
        }), 400

    # Gets the optional search value.
    search = request.args.get("search", "").strip()

    # Gets the optional category filter.
    category_id = request.args.get("category_id", "").strip()

    # Gets the optional stock status filter.
    stock_status = request.args.get("stock_status", "").strip().lower()

    connection = None
    cursor = None

    try:

        # Gets a database connection from the connection pool.
        connection = get_db_connection()

        # Creates a cursor that returns database rows as dictionaries.
        cursor = connection.cursor(dictionary=True)

        # Gets inventory together with product and category information.
        sql = """
            SELECT
                i.inventory_id,
                i.product_id,
                p.product_name,
                p.sku,
                p.part_number,
                p.brand,
                p.category_id,
                c.category_name,
                p.selling_price,
                p.reorder_level,
                i.stock_quantity,
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

        # Searches inventory using important product information.
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

        # Filters inventory by category.
        if category_id:

            sql += """
                AND p.category_id = %s
            """

            params.append(category_id)

        # Shows only products with zero stock.
        if stock_status == "out_of_stock":

            sql += """
                AND i.stock_quantity = 0
            """

        # Shows products that reached or passed their reorder level.
        elif stock_status == "low_stock":

            sql += """
                AND i.stock_quantity > 0
                AND i.stock_quantity <= p.reorder_level
            """

        # Shows products with stock above their reorder level.
        elif stock_status == "in_stock":

            sql += """
                AND i.stock_quantity > p.reorder_level
            """

        # Shows the inventory alphabetically by product name.
        sql += """
            ORDER BY p.product_name ASC
        """

        # Executes the inventory query.
        cursor.execute(sql, tuple(params))

        inventory = cursor.fetchall()

        return jsonify(inventory), 200

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


# Gets one inventory record belonging to the logged-in user's store.
@inventory_bp.route("/<int:product_id>", methods=["GET"])
@jwt_required()
def get_inventory_product(product_id):

    # Gets the logged-in user's role and store ID from the JWT token.
    claims = get_jwt()
    user_role = claims.get("role")
    store_id = claims.get("store_id")

    # Prevents the system ADMIN from accessing store inventory.
    if user_role == "ADMIN":
        return jsonify({
            "error": "ADMIN does not manage store inventory."
        }), 403

    # Prevents access when the user is not assigned to a store.
    if not store_id:
        return jsonify({
            "error": "Your account is not assigned to a store."
        }), 400

    connection = None
    cursor = None

    try:

        # Gets a database connection from the connection pool.
        connection = get_db_connection()

        # Creates a cursor that returns rows as dictionaries.
        cursor = connection.cursor(dictionary=True)

        # Gets the inventory record only when it belongs to the user's store.
        cursor.execute("""
            SELECT
                i.inventory_id,
                i.product_id,
                p.product_name,
                p.sku,
                p.part_number,
                p.brand,
                p.category_id,
                c.category_name,
                p.selling_price,
                p.reorder_level,
                i.stock_quantity,
                i.store_id,
                i.updated_at
            FROM inventory i
            INNER JOIN products p
                ON i.product_id = p.product_id
            INNER JOIN categories c
                ON p.category_id = c.category_id
            WHERE i.product_id = %s
            AND i.store_id = %s
        """, (
            product_id,
            store_id
        ))

        inventory = cursor.fetchone()

        # Returns an error when the product inventory does not exist.
        if not inventory:
            return jsonify({
                "error": "Inventory record not found."
            }), 404

        return jsonify(inventory), 200

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


# Gets a summary of the logged-in store's inventory.
@inventory_bp.route("/summary", methods=["GET"])
@jwt_required()
def get_inventory_summary():

    # Gets the logged-in user's role and store ID from the JWT token.
    claims = get_jwt()
    user_role = claims.get("role")
    store_id = claims.get("store_id")

    # Prevents the system ADMIN from viewing store inventory summaries.
    if user_role == "ADMIN":
        return jsonify({
            "error": "ADMIN does not manage store inventory."
        }), 403

    # Prevents access when the user is not assigned to a store.
    if not store_id:
        return jsonify({
            "error": "Your account is not assigned to a store."
        }), 400

    connection = None
    cursor = None

    try:

        # Gets a database connection from the connection pool.
        connection = get_db_connection()

        # Creates a cursor that returns rows as dictionaries.
        cursor = connection.cursor(dictionary=True)

        # Calculates inventory totals for the logged-in user's store only.
        cursor.execute("""
            SELECT
                COUNT(*) AS total_products,

                COALESCE(SUM(i.stock_quantity), 0) AS total_stock,

                SUM(
                    CASE
                        WHEN i.stock_quantity = 0
                        THEN 1
                        ELSE 0
                    END
                ) AS out_of_stock,

                SUM(
                    CASE
                        WHEN i.stock_quantity > 0
                        AND i.stock_quantity <= p.reorder_level
                        THEN 1
                        ELSE 0
                    END
                ) AS low_stock,

                SUM(
                    CASE
                        WHEN i.stock_quantity > p.reorder_level
                        THEN 1
                        ELSE 0
                    END
                ) AS in_stock

            FROM inventory i

            INNER JOIN products p
                ON i.product_id = p.product_id

            WHERE i.store_id = %s
        """, (store_id,))

        summary = cursor.fetchone()

        return jsonify(summary), 200

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
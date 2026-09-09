from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from routes.user_routes import role_required
from database import get_db_connection


# Creates the Blueprint for category management.
category_bp = Blueprint(
    "categories",
    __name__,
    url_prefix="/api/categories"
)


# Gets all categories belonging to the logged-in user's store.
@category_bp.route("/", methods=["GET"])
@jwt_required()
def get_categories():

    # Gets the logged-in user's role from the JWT token.
    user_role = get_jwt().get("role")

    # Gets the logged-in user's store ID from the JWT token.
    store_id = get_jwt().get("store_id")

    # Prevents ADMIN from accessing store categories.
    if user_role == "ADMIN":
        return jsonify({
            "error": "ADMIN does not manage store categories."
        }), 403

    # Ensures the user belongs to a store.
    if not store_id:
        return jsonify({
            "error": "Your account is not assigned to a store."
        }), 400

    # Gets optional search and status filters.
    search = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip().lower()

    connection = None
    cursor = None

    try:

        # Gets a database connection from the pool.
        connection = get_db_connection()

        # Creates a cursor that returns rows as dictionaries.
        cursor = connection.cursor(dictionary=True)

        # Starts the query with categories from the user's store only.
        sql = """
            SELECT
                category_id,
                category_name,
                description,
                store_id,
                is_active,
                created_at,
                updated_at
            FROM categories
            WHERE store_id = %s
        """

        params = [store_id]

        # Filters categories using the category name or description.
        if search:
            sql += """
                AND (
                    category_name LIKE %s
                    OR description LIKE %s
                )
            """
            search_value = f"%{search}%"
            params.extend([search_value, search_value])

        # Filters active categories.
        if status == "active":
            sql += " AND is_active = TRUE"

        # Filters inactive categories.
        elif status == "inactive":
            sql += " AND is_active = FALSE"

        # Sorts categories by newest first.
        sql += " ORDER BY category_id DESC"

        # Executes the category query.
        cursor.execute(sql, tuple(params))

        categories = cursor.fetchall()

        return jsonify(categories), 200

    except Exception as e:

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


# Gets one category belonging to the logged-in user's store.
@category_bp.route("/<int:category_id>", methods=["GET"])
@jwt_required()
def get_category(category_id):

    # Gets the logged-in user's role from the JWT token.
    user_role = get_jwt().get("role")

    # Gets the logged-in user's store ID from the JWT token.
    store_id = get_jwt().get("store_id")

    # Prevents ADMIN from accessing store categories.
    if user_role == "ADMIN":
        return jsonify({
            "error": "ADMIN does not manage store categories."
        }), 403

    connection = None
    cursor = None

    try:

        # Gets a database connection from the pool.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Gets the category only if it belongs to the user's store.
        cursor.execute("""
            SELECT
                category_id,
                category_name,
                description,
                store_id,
                is_active,
                created_at,
                updated_at
            FROM categories
            WHERE category_id = %s
            AND store_id = %s
        """, (
            category_id,
            store_id
        ))

        category = cursor.fetchone()

        # Returns an error when the category does not belong to the store.
        if not category:
            return jsonify({
                "error": "Category not found."
            }), 404

        return jsonify(category), 200

    except Exception as e:

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


# Allows the OWNER to create a category for their store.
@category_bp.route("/", methods=["POST"])
@role_required("OWNER")
def create_category():

    # Gets the JSON data sent by the OWNER.
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required."
        }), 400

    # Gets the category name.
    category_name = data.get("category_name", "").strip()

    # Gets the optional category description.
    description = data.get("description", "").strip()

    # Requires a category name.
    if not category_name:
        return jsonify({
            "error": "Category name is required."
        }), 400

    # Gets the OWNER's store ID from the JWT token.
    store_id = get_jwt().get("store_id")

    connection = None
    cursor = None

    try:

        # Gets a database connection from the pool.
        connection = get_db_connection()

        # Creates a database cursor.
        cursor = connection.cursor()

        # Checks whether the category already exists in this store.
        cursor.execute("""
            SELECT category_id
            FROM categories
            WHERE category_name = %s
            AND store_id = %s
        """, (
            category_name,
            store_id
        ))

        existing_category = cursor.fetchone()

        # Prevents duplicate category names inside the same store.
        if existing_category:
            return jsonify({
                "error": "This category already exists in your store."
            }), 409

        # Creates the category inside the OWNER's store.
        cursor.execute("""
            INSERT INTO categories (
                category_name,
                description,
                store_id,
                is_active
            )
            VALUES (%s, %s, %s, TRUE)
        """, (
            category_name,
            description if description else None,
            store_id
        ))

        # Saves the new category.
        connection.commit()

        return jsonify({
            "message": "Category created successfully.",
            "category_id": cursor.lastrowid
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

        # Returns the connection to the pool.
        if connection:
            connection.close()


# Allows the OWNER to update a category belonging to their store.
@category_bp.route("/<int:category_id>", methods=["PUT"])
@role_required("OWNER")
def update_category(category_id):

    # Gets the JSON data.
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required."
        }), 400

    # Gets the updated category name.
    category_name = data.get("category_name", "").strip()

    # Gets the updated description.
    description = data.get("description", "").strip()

    # Requires a category name.
    if not category_name:
        return jsonify({
            "error": "Category name is required."
        }), 400

    # Gets the OWNER's store ID from the JWT token.
    store_id = get_jwt().get("store_id")

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a database cursor.
        cursor = connection.cursor()

        # Checks whether the category belongs to the OWNER's store.
        cursor.execute("""
            SELECT category_id
            FROM categories
            WHERE category_id = %s
            AND store_id = %s
        """, (
            category_id,
            store_id
        ))

        category = cursor.fetchone()

        # Prevents editing categories from another store.
        if not category:
            return jsonify({
                "error": "Category not found in your store."
            }), 404

        # Updates the category.
        cursor.execute("""
            UPDATE categories
            SET
                category_name = %s,
                description = %s
            WHERE category_id = %s
            AND store_id = %s
        """, (
            category_name,
            description if description else None,
            category_id,
            store_id
        ))

        # Saves the changes.
        connection.commit()

        return jsonify({
            "message": "Category updated successfully."
        }), 200

    except Exception as e:

        # Cancels unfinished database changes.
        if connection:
            connection.rollback()

        if "Duplicate entry" in str(e) or "1062" in str(e):
            return jsonify({
                "error": "Category name already exists."
            }), 409

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


# Allows the OWNER to deactivate a category instead of deleting it.
@category_bp.route("/<int:category_id>/deactivate", methods=["PUT"])
@role_required("OWNER")
def deactivate_category(category_id):

    # Gets the OWNER's store ID from the JWT token.
    store_id = get_jwt().get("store_id")

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a database cursor.
        cursor = connection.cursor()

        # Deactivates the category only inside the OWNER's store.
        cursor.execute("""
            UPDATE categories
            SET is_active = FALSE
            WHERE category_id = %s
            AND store_id = %s
        """, (
            category_id,
            store_id
        ))

        # Checks whether a category was actually updated.
        if cursor.rowcount == 0:
            return jsonify({
                "error": "Category not found in your store."
            }), 404

        # Saves the deactivation.
        connection.commit()

        return jsonify({
            "message": "Category deactivated successfully."
        }), 200

    except Exception as e:

        # Cancels unfinished changes.
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


# Allows the OWNER to reactivate an inactive category in their store.
@category_bp.route("/<int:category_id>/activate", methods=["PUT"])
@role_required("OWNER")
def activate_category(category_id):

    # Gets the OWNER's store ID from the JWT token.
    store_id = get_jwt().get("store_id")

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a database cursor.
        cursor = connection.cursor()

        # Reactivates the category only inside the OWNER's store.
        cursor.execute("""
            UPDATE categories
            SET is_active = TRUE
            WHERE category_id = %s
            AND store_id = %s
        """, (
            category_id,
            store_id
        ))

        # Checks whether the category exists.
        if cursor.rowcount == 0:
            return jsonify({
                "error": "Category not found in your store."
            }), 404

        # Saves the activation.
        connection.commit()

        return jsonify({
            "message": "Category activated successfully."
        }), 200

    except Exception as e:

        # Cancels unfinished changes.
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
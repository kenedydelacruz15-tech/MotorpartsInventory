from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from database import get_db_connection
from routes.user_routes import role_required


category_bp = Blueprint(
    "categories",
    __name__,
    url_prefix="/api/categories"
)


def get_store_id():
    claims = get_jwt()
    return claims.get("store_id")


def check_store():
    store_id = get_store_id()

    if not store_id:
        return None, (
            jsonify({
                "message": "User is not assigned to a store."
            }),
            400
        )

    return store_id, None


@category_bp.route("/", methods=["GET"])
@jwt_required()
def get_categories():
    claims = get_jwt()

    if claims.get("role") == "ADMIN":
        return jsonify({
            "message": "ADMIN does not manage store categories."
        }), 403

    store_id, error = check_store()

    if error:
        return error

    status = request.args.get("status", "active")
    search = request.args.get("search", "").strip()

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
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

        if status == "active":
            query += " AND is_active = 1"

        elif status == "inactive":
            query += " AND is_active = 0"

        elif status != "all":
            return jsonify({
                "message": "Invalid status. Use active, inactive, or all."
            }), 400

        if search:
            query += """
                AND (
                    category_name LIKE %s
                    OR description LIKE %s
                )
            """

            search_value = f"%{search}%"
            params.extend([search_value, search_value])

        query += " ORDER BY category_name ASC"

        cursor.execute(query, tuple(params))

        categories = cursor.fetchall()

        return jsonify(categories), 200

    except Exception as e:
        print("GET CATEGORIES ERROR:", e)

        return jsonify({
            "message": "Failed to load categories.",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


@category_bp.route("/<int:category_id>", methods=["GET"])
@jwt_required()
def get_category(category_id):
    store_id, error = check_store()

    if error:
        return error

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

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
        """, (category_id, store_id))

        category = cursor.fetchone()

        if not category:
            return jsonify({
                "message": "Category not found."
            }), 404

        return jsonify(category), 200

    except Exception as e:
        print("GET CATEGORY ERROR:", e)

        return jsonify({
            "message": "Failed to load category.",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


@category_bp.route("/", methods=["POST"])
@jwt_required()
@role_required("OWNER")
def create_category():
    store_id, error = check_store()

    if error:
        return error

    data = request.get_json() or {}

    category_name = str(
        data.get("category_name", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    if not category_name:
        return jsonify({
            "message": "Category name is required."
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT category_id
            FROM categories
            WHERE store_id = %s
              AND LOWER(category_name) = LOWER(%s)
            LIMIT 1
        """, (store_id, category_name))

        existing = cursor.fetchone()

        if existing:
            return jsonify({
                "message": "Category already exists in this store."
            }), 409

        cursor.execute("""
            INSERT INTO categories (
                category_name,
                description,
                store_id,
                is_active
            )
            VALUES (%s, %s, %s, 1)
        """, (
            category_name,
            description,
            store_id
        ))

        connection.commit()

        return jsonify({
            "message": "Category created successfully.",
            "category_id": cursor.lastrowid
        }), 201

    except Exception as e:
        if connection:
            connection.rollback()

        print("CREATE CATEGORY ERROR:", e)

        return jsonify({
            "message": "Failed to create category.",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


@category_bp.route("/<int:category_id>", methods=["PUT"])
@jwt_required()
@role_required("OWNER")
def update_category(category_id):
    store_id, error = check_store()

    if error:
        return error

    data = request.get_json() or {}

    category_name = str(
        data.get("category_name", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    if not category_name:
        return jsonify({
            "message": "Category name is required."
        }), 400

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT category_id
            FROM categories
            WHERE category_id = %s
              AND store_id = %s
        """, (category_id, store_id))

        category = cursor.fetchone()

        if not category:
            return jsonify({
                "message": "Category not found."
            }), 404

        cursor.execute("""
            SELECT category_id
            FROM categories
            WHERE store_id = %s
              AND LOWER(category_name) = LOWER(%s)
              AND category_id != %s
            LIMIT 1
        """, (
            store_id,
            category_name,
            category_id
        ))

        duplicate = cursor.fetchone()

        if duplicate:
            return jsonify({
                "message": "Another category with this name already exists."
            }), 409

        cursor.execute("""
            UPDATE categories
            SET
                category_name = %s,
                description = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE category_id = %s
              AND store_id = %s
        """, (
            category_name,
            description,
            category_id,
            store_id
        ))

        connection.commit()

        return jsonify({
            "message": "Category updated successfully."
        }), 200

    except Exception as e:
        if connection:
            connection.rollback()

        print("UPDATE CATEGORY ERROR:", e)

        return jsonify({
            "message": "Failed to update category.",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


@category_bp.route("/<int:category_id>/deactivate", methods=["PUT"])
@jwt_required()
@role_required("OWNER")
def deactivate_category(category_id):
    store_id, error = check_store()

    if error:
        return error

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                category_id,
                category_name,
                is_active
            FROM categories
            WHERE category_id = %s
              AND store_id = %s
        """, (category_id, store_id))

        category = cursor.fetchone()

        if not category:
            return jsonify({
                "message": "Category not found."
            }), 404

        if category["is_active"] == 0:
            return jsonify({
                "message": "Category is already inactive."
            }), 400

        cursor.execute("""
            UPDATE categories
            SET
                is_active = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE category_id = %s
              AND store_id = %s
        """, (
            category_id,
            store_id
        ))

        connection.commit()

        return jsonify({
            "message": "Category deactivated successfully."
        }), 200

    except Exception as e:
        if connection:
            connection.rollback()

        print("DEACTIVATE CATEGORY ERROR:", e)

        return jsonify({
            "message": "Failed to deactivate category.",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()


@category_bp.route("/<int:category_id>/restore", methods=["PUT"])
@jwt_required()
@role_required("OWNER")
def restore_category(category_id):
    store_id, error = check_store()

    if error:
        return error

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                category_id,
                category_name,
                is_active
            FROM categories
            WHERE category_id = %s
              AND store_id = %s
        """, (category_id, store_id))

        category = cursor.fetchone()

        if not category:
            return jsonify({
                "message": "Category not found."
            }), 404

        if category["is_active"] == 1:
            return jsonify({
                "message": "Category is already active."
            }), 400

        cursor.execute("""
            UPDATE categories
            SET
                is_active = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE category_id = %s
              AND store_id = %s
        """, (
            category_id,
            store_id
        ))

        connection.commit()

        return jsonify({
            "message": "Category restored successfully."
        }), 200

    except Exception as e:
        if connection:
            connection.rollback()

        print("RESTORE CATEGORY ERROR:", e)

        return jsonify({
            "message": "Failed to restore category.",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from database import get_db_connection

# Store API routes
store_bp = Blueprint("store_bp", __name__)


# Admin-only helper
def admin_only():
    claims = get_jwt()

    if claims.get("role") != "ADMIN":
        return False

    return True


# Get all stores for Admin
@store_bp.route("/api/store", methods=["GET"])
@jwt_required()
def get_stores():
    if not admin_only():
        return jsonify({
            "error": "You do not have permission to access stores."
        }), 403

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                s.store_id,
                s.store_name,
                s.store_address,
                s.store_contact,

                (
                    SELECT u.full_name
                    FROM users u
                    WHERE u.store_id = s.store_id
                      AND u.role = 'OWNER'
                    ORDER BY u.user_id ASC
                    LIMIT 1
                ) AS owner_name,

                (
                    SELECT COUNT(*)
                    FROM users u
                    WHERE u.store_id = s.store_id
                      AND u.role = 'STAFF'
                ) AS staff_count

            FROM stores s
            ORDER BY s.store_name ASC
            """
        )

        stores = cursor.fetchall()

        return jsonify(stores), 200

    except Exception as e:
        print("GET STORES ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        cursor.close()
        db.close()


# Create a store for Admin
@store_bp.route("/api/store", methods=["POST"])
@jwt_required()
def create_store():
    if not admin_only():
        return jsonify({
            "error": "Only Admin can create stores."
        }), 403

    data = request.get_json() or {}

    store_name = data.get("store_name", "").strip()
    store_address = data.get("store_address", "").strip()
    store_contact = data.get("store_contact", "").strip()

    if not store_name:
        return jsonify({
            "error": "Store name is required."
        }), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Check duplicate store name
        cursor.execute(
            """
            SELECT store_id
            FROM stores
            WHERE store_name = %s
            LIMIT 1
            """,
            (store_name,)
        )

        existing_store = cursor.fetchone()

        if existing_store:
            return jsonify({
                "error": "A store with this name already exists."
            }), 409

        cursor.execute(
            """
            INSERT INTO stores (
                store_name,
                store_address,
                store_contact
            )
            VALUES (%s, %s, %s)
            """,
            (
                store_name,
                store_address,
                store_contact
            )
        )

        db.commit()

        store_id = cursor.lastrowid

        return jsonify({
            "message": "Store created successfully.",
            "store_id": store_id
        }), 201

    except Exception as e:
        db.rollback()

        print("CREATE STORE ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        cursor.close()
        db.close()


# Update a store for Admin
@store_bp.route("/api/store/<int:store_id>", methods=["PUT"])
@jwt_required()
def update_store(store_id):
    if not admin_only():
        return jsonify({
            "error": "Only Admin can update stores."
        }), 403

    data = request.get_json() or {}

    store_name = data.get("store_name", "").strip()
    store_address = data.get("store_address", "").strip()
    store_contact = data.get("store_contact", "").strip()

    if not store_name:
        return jsonify({
            "error": "Store name is required."
        }), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Check store exists
        cursor.execute(
            """
            SELECT store_id
            FROM stores
            WHERE store_id = %s
            """,
            (store_id,)
        )

        store = cursor.fetchone()

        if not store:
            return jsonify({
                "error": "Store not found."
            }), 404

        # Check duplicate store name
        cursor.execute(
            """
            SELECT store_id
            FROM stores
            WHERE store_name = %s
              AND store_id != %s
            LIMIT 1
            """,
            (
                store_name,
                store_id
            )
        )

        duplicate = cursor.fetchone()

        if duplicate:
            return jsonify({
                "error": "Another store already uses this name."
            }), 409

        cursor.execute(
            """
            UPDATE stores
            SET
                store_name = %s,
                store_address = %s,
                store_contact = %s
            WHERE store_id = %s
            """,
            (
                store_name,
                store_address,
                store_contact,
                store_id
            )
        )

        db.commit()

        return jsonify({
            "message": "Store updated successfully."
        }), 200

    except Exception as e:
        db.rollback()

        print("UPDATE STORE ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        cursor.close()
        db.close()


# Get current owner's store information
@store_bp.route("/api/store/profile", methods=["GET"])
@jwt_required()
def get_store_profile():
    claims = get_jwt()
    role = claims.get("role")
    store_id = claims.get("store_id")

    if role != "OWNER":
        return jsonify({
            "error": "Only the store owner can access store settings."
        }), 403

    if not store_id:
        return jsonify({
            "error": "Store ID not found in token."
        }), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                store_id,
                store_name,
                store_address,
                store_contact
            FROM stores
            WHERE store_id = %s
            """,
            (store_id,)
        )

        store = cursor.fetchone()

        if not store:
            return jsonify({
                "error": "Store not found."
            }), 404

        return jsonify({
            "store_id": store["store_id"],
            "store_name": store["store_name"] or "",
            "address": store["store_address"] or "",
            "contact_number": store["store_contact"] or ""
        }), 200

    except Exception as e:
        print("GET STORE PROFILE ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        cursor.close()
        db.close()


# Update current owner's store information
@store_bp.route("/api/store/profile", methods=["PUT"])
@jwt_required()
def update_store_profile():
    claims = get_jwt()
    role = claims.get("role")
    store_id = claims.get("store_id")

    if role != "OWNER":
        return jsonify({
            "error": "Only the store owner can update store settings."
        }), 403

    if not store_id:
        return jsonify({
            "error": "Store ID not found in token."
        }), 400

    data = request.get_json() or {}

    store_name = data.get("store_name", "").strip()
    address = data.get("address", "").strip()
    contact_number = data.get("contact_number", "").strip()

    if not store_name:
        return jsonify({
            "error": "Store name is required."
        }), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            UPDATE stores
            SET
                store_name = %s,
                store_address = %s,
                store_contact = %s
            WHERE store_id = %s
            """,
            (
                store_name,
                address,
                contact_number,
                store_id
            )
        )

        db.commit()

        return jsonify({
            "message": "Store information updated successfully."
        }), 200

    except Exception as e:
        db.rollback()

        print("UPDATE STORE PROFILE ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        cursor.close()
        db.close()


# Check store setup status
@store_bp.route("/api/store/setup-status", methods=["GET"])
@jwt_required()
def setup_status():
    claims = get_jwt()
    store_id = claims.get("store_id")

    if not store_id:
        return jsonify({
            "setup_complete": False,
            "error": "Store ID not found in token."
        }), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT
                store_id,
                store_name,
                store_address,
                store_contact
            FROM stores
            WHERE store_id = %s
            """,
            (store_id,)
        )

        store = cursor.fetchone()

        if not store:
            return jsonify({
                "setup_complete": False
            }), 200

        # Check required setup fields
        setup_complete = bool(
            store.get("store_name") and
            store.get("store_address")
        )

        return jsonify({
            "setup_complete": setup_complete,
            "store": store
        }), 200

    except Exception as e:
        print("SETUP STATUS ERROR:", e)

        return jsonify({
            "error": str(e)
        }), 500

    finally:
        cursor.close()
        db.close()
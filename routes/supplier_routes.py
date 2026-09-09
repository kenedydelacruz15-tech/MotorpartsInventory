from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt

from database import get_db_connection


# Creates the Blueprint for supplier management.
supplier_bp = Blueprint(
    "suppliers",
    __name__,
    url_prefix="/api/suppliers"
)


# Gets the logged-in user's store and blocks the system ADMIN.
def get_store_access():

    # Gets the current user's JWT information.
    claims = get_jwt()

    # Gets the current user's role.
    user_role = claims.get("role")

    # Gets the current user's store ID.
    store_id = claims.get("store_id")

    # Blocks ADMIN from managing store suppliers.
    if user_role == "ADMIN":
        return None, jsonify({
            "error": "ADMIN does not manage store suppliers."
        }), 403

    # Blocks users without an assigned store.
    if not store_id:
        return None, jsonify({
            "error": "You are not assigned to a store."
        }), 403

    return (user_role, store_id), None, None


# Gets all active suppliers from the logged-in user's store.
@supplier_bp.route("/", methods=["GET"])
@jwt_required()
def get_suppliers():

    # Checks the user's store access.
    access, error_response, status_code = get_store_access()

    # Returns the access error when the user is blocked.
    if error_response:
        return error_response, status_code

    # Gets the user's role and store ID.
    user_role, store_id = access

    # Gets the optional search keyword.
    search = request.args.get("search", "").strip()

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Gets active suppliers from the user's store.
        sql = """
            SELECT
                supplier_id,
                supplier_name,
                contact_person,
                contact_number,
                email,
                address,
                store_id
            FROM suppliers
            WHERE store_id = %s
            AND deleted_at IS NULL
        """

        # Stores the SQL parameters.
        params = [store_id]

        # Searches supplier information.
        if search:

            sql += """
                AND (
                    supplier_name LIKE %s
                    OR contact_person LIKE %s
                    OR contact_number LIKE %s
                    OR email LIKE %s
                )
            """

            search_value = f"%{search}%"

            params.extend([
                search_value,
                search_value,
                search_value,
                search_value
            ])

        # Sorts suppliers alphabetically.
        sql += " ORDER BY supplier_name ASC"

        # Executes the supplier query.
        cursor.execute(sql, tuple(params))

        # Gets all matching suppliers.
        suppliers = cursor.fetchall()

        return jsonify({
            "supplier_count": len(suppliers),
            "suppliers": suppliers
        }), 200

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


# Gets one active supplier from the logged-in user's store.
@supplier_bp.route("/<int:supplier_id>", methods=["GET"])
@jwt_required()
def get_supplier(supplier_id):

    # Checks the user's store access.
    access, error_response, status_code = get_store_access()

    # Returns the access error when the user is blocked.
    if error_response:
        return error_response, status_code

    # Gets the user's store ID.
    user_role, store_id = access

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Gets the supplier only from the user's store.
        cursor.execute("""
            SELECT
                supplier_id,
                supplier_name,
                contact_person,
                contact_number,
                email,
                address,
                store_id
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

        # Returns an error when the supplier does not exist.
        if not supplier:
            return jsonify({
                "error": "Supplier not found."
            }), 404

        return jsonify(supplier), 200

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


# Allows only OWNER users to create suppliers.
@supplier_bp.route("/", methods=["POST"])
@jwt_required()
def create_supplier():

    # Checks the user's store access.
    access, error_response, status_code = get_store_access()

    # Returns the access error when the user is blocked.
    if error_response:
        return error_response, status_code

    # Gets the user's role and store ID.
    user_role, store_id = access

    # Allows only OWNER users to create suppliers.
    if user_role != "OWNER":
        return jsonify({
            "error": "Only OWNER can create suppliers."
        }), 403

    # Gets the JSON request data.
    data = request.get_json() or {}

    # Gets the supplier name.
    supplier_name = data.get("supplier_name", "").strip()

    # Gets the contact person.
    contact_person = data.get("contact_person", "").strip()

    # Gets the contact number.
    contact_number = data.get("contact_number")

    # Gets the email address.
    email = data.get("email")

    # Gets the supplier address.
    address = data.get("address")

    # Requires a supplier name.
    if not supplier_name:
        return jsonify({
            "error": "Supplier name is required."
        }), 400

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Checks for an existing active supplier in the same store.
        cursor.execute("""
            SELECT supplier_id
            FROM suppliers
            WHERE supplier_name = %s
            AND store_id = %s
            AND deleted_at IS NULL
        """, (
            supplier_name,
            store_id
        ))

        # Prevents duplicate active suppliers.
        if cursor.fetchone():
            return jsonify({
                "error": "Supplier already exists in your store."
            }), 409

        # Checks whether the supplier exists in the store's trash.
        cursor.execute("""
            SELECT supplier_id
            FROM suppliers
            WHERE supplier_name = %s
            AND store_id = %s
            AND deleted_at IS NOT NULL
        """, (
            supplier_name,
            store_id
        ))

        # Gets the deleted supplier.
        deleted_supplier = cursor.fetchone()

        # Suggests restoring instead of creating a duplicate.
        if deleted_supplier:
            return jsonify({
                "error": "This supplier exists in trash. Restore it instead.",
                "supplier_id": deleted_supplier["supplier_id"]
            }), 409

        # Closes the dictionary cursor.
        cursor.close()

        # Creates a normal cursor for inserting.
        cursor = connection.cursor()

        # Creates the supplier for the logged-in user's store.
        cursor.execute("""
            INSERT INTO suppliers (
                supplier_name,
                contact_person,
                contact_number,
                email,
                address,
                store_id
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            supplier_name,
            contact_person or None,
            contact_number,
            email,
            address,
            store_id
        ))

        # Gets the new supplier ID.
        supplier_id = cursor.lastrowid

        # Saves the supplier.
        connection.commit()

        return jsonify({
            "message": "Supplier created successfully.",
            "supplier_id": supplier_id
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

        # Returns the database connection.
        if connection:
            connection.close()


# Allows only OWNER users to fully update suppliers.
@supplier_bp.route("/<int:supplier_id>", methods=["PUT"])
@jwt_required()
def update_supplier(supplier_id):

    # Checks the user's store access.
    access, error_response, status_code = get_store_access()

    # Returns the access error when the user is blocked.
    if error_response:
        return error_response, status_code

    # Gets the user's role and store ID.
    user_role, store_id = access

    # Allows only OWNER users to update suppliers.
    if user_role != "OWNER":
        return jsonify({
            "error": "Only OWNER can update suppliers."
        }), 403

    # Gets the JSON request data.
    data = request.get_json() or {}

    # Gets the supplier name.
    supplier_name = data.get("supplier_name", "").strip()

    # Gets the contact person.
    contact_person = data.get("contact_person", "").strip()

    # Gets the contact number.
    contact_number = data.get("contact_number")

    # Gets the email.
    email = data.get("email")

    # Gets the address.
    address = data.get("address")

    # Requires a supplier name.
    if not supplier_name:
        return jsonify({
            "error": "Supplier name is required."
        }), 400

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Checks whether the supplier belongs to the user's store.
        cursor.execute("""
            SELECT supplier_id
            FROM suppliers
            WHERE supplier_id = %s
            AND store_id = %s
            AND deleted_at IS NULL
        """, (
            supplier_id,
            store_id
        ))

        # Returns an error when the supplier does not exist.
        if not cursor.fetchone():
            return jsonify({
                "error": "Supplier not found."
            }), 404

        # Checks for duplicate supplier names in the same store.
        cursor.execute("""
            SELECT supplier_id
            FROM suppliers
            WHERE supplier_name = %s
            AND supplier_id != %s
            AND store_id = %s
            AND deleted_at IS NULL
        """, (
            supplier_name,
            supplier_id,
            store_id
        ))

        # Prevents duplicate supplier names.
        if cursor.fetchone():
            return jsonify({
                "error": "Another supplier with this name already exists."
            }), 409

        # Closes the dictionary cursor.
        cursor.close()

        # Creates a normal cursor.
        cursor = connection.cursor()

        # Updates the supplier information.
        cursor.execute("""
            UPDATE suppliers
            SET
                supplier_name = %s,
                contact_person = %s,
                contact_number = %s,
                email = %s,
                address = %s
            WHERE supplier_id = %s
            AND store_id = %s
            AND deleted_at IS NULL
        """, (
            supplier_name,
            contact_person or None,
            contact_number,
            email,
            address,
            supplier_id,
            store_id
        ))

        # Saves the changes.
        connection.commit()

        return jsonify({
            "message": "Supplier updated successfully."
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

        # Returns the database connection.
        if connection:
            connection.close()


# Gets deleted suppliers from the logged-in user's store.
@supplier_bp.route("/trash", methods=["GET"])
@jwt_required()
def get_supplier_trash():

    # Checks the user's store access.
    access, error_response, status_code = get_store_access()

    # Returns the access error when the user is blocked.
    if error_response:
        return error_response, status_code

    # Gets the user's store ID.
    user_role, store_id = access

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Gets deleted suppliers from the user's store.
        cursor.execute("""
            SELECT
                supplier_id,
                supplier_name,
                contact_person,
                contact_number,
                email,
                address,
                deleted_at
            FROM suppliers
            WHERE store_id = %s
            AND deleted_at IS NOT NULL
            ORDER BY deleted_at DESC
        """, (store_id,))

        # Gets the deleted suppliers.
        suppliers = cursor.fetchall()

        return jsonify({
            "trash_count": len(suppliers),
            "deleted_suppliers": suppliers
        }), 200

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


# Allows only OWNER users to move suppliers to trash.
@supplier_bp.route("/<int:supplier_id>", methods=["DELETE"])
@jwt_required()
def delete_supplier(supplier_id):

    # Checks the user's store access.
    access, error_response, status_code = get_store_access()

    # Returns the access error when the user is blocked.
    if error_response:
        return error_response, status_code

    # Gets the user's role and store ID.
    user_role, store_id = access

    # Allows only OWNER users to delete suppliers.
    if user_role != "OWNER":
        return jsonify({
            "error": "Only OWNER can delete suppliers."
        }), 403

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Checks whether the supplier belongs to the user's store.
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

        # Returns an error when the supplier does not exist.
        if not supplier:
            return jsonify({
                "error": "Supplier not found or already deleted."
            }), 404

        # Closes the dictionary cursor.
        cursor.close()

        # Creates a normal cursor.
        cursor = connection.cursor()

        # Moves the supplier to trash.
        cursor.execute("""
            UPDATE suppliers
            SET deleted_at = NOW()
            WHERE supplier_id = %s
            AND store_id = %s
            AND deleted_at IS NULL
        """, (
            supplier_id,
            store_id
        ))

        # Saves the soft delete.
        connection.commit()

        return jsonify({
            "message": "Supplier moved to trash successfully.",
            "supplier_id": supplier_id,
            "supplier_name": supplier["supplier_name"]
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

        # Returns the database connection.
        if connection:
            connection.close()


# Allows only OWNER users to restore suppliers from trash.
@supplier_bp.route("/<int:supplier_id>/restore", methods=["PUT"])
@jwt_required()
def restore_supplier(supplier_id):

    # Checks the user's store access.
    access, error_response, status_code = get_store_access()

    # Returns the access error when the user is blocked.
    if error_response:
        return error_response, status_code

    # Gets the user's role and store ID.
    user_role, store_id = access

    # Allows only OWNER users to restore suppliers.
    if user_role != "OWNER":
        return jsonify({
            "error": "Only OWNER can restore suppliers."
        }), 403

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Finds the deleted supplier in the user's store.
        cursor.execute("""
            SELECT supplier_id, supplier_name
            FROM suppliers
            WHERE supplier_id = %s
            AND store_id = %s
            AND deleted_at IS NOT NULL
        """, (
            supplier_id,
            store_id
        ))

        # Gets the deleted supplier.
        supplier = cursor.fetchone()

        # Returns an error when the supplier is not in trash.
        if not supplier:
            return jsonify({
                "error": "Deleted supplier not found."
            }), 404

        # Checks for an active supplier with the same name.
        cursor.execute("""
            SELECT supplier_id
            FROM suppliers
            WHERE supplier_name = %s
            AND store_id = %s
            AND deleted_at IS NULL
        """, (
            supplier["supplier_name"],
            store_id
        ))

        # Prevents duplicate active suppliers.
        if cursor.fetchone():
            return jsonify({
                "error": "An active supplier with this name already exists."
            }), 409

        # Closes the dictionary cursor.
        cursor.close()

        # Creates a normal cursor.
        cursor = connection.cursor()

        # Restores the supplier.
        cursor.execute("""
            UPDATE suppliers
            SET deleted_at = NULL
            WHERE supplier_id = %s
            AND store_id = %s
            AND deleted_at IS NOT NULL
        """, (
            supplier_id,
            store_id
        ))

        # Saves the restoration.
        connection.commit()

        return jsonify({
            "message": "Supplier restored successfully."
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

        # Returns the database connection.
        if connection:
            connection.close()


# Allows only OWNER users to permanently delete unused suppliers.
@supplier_bp.route("/<int:supplier_id>/permanent", methods=["DELETE"])
@jwt_required()
def permanently_delete_supplier(supplier_id):

    # Checks the user's store access.
    access, error_response, status_code = get_store_access()

    # Returns the access error when the user is blocked.
    if error_response:
        return error_response, status_code

    # Gets the user's role and store ID.
    user_role, store_id = access

    # Allows only OWNER users to permanently delete suppliers.
    if user_role != "OWNER":
        return jsonify({
            "error": "Only OWNER can permanently delete suppliers."
        }), 403

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Finds the deleted supplier in the user's store.
        cursor.execute("""
            SELECT supplier_id, supplier_name
            FROM suppliers
            WHERE supplier_id = %s
            AND store_id = %s
            AND deleted_at IS NOT NULL
        """, (
            supplier_id,
            store_id
        ))

        # Gets the supplier.
        supplier = cursor.fetchone()

        # Requires the supplier to be in trash.
        if not supplier:
            return jsonify({
                "error": "Supplier not found in trash."
            }), 404

        # Checks whether Stock In records use this supplier.
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM stock_in
            WHERE supplier_id = %s
            AND store_id = %s
        """, (
            supplier_id,
            store_id
        ))

        # Gets the Stock In usage count.
        stock_in_count = cursor.fetchone()["total"]

        # Checks whether Purchase Orders use this supplier.
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM purchase_orders
            WHERE supplier_id = %s
            AND store_id = %s
        """, (
            supplier_id,
            store_id
        ))

        # Gets the Purchase Order usage count.
        purchase_order_count = cursor.fetchone()["total"]

        # Prevents permanent deletion when transaction history exists.
        if stock_in_count > 0 or purchase_order_count > 0:
            return jsonify({
                "error": "Cannot permanently delete this supplier because transaction history exists.",
                "stock_in_records": stock_in_count,
                "purchase_order_records": purchase_order_count
            }), 400

        # Closes the dictionary cursor.
        cursor.close()

        # Creates a normal cursor.
        cursor = connection.cursor()

        # Permanently removes the supplier.
        cursor.execute("""
            DELETE FROM suppliers
            WHERE supplier_id = %s
            AND store_id = %s
            AND deleted_at IS NOT NULL
        """, (
            supplier_id,
            store_id
        ))

        # Saves the permanent deletion.
        connection.commit()

        return jsonify({
            "message": "Supplier permanently deleted successfully."
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

        # Returns the database connection.
        if connection:
            connection.close()
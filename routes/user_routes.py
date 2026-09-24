from functools import wraps

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db_connection


# Creates the Blueprint for authentication and user management.
user_bp = Blueprint(
    "users",
    __name__,
    url_prefix="/api/users"
)


# Checks whether the logged-in user has one of the allowed roles.
def role_required(*allowed_roles):

    def decorator(fn):

        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):

            # Gets the role stored inside the JWT token.
            user_role = get_jwt().get("role")

            # Blocks users who do not have an allowed role.
            if user_role not in allowed_roles:
                return jsonify({
                    "error": "You do not have permission to access this resource."
                }), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator


# Registers a new store and automatically creates its OWNER account.
@user_bp.route("/register-owner", methods=["POST"])
def register_owner():

    # Gets the JSON data sent by the user.
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required."
        }), 400

    # Gets the store information.
    store_name = data.get("store_name", "").strip()
    store_address = data.get("store_address", "").strip()
    store_contact = data.get("store_contact", "").strip()

    # Gets the owner information.
    full_name = data.get("full_name", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    # Requires the important store and owner information.
    if not store_name or not full_name or not username or not email or not password:
        return jsonify({
            "error": "Store name, full name, username, email, and password are required."
        }), 400

    # Requires a minimum password length.
    if len(password) < 8:
        return jsonify({
            "error": "Password must be at least 8 characters."
        }), 400

    connection = None
    cursor = None

    try:

        # Gets a database connection from the connection pool.
        connection = get_db_connection()

        # Creates a cursor for checking existing accounts.
        cursor = connection.cursor(dictionary=True)

        # Checks whether the username already exists.
        cursor.execute("""
            SELECT user_id
            FROM users
            WHERE username = %s
            LIMIT 1
        """, (username,))

        if cursor.fetchone():
            return jsonify({
                "error": "Username already exists."
            }), 409

        # Checks whether the email already exists.
        cursor.execute("""
            SELECT user_id
            FROM users
            WHERE email = %s
            LIMIT 1
        """, (email,))

        if cursor.fetchone():
            return jsonify({
                "error": "Email already exists."
            }), 409

        # Closes the checking cursor.
        cursor.close()

        # Creates a normal cursor for inserting data.
        cursor = connection.cursor()

        # Creates the new store first.
        cursor.execute("""
            INSERT INTO stores (
                store_name,
                store_address,
                store_contact
            )
            VALUES (%s, %s, %s)
        """, (
            store_name,
            store_address if store_address else None,
            store_contact if store_contact else None
        ))

        # Gets the ID of the newly created store.
        store_id = cursor.lastrowid

        # Creates a secure password hash.
        password_hash = generate_password_hash(password)

        # Creates the OWNER account and connects it to the store.
        cursor.execute("""
            INSERT INTO users (
                full_name,
                username,
                email,
                password_hash,
                role,
                is_active,
                store_id
            )
            VALUES (%s, %s, %s, %s, 'OWNER', TRUE, %s)
        """, (
            full_name,
            username,
            email,
            password_hash,
            store_id
        ))

        # Gets the ID of the new owner.
        user_id = cursor.lastrowid

        # Saves both the store and owner account.
        connection.commit()

        return jsonify({
            "message": "Store and OWNER account registered successfully.",
            "store": {
                "store_id": store_id,
                "store_name": store_name
            },
            "owner": {
                "user_id": user_id,
                "full_name": full_name,
                "username": username,
                "role": "OWNER"
            }
        }), 201

    except Exception as e:

        # Cancels unfinished changes when an error occurs.
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


# Logs in an ADMIN, OWNER, or STAFF account.
@user_bp.route("/login", methods=["POST"])
def login():

    # Gets the JSON data sent by the user.
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required."
        }), 400

    # Gets the login credentials.
    username = data.get("username", "").strip()
    password = data.get("password", "")

    # Requires both login fields.
    if not username or not password:
        return jsonify({
            "error": "Username and password are required."
        }), 400

    connection = None
    cursor = None

    try:

        # Gets a database connection from the pool.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Searches for the user.
        cursor.execute("""
            SELECT *
            FROM users
            WHERE username = %s
        """, (username,))

        user = cursor.fetchone()

        # Rejects unknown usernames.
        if not user:
            return jsonify({
                "error": "Invalid username or password."
            }), 401

        # Rejects inactive accounts.
        if not user["is_active"]:
            return jsonify({
                "error": "This account has been deactivated."
            }), 403

        # Verifies the password.
        if not check_password_hash(user["password_hash"], password):
            return jsonify({
                "error": "Invalid username or password."
            }), 401

        # Creates the JWT containing user and store information.
        access_token = create_access_token(
            identity=str(user["user_id"]),
            additional_claims={
                "role": user["role"],
                "username": user["username"],
                "store_id": user["store_id"]
            }
        )

        return jsonify({
            "message": "Login successful.",
            "access_token": access_token,
            "user": {
                "user_id": user["user_id"],
                "full_name": user["full_name"],
                "username": user["username"],
                "email": user["email"],
                "role": user["role"],
                "store_id": user["store_id"]
            }
        }), 200

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


# Allows an OWNER to create STAFF accounts for their own store.
@user_bp.route("/", methods=["POST"])
@role_required("OWNER")
def create_staff():

    # Gets the JSON data.
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required."
        }), 400

    # Gets the new staff information.
    full_name = data.get("full_name", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    # Requires all important staff information.
    if not full_name or not username or not email or not password:
        return jsonify({
            "error": "Full name, username, email, and password are required."
        }), 400

    # Requires a minimum password length.
    if len(password) < 8:
        return jsonify({
            "error": "Password must be at least 8 characters."
        }), 400

    # Gets the owner's store ID from the JWT.
    store_id = get_jwt().get("store_id")

    # Ensures the owner belongs to a store.
    if not store_id:
        return jsonify({
            "error": "Your account is not assigned to a store."
        }), 400

    # Creates a secure password hash.
    password_hash = generate_password_hash(password)

    connection = None
    cursor = None

    try:

        # Gets a database connection from the pool.
        connection = get_db_connection()

        # Creates a database cursor.
        cursor = connection.cursor()

        # Creates the STAFF account inside the owner's store.
        cursor.execute("""
            INSERT INTO users (
                full_name,
                username,
                email,
                password_hash,
                role,
                is_active,
                store_id
            )
            VALUES (%s, %s, %s, %s, 'STAFF', TRUE, %s)
        """, (
            full_name,
            username,
            email,
            password_hash,
            store_id
        ))

        # Saves the new staff account.
        connection.commit()

        return jsonify({
            "message": "STAFF account created successfully.",
            "store_id": store_id
        }), 201

    except Exception as e:

        # Cancels unfinished changes.
        if connection:
            connection.rollback()

        if "Duplicate entry" in str(e) or "1062" in str(e):
            return jsonify({
                "error": "Username or email already exists."
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


# Allows the OWNER to view users belonging only to their store.
@user_bp.route("/", methods=["GET"])
@role_required("OWNER")
def get_store_users():

    # Gets the owner's store ID from the JWT.
    store_id = get_jwt().get("store_id")

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Gets users belonging only to the owner's store.
        cursor.execute("""
            SELECT
                user_id,
                full_name,
                username,
                email,
                role,
                is_active,
                created_at,
                updated_at
            FROM users
            WHERE store_id = %s
            ORDER BY created_at DESC
        """, (store_id,))

        users = cursor.fetchall()

        return jsonify(users), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        # Closes the cursor.
        if cursor:
            cursor.close()

        # Returns the connection to the pool.
        if connection:
            connection.close()


# Returns the profile of the logged-in user.
@user_bp.route("/me", methods=["GET"])
@jwt_required()
def get_my_profile():

    # Gets the logged-in user's ID.
    user_id = get_jwt_identity()

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Gets the user's profile.
        cursor.execute("""
            SELECT
                user_id,
                full_name,
                username,
                email,
                role,
                is_active,
                store_id,
                created_at,
                updated_at
            FROM users
            WHERE user_id = %s
        """, (user_id,))

        user = cursor.fetchone()

        # Returns an error when the account does not exist.
        if not user:
            return jsonify({
                "error": "User not found."
            }), 404

        return jsonify(user), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        # Closes the cursor.
        if cursor:
            cursor.close()

        # Returns the connection to the pool.
        if connection:
            connection.close()


# Allows an OWNER to update STAFF accounts belonging to their store.
@user_bp.route("/<int:user_id>", methods=["PUT"])
@role_required("OWNER")
def update_staff(user_id):

    # Gets the JSON data.
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required."
        }), 400

    # Gets the owner's store ID.
    store_id = get_jwt().get("store_id")

    # Gets the updated information.
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip()

    # Requires the important fields.
    if not full_name or not email:
        return jsonify({
            "error": "Full name and email are required."
        }), 400

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Checks whether the staff belongs to the owner's store.
        cursor.execute("""
            SELECT user_id, role
            FROM users
            WHERE user_id = %s
            AND store_id = %s
        """, (
            user_id,
            store_id
        ))

        user = cursor.fetchone()

        # Rejects users outside the owner's store.
        if not user:
            return jsonify({
                "error": "User not found in your store."
            }), 404

        # Prevents the route from editing another OWNER.
        if user["role"] != "STAFF":
            return jsonify({
                "error": "You can only update STAFF accounts."
            }), 403

        # Closes the dictionary cursor.
        cursor.close()

        # Creates a normal cursor.
        cursor = connection.cursor()

        # Updates the staff information.
        cursor.execute("""
            UPDATE users
            SET
                full_name = %s,
                email = %s
            WHERE user_id = %s
            AND store_id = %s
        """, (
            full_name,
            email,
            user_id,
            store_id
        ))

        # Saves the changes.
        connection.commit()

        return jsonify({
            "message": "STAFF account updated successfully."
        }), 200

    except Exception as e:

        # Cancels unfinished changes.
        if connection:
            connection.rollback()

        if "Duplicate entry" in str(e) or "1062" in str(e):
            return jsonify({
                "error": "Email already exists."
            }), 409

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        # Closes the cursor.
        if cursor:
            cursor.close()

        # Returns the connection to the pool.
        if connection:
            connection.close()


# Allows an OWNER to deactivate STAFF accounts in their store.
@user_bp.route("/<int:user_id>/deactivate", methods=["PUT"])
@role_required("OWNER")
def deactivate_staff(user_id):

    # Gets the owner's store ID.
    store_id = get_jwt().get("store_id")

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Checks whether the staff belongs to the owner's store.
        cursor.execute("""
            SELECT user_id, role
            FROM users
            WHERE user_id = %s
            AND store_id = %s
        """, (
            user_id,
            store_id
        ))

        user = cursor.fetchone()

        # Rejects users outside the owner's store.
        if not user:
            return jsonify({
                "error": "User not found in your store."
            }), 404

        # Prevents the OWNER from deactivating OWNER accounts.
        if user["role"] != "STAFF":
            return jsonify({
                "error": "You can only deactivate STAFF accounts."
            }), 403

        # Closes the dictionary cursor.
        cursor.close()

        # Creates a normal cursor.
        cursor = connection.cursor()

        # Deactivates the staff account.
        cursor.execute("""
            UPDATE users
            SET is_active = FALSE
            WHERE user_id = %s
            AND store_id = %s
        """, (
            user_id,
            store_id
        ))

        # Saves the changes.
        connection.commit()

        return jsonify({
            "message": "STAFF account deactivated successfully."
        }), 200

    except Exception as e:

        # Cancels unfinished changes.
        if connection:
            connection.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        # Closes the cursor.
        if cursor:
            cursor.close()

        # Returns the connection to the pool.
        if connection:
            connection.close()


# Allows any logged-in user to change their own password.
@user_bp.route("/change-password", methods=["PUT"])
@jwt_required()
def change_password():

    # Gets the JSON data.
    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required."
        }), 400

    # Gets the password values.
    current_password = data.get("current_password", "")
    new_password = data.get("new_password", "")

    # Requires both passwords.
    if not current_password or not new_password:
        return jsonify({
            "error": "Current password and new password are required."
        }), 400

    # Requires a secure password length.
    if len(new_password) < 8:
        return jsonify({
            "error": "New password must be at least 8 characters."
        }), 400

    # Gets the logged-in user's ID.
    user_id = get_jwt_identity()

    connection = None
    cursor = None

    try:

        # Gets a database connection.
        connection = get_db_connection()

        # Creates a dictionary cursor.
        cursor = connection.cursor(dictionary=True)

        # Gets the current password hash.
        cursor.execute("""
            SELECT password_hash
            FROM users
            WHERE user_id = %s
        """, (user_id,))

        user = cursor.fetchone()

        # Rejects missing accounts.
        if not user:
            return jsonify({
                "error": "User not found."
            }), 404

        # Verifies the current password.
        if not check_password_hash(
            user["password_hash"],
            current_password
        ):
            return jsonify({
                "error": "Current password is incorrect."
            }), 401

        # Creates the new password hash.
        new_password_hash = generate_password_hash(new_password)

        # Closes the dictionary cursor.
        cursor.close()

        # Creates a normal cursor.
        cursor = connection.cursor()

        # Updates the password hash.
        cursor.execute("""
            UPDATE users
            SET password_hash = %s
            WHERE user_id = %s
        """, (
            new_password_hash,
            user_id
        ))

        # Saves the new password.
        connection.commit()

        return jsonify({
            "message": "Password changed successfully."
        }), 200

    except Exception as e:

        # Cancels unfinished changes.
        if connection:
            connection.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        # Closes the cursor.
        if cursor:
            cursor.close()

        # Returns the connection to the pool.
        if connection:
            connection.close()


    # Allows ADMIN to view all system users.
@user_bp.route("/admin/users", methods=["GET"])
@role_required("ADMIN")
def admin_get_users():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                u.user_id,
                u.full_name,
                u.username,
                u.email,
                u.role,
                u.is_active,
                u.store_id,
                s.store_name,
                u.created_at,
                u.updated_at
            FROM users u
            LEFT JOIN stores s
                ON u.store_id = s.store_id
            ORDER BY u.created_at DESC
        """)

        users = cursor.fetchall()

        return jsonify(users), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# Allows ADMIN to create OWNER or STAFF accounts.
@user_bp.route("/admin/users", methods=["POST"])
@role_required("ADMIN")
def admin_create_user():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Request body is required."
        }), 400

    full_name = data.get("full_name", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    role = data.get("role", "").strip().upper()
    store_id = data.get("store_id")

    # Validate required fields.
    if not full_name or not username or not email or not password or not role:
        return jsonify({
            "error": "Full name, username, email, password, and role are required."
        }), 400

    # Only OWNER and STAFF can be created here.
    if role not in ("OWNER", "STAFF"):
        return jsonify({
            "error": "Role must be OWNER or STAFF."
        }), 400

    # Validate password.
    if len(password) < 8:
        return jsonify({
            "error": "Password must be at least 8 characters."
        }), 400

    # OWNER and STAFF must belong to a store.
    if not store_id:
        return jsonify({
            "error": "Store ID is required."
        }), 400

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Check username.
        cursor.execute("""
            SELECT user_id
            FROM users
            WHERE username = %s
            LIMIT 1
        """, (username,))

        if cursor.fetchone():
            return jsonify({
                "error": "Username already exists."
            }), 409

        # Check email.
        cursor.execute("""
            SELECT user_id
            FROM users
            WHERE email = %s
            LIMIT 1
        """, (email,))

        if cursor.fetchone():
            return jsonify({
                "error": "Email already exists."
            }), 409

        # Check store.
        cursor.execute("""
            SELECT store_id, store_name
            FROM stores
            WHERE store_id = %s
            LIMIT 1
        """, (store_id,))

        store = cursor.fetchone()

        if not store:
            return jsonify({
                "error": "Store not found."
            }), 404

        password_hash = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users (
                full_name,
                username,
                email,
                password_hash,
                role,
                is_active,
                store_id
            )
            VALUES (%s, %s, %s, %s, %s, TRUE, %s)
        """, (
            full_name,
            username,
            email,
            password_hash,
            role,
            store_id
        ))

        user_id = cursor.lastrowid

        connection.commit()

        return jsonify({
            "message": "User created successfully.",
            "user": {
                "user_id": user_id,
                "full_name": full_name,
                "username": username,
                "email": email,
                "role": role,
                "store_id": store_id,
                "store_name": store["store_name"]
            }
        }), 201

    except Exception as e:

        if connection:
            connection.rollback()

        if "Duplicate entry" in str(e) or "1062" in str(e):
            return jsonify({
                "error": "Username or email already exists."
            }), 409

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# Allows ADMIN to activate or deactivate any user.
@user_bp.route("/admin/users/<int:user_id>/status", methods=["PUT"])
@role_required("ADMIN")
def admin_update_user_status(user_id):

    data = request.get_json()

    if not data or "is_active" not in data:
        return jsonify({
            "error": "is_active is required."
        }), 400

    is_active = bool(data["is_active"])

    connection = None
    cursor = None

    try:

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Check whether the user exists.
        cursor.execute("""
            SELECT user_id, username, role
            FROM users
            WHERE user_id = %s
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
            return jsonify({
                "error": "User not found."
            }), 404

        # Prevent ADMIN from disabling another ADMIN.
        if user["role"] == "ADMIN":
            return jsonify({
                "error": "ADMIN accounts cannot be changed here."
            }), 403

        cursor.execute("""
            UPDATE users
            SET is_active = %s
            WHERE user_id = %s
        """, (
            is_active,
            user_id
        ))

        connection.commit()

        return jsonify({
            "message": (
                "User activated successfully."
                if is_active
                else "User deactivated successfully."
            )
        }), 200

    except Exception as e:

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


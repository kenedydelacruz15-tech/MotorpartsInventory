from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt

from database import get_db_connection
from services.dashboard_service import get_dashboard_summary


# Dashboard API routes
dashboard_bp = Blueprint("dashboard_bp", __name__)


# Dashboard summary statistics
@dashboard_bp.route("/api/dashboard/summary", methods=["GET"])
@jwt_required()
def dashboard_summary():

    # Get JWT claims
    claims = get_jwt()

    # Get store ID from JWT
    store_id = claims.get("store_id")

    if not store_id:
        return jsonify({
            "error": "Store ID not found in token."
        }), 400

    try:
        # Get dashboard summary
        summary = get_dashboard_summary(store_id)

        return jsonify(summary), 200

    except Exception as e:
        # Debug summary error
        return jsonify({
            "error": str(e)
        }), 500


# Sales trend data
@dashboard_bp.route("/api/dashboard/charts/sales", methods=["GET"])
@jwt_required()
def get_sales_chart():

    # Get JWT claims
    claims = get_jwt()

    # Get store ID from JWT
    current_store_id = claims.get("store_id")

    # Get requested number of days
    days = request.args.get(
        "days",
        default=7,
        type=int
    )

    if days <= 0:
        return jsonify({
            "error": "Days must be greater than 0."
        }), 400

    # Open database connection
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Get daily sales
        cursor.execute(
            """
            SELECT
                DATE(sale_date) AS sale_day,
                COUNT(sale_id) AS sale_count,
                COALESCE(SUM(total_sales), 0) AS total_sales
            FROM sales
            WHERE
                store_id = %s
                AND DATE(sale_date) >= DATE_SUB(
                    CURDATE(),
                    INTERVAL %s DAY
                )
            GROUP BY DATE(sale_date)
            ORDER BY sale_day ASC
            """,
            (current_store_id, days)
        )

        sales_data = cursor.fetchall()

        return jsonify({
            "chart": "sales_trend",
            "period_days": days,
            "data": sales_data
        }), 200

    except Exception as e:
        # Debug sales chart error
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        cursor.close()
        db.close()


# Stock grouped by category
@dashboard_bp.route("/api/dashboard/charts/category-stock", methods=["GET"])
@jwt_required()
def get_category_stock_chart():

    # Get JWT claims
    claims = get_jwt()

    # Get store ID from JWT
    current_store_id = claims.get("store_id")

    # Open database connection
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Get stock totals by category
        cursor.execute(
            """
            SELECT
                COALESCE(
                    c.category_name,
                    'Uncategorized'
                ) AS category_name,

                COALESCE(
                    SUM(i.stock_quantity),
                    0
                ) AS total_stock

            FROM products p

            LEFT JOIN categories c
                ON p.category_id = c.category_id
                AND c.store_id = p.store_id

            LEFT JOIN inventory i
                ON p.product_id = i.product_id

            WHERE p.store_id = %s

            GROUP BY
                c.category_id,
                c.category_name

            ORDER BY total_stock DESC
            """,
            (current_store_id,)
        )

        category_data = cursor.fetchall()

        return jsonify({
            "chart": "stock_by_category",
            "data": category_data
        }), 200

    except Exception as e:
        # Debug category stock error
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        cursor.close()
        db.close()


# Inventory status counts
@dashboard_bp.route("/api/dashboard/charts/inventory-status", methods=["GET"])
@jwt_required()
def get_inventory_status_chart():

    # Get JWT claims
    claims = get_jwt()

    # Get store ID from JWT
    current_store_id = claims.get("store_id")

    # Open database connection
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Get product stock status
        cursor.execute(
            """
            SELECT
                CASE
                    WHEN COALESCE(i.stock_quantity, 0) <= 0
                        THEN 'OUT_OF_STOCK'

                    WHEN COALESCE(i.stock_quantity, 0)
                         <= p.reorder_level
                        THEN 'LOW_STOCK'

                    ELSE 'IN_STOCK'
                END AS stock_status,

                COUNT(p.product_id) AS product_count

            FROM products p

            LEFT JOIN inventory i
                ON p.product_id = i.product_id

            WHERE p.store_id = %s

            GROUP BY stock_status
            """,
            (current_store_id,)
        )

        status_data = cursor.fetchall()

        return jsonify({
            "chart": "inventory_status",
            "data": status_data
        }), 200

    except Exception as e:
        # Debug inventory status error
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        cursor.close()
        db.close()


# Stock movement totals
@dashboard_bp.route("/api/dashboard/charts/stock-movements", methods=["GET"])
@jwt_required()
def get_stock_movement_chart():

    # Get JWT claims
    claims = get_jwt()

    # Get store ID from JWT
    current_store_id = claims.get("store_id")

    # Get requested number of days
    days = request.args.get(
        "days",
        default=7,
        type=int
    )

    if days <= 0:
        return jsonify({
            "error": "Days must be greater than 0."
        }), 400

    # Open database connection
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    try:
        # Get stock movements
        cursor.execute(
            """
            SELECT
                sm.movement_type,

                COALESCE(
                    SUM(sm.quantity),
                    0
                ) AS total_quantity

            FROM stock_movements sm

            JOIN products p
                ON sm.product_id = p.product_id

            WHERE
                p.store_id = %s

                AND DATE(sm.movement_date) >= DATE_SUB(
                    CURDATE(),
                    INTERVAL %s DAY
                )

            GROUP BY sm.movement_type

            ORDER BY sm.movement_type ASC
            """,
            (current_store_id, days)
        )

        movement_data = cursor.fetchall()

        return jsonify({
            "chart": "stock_movements",
            "period_days": days,
            "data": movement_data
        }), 200

    except Exception as e:
        # Debug stock movement error
        return jsonify({
            "error": str(e)
        }), 500

    finally:
        cursor.close()
        db.close()
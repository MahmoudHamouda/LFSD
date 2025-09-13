from flask import Blueprint, request, jsonify
from shared.db_connection import get_db_connection
from datetime import datetime
from api_gateway.middleware.authentication import token_required
from marshmallow import Schema, fields, ValidationError

financial_blueprint = Blueprint("financial_service", __name__)


# ---- Schemas ----------------------------------------------------------------
class AffordabilitySchema(Schema):
    item = fields.Str(required=True)
    price = fields.Float(required=True)
    loan_term = fields.Int(required=True)
    down_payment = fields.Float(required=True)


class TransactionSchema(Schema):
    amount = fields.Float(required=True)
    category = fields.Str(required=True)
    description = fields.Str(load_default=None)
    transaction_date = fields.DateTime(load_default=lambda: datetime.utcnow())
    linked_expense_id = fields.Int(load_default=None)
    linked_order_id = fields.Int(load_default=None)
    linked_debt_id = fields.Int(load_default=None)


# ---- Routes -----------------------------------------------------------------
@financial_blueprint.route("/users/<int:user_id>/financials", methods=["GET"])
@token_required
def get_financial_summary(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT income, expenses, savings, debts FROM Financials WHERE user_id = %s",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Financial data not found"}), 404

    return (
        jsonify(
            {
                "status": "success",
                "data": {
                    "income": row[0],
                    "expenses": row[1],
                    "savings": row[2],
                    "debts": row[3],
                },
            }
        ),
        200,
    )


@financial_blueprint.route(
    "/users/<int:user_id>/financials/affordability", methods=["POST"]
)
@token_required
def analyze_affordability(user_id: int):
    try:
        data = AffordabilitySchema().load(request.json or {})
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    item = data["item"]
    price = data["price"]
    loan_term = data["loan_term"]
    down_payment = data["down_payment"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT income, expenses, savings FROM Financials WHERE user_id = %s",
        (user_id,),
    )
    financials = cursor.fetchone()
    if not financials:
        conn.close()
        return jsonify({"error": "Financial data not found"}), 404

    income, expenses, savings = financials
    available_income = income - expenses
    monthly_payment = (price - down_payment) / max(loan_term, 1)
    affordable = monthly_payment <= available_income

    result = {
        "monthly_payment": monthly_payment,
        "savings_goal": {
            "amount_per_month": max(0, (price - savings - down_payment) / 12),
            "duration": 12 if savings < price - down_payment else 0,
        },
        "affordable": affordable,
    }

    cursor.execute(
        """
        INSERT INTO AffordabilityAnalysis
            (user_id, item, price, loan_term, down_payment, monthly_payment,
             savings_goal, result, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING analysis_id
        """,
        (
            user_id,
            item,
            price,
            loan_term,
            down_payment,
            monthly_payment,
            result["savings_goal"],
            result,
            datetime.utcnow(),
            datetime.utcnow(),
        ),
    )
    analysis_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    result["analysis_id"] = analysis_id
    return jsonify({"status": "success", "data": result}), 200


@financial_blueprint.route("/users/<int:user_id>/transactions", methods=["POST"])
@token_required
def log_transaction(user_id: int):
    try:
        data = TransactionSchema().load(request.json or {})
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Transactions
            (user_id, amount, category, description, transaction_date,
             linked_expense_id, linked_order_id, linked_debt_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING transaction_id
        """,
        (
            user_id,
            data["amount"],
            data["category"],
            data.get("description"),
            data.get("transaction_date", datetime.utcnow()),
            data.get("linked_expense_id"),
            data.get("linked_order_id"),
            data.get("linked_debt_id"),
        ),
    )
    transaction_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "transaction_id": transaction_id}), 201


@financial_blueprint.route("/users/<int:user_id>/transactions", methods=["GET"])
@token_required
def get_transactions(user_id: int):
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    category = request.args.get("category")
    limit = request.args.get("limit", type=int, default=10)
    offset = request.args.get("offset", type=int, default=0)

    query = """
        SELECT transaction_id, amount, category, description, transaction_date,
               linked_expense_id, linked_order_id, linked_debt_id
        FROM Transactions
        WHERE user_id = %s
    """
    params = [user_id]

    if start_date and end_date:
        query += " AND transaction_date BETWEEN %s AND %s"
        params.extend([start_date, end_date])

    if category:
        query += " AND category = %s"
        params.append(category)

    query += " ORDER BY transaction_date DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    transactions = [
        {
            "transaction_id": r[0],
            "amount": r[1],
            "category": r[2],
            "description": r[3],
            "transaction_date": r[4],
            "linked_expense_id": r[5],
            "linked_order_id": r[6],
            "linked_debt_id": r[7],
        }
        for r in rows
    ]
    return jsonify({"status": "success", "data": transactions}), 200

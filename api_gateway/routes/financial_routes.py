from flask import Blueprint, request, jsonify
from shared.db_connection import get_db_connection
import datetime
from api_gateway.middleware.authentication import token_required
from functools import wraps
from marshmallow import Schema, fields, ValidationError

financial_blueprint = Blueprint("financial_service", __name__)


# Schema for input validation
class AffordabilitySchema(Schema):
    item = fields.Str(required=True)
    price = fields.Float(required=True)
    loan_term = fields.Int(required=True)
    down_payment = fields.Float(required=True)

class TransactionSchema(Schema):
    amount = fields.Float(required=True)
    category = fields.Str(required=True)
    description = fields.Str(missing=None)
    transaction_date = fields.DateTime(missing=datetime.datetime.utcnow)
    linked_expense_id = fields.Int(missing=None)
    linked_order_id = fields.Int(missing=None)
    linked_debt_id = fields.Int(missing=None)

# GET /users/{user_id}/financials
@financial_blueprint.route("/users/<int:user_id>/financials", methods=["GET"])
@token_required
def get_financial_summary(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT income, expenses, savings, debts FROM Financials WHERE user_id = %s
        """,
        (user_id,),
    )
    financials = cursor.fetchone()
    conn.close()

    if not financials:
        return jsonify({"error": "Financial data not found"}), 404

    financial_summary = {
        "income": financials[0],
        "expenses": financials[1],
        "savings": financials[2],
        "debts": financials[3],
    }
    return jsonify({"status": "success", "data": financial_summary}), 200

# POST /users/{user_id}/financials/affordability
@financial_blueprint.route("/users/<int:user_id>/financials/affordability", methods=["POST"])
@token_required
def analyze_affordability(user_id):
    try:
        data = request.json
        AffordabilitySchema().load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    item = data["item"]
    price = data["price"]
    loan_term = data["loan_term"]
    down_payment = data["down_payment"]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT income, expenses, savings FROM Financials WHERE user_id = %s
        """,
        (user_id,),
    )
    financials = cursor.fetchone()

    if not financials:
        conn.close()
        return jsonify({"error": "Financial data not found"}), 404

    income, expenses, savings = financials
    available_income = income - expenses
    monthly_payment = (price - down_payment) / loan_term
    affordable = monthly_payment <= available_income

    result = {
        "monthly_payment": monthly_payment,
        "savings_goal": {
            "amount_per_month": max(0, (price - savings - down_payment) / 12),
            "duration": 12 if savings < price - down_payment else 0,
        },
        "affordable": affordable,
    }

    # Insert affordability analysis result into Affordability Analysis table
    cursor.execute(
        """
        INSERT INTO AffordabilityAnalysis (user_id, item, price, loan_term, down_payment, monthly_payment, savings_goal, result, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING analysis_id
        """,
        (user_id, item, price, loan_term, down_payment, monthly_payment, result["savings_goal"], result, datetime.datetime.utcnow(), datetime.datetime.utcnow()),
    )
    analysis_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    result["analysis_id"] = analysis_id
    return jsonify({"status": "success", "data": result}), 200

# POST /users/{user_id}/transactions
@financial_blueprint.route("/users/<int:user_id>/transactions", methods=["POST"])
@token_required
def log_transaction(user_id):
    try:
        data = request.json
        TransactionSchema().load(data)
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400

    amount = data["amount"]
    category = data["category"]
    description = data.get("description")
    transaction_date = data.get("transaction_date", datetime.datetime.utcnow())
    linked_expense_id = data.get("linked_expense_id")
    linked_order_id = data.get("linked_order_id")
    linked_debt_id = data.get("linked_debt_id")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Transactions (user_id, amount, category, description, transaction_date, linked_expense_id, linked_order_id, linked_debt_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING transaction_id
        """,
        (user_id, amount, category, description, transaction_date, linked_expense_id, linked_order_id, linked_debt_id),
    )
    transaction_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "transaction_id": transaction_id}), 201

# GET /users/{user_id}/transactions
@financial_blueprint.route("/users/<int:user_id>/transactions", methods=["GET"])
@token_required
def get_transactions(user_id):
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    category = request.args.get("category")
    limit = request.args.get("limit", type=int, default=10)
    offset = request.args.get("offset", type=int, default=0)

    query = "SELECT transaction_id, amount, category, description, transaction_date, linked_expense_id, linked_order_id, linked_debt_id FROM Transactions WHERE user_id = %s"
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
    transactions = cursor.fetchall()
    conn.close()

    transaction_list = [
        {
            "transaction_id": t[0],
            "amount": t[1],
            "category": t[2],
            "description": t[3],
            "transaction_date": t[4],
            "linked_expense_id": t[5],
            "linked_order_id": t[6],
            "linked_debt_id": t[7],
        }
        for t in transactions
    ]

    return jsonify({"status": "success", "data": transaction_list}), 200

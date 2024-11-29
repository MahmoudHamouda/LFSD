from flask import Blueprint, request, jsonify
from db import get_db_session
from models import Transaction, AffordabilityAnalysis, RecurringExpense

financial_blueprint = Blueprint("financial_service", __name__)

# GET /users/<user_id>/financials
@financial_blueprint.route("/<int:user_id>/financials", methods=["GET"])
def get_financial_summary(user_id):
    session = get_db_session()
    transactions = session.query(Transaction).filter_by(user_id=user_id).all()
    recurring_expenses = session.query(RecurringExpense).filter_by(user_id=user_id).all()
    session.close()

    transaction_data = [
        {"transaction_id": t.transaction_id, "amount": t.amount, "category": t.category, "timestamp": t.timestamp}
        for t in transactions
    ]
    recurring_expense_data = [
        {"expense_id": e.expense_id, "amount": e.amount, "category": e.category, "frequency": e.frequency}
        for e in recurring_expenses
    ]

    return jsonify({"transactions": transaction_data, "recurring_expenses": recurring_expense_data}), 200

# POST /users/<user_id>/financials/affordability
@financial_blueprint.route("/<int:user_id>/financials/affordability", methods=["POST"])
def perform_affordability_analysis(user_id):
    data = request.json
    item = data.get("item")
    price = data.get("price")
    loan_term = data.get("loan_term")
    down_payment = data.get("down_payment")

    if not item or price is None:
        return jsonify({"error": "Item and price are required."}), 400

    monthly_payment = (price - down_payment) / loan_term if loan_term else price
    affordable = "Yes" if monthly_payment < 0.3 * price else "No"

    session = get_db_session()
    analysis = AffordabilityAnalysis(
        user_id=user_id,
        item=item,
        price=price,
        loan_term=loan_term,
        down_payment=down_payment,
        monthly_payment=monthly_payment,
        affordable=affordable,
    )
    session.add(analysis)
    session.commit()
    session.close()

    return jsonify({"monthly_payment": monthly_payment, "affordable": affordable}), 201

# POST /users/<user_id>/transactions
@financial_blueprint.route("/<int:user_id>/transactions", methods=["POST"])
def add_transaction(user_id):
    data = request.json
    amount = data.get("amount")
    category = data.get("category")
    description = data.get("description")

    if not amount or not category:
        return jsonify({"error": "Amount and category are required."}), 400

    session = get_db_session()
    transaction = Transaction(user_id=user_id, amount=amount, category=category, description=description)
    session.add(transaction)
    session.commit()
    session.close()

    return jsonify({"message": "Transaction added successfully"}), 201

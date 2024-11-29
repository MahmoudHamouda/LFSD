from flask import Blueprint, request, jsonify
from shared.openai_client import generate_response
from shared.db_connection import get_db_connection
from shared.config import get_config
from shared.authentication import validate_jwt  # Assuming there's a function for JWT validation
from shared.nosql_db import save_chat_log  # Assuming NoSQL integration for chat logs
from shared.logging import get_logger
from shared.rate_limiting import check_rate_limit

logger = get_logger(__name__)

chat_blueprint = Blueprint("chat_service", __name__)

# POST /users/{user_id}/chat
@chat_blueprint.route("/users/<int:user_id>/chat", methods=["POST"])
def handle_chat(user_id):
    # Check rate limit for user
    if not check_rate_limit(user_id):
        logger.warning(f"Rate limit exceeded for user_id: {user_id}")
        return jsonify({"error": "Rate limit exceeded"}), 429

    # Validate JWT Token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not validate_jwt(auth_header):
        logger.error(f"Unauthorized access attempt for user_id: {user_id}")
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    query = data.get("query")

    if not query:
        logger.error(f"Query is missing for user_id: {user_id}")
        return jsonify({"error": "Query is required"}), 400

    # Fetch user context (mocking database call for simplicity)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT u.income, u.expenses, s.balance as savings, d.principal as debts, u.preferences
            FROM Users u
            LEFT JOIN SavingsAccounts s ON u.user_id = s.user_id
            LEFT JOIN Debts d ON u.user_id = d.user_id
            WHERE u.user_id = %s
            """,
            (user_id,),
        )
        context = cursor.fetchone()
    except Exception as e:
        logger.error(f"Database error for user_id {user_id}: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

    if not context:
        logger.error(f"User context not found for user_id: {user_id}")
        return jsonify({"error": "User context not found"}), 404

    # Format context for OpenAI
    formatted_context = f"""
    Financial Summary:
    - Monthly income: {context[0]}
    - Monthly expenses: {context[1]}
    - Savings: {context[2]}
    - Debts: {context[3]}
    User Preferences: {context[4]}
    """

    # Check for affordability-related queries
    if "affordability" in query.lower():
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT item, price, monthly_payment, result
                FROM AffordabilityAnalysis
                WHERE user_id = %s
                """,
                (user_id,),
            )
            affordability_data = cursor.fetchone()
        except Exception as e:
            logger.error(f"Database error for affordability analysis for user_id {user_id}: {str(e)}")
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            if conn:
                conn.close()

        if affordability_data:
            affordability_context = f"""
            You recently performed an affordability analysis for {affordability_data[0]}:
            - Price: {affordability_data[1]}
            - Monthly Payment: {affordability_data[2]}
            - Result: {affordability_data[3]}
            """
            formatted_context += affordability_context

    # Generate a response using OpenAI
    try:
        response = generate_response(query, formatted_context)
    except Exception as e:
        logger.error(f"Failed to generate response for user_id {user_id}: {str(e)}")
        return jsonify({"error": f"Failed to generate response: {str(e)}"}), 500

    # Save chat log to NoSQL database
    try:
        save_chat_log(user_id, {"type": "User", "content": query})
        save_chat_log(user_id, {"type": "Assistant", "content": response})
    except Exception as e:
        logger.error(f"Failed to save chat log for user_id {user_id}: {str(e)}")
        return jsonify({"error": f"Failed to save chat log: {str(e)}"}), 500

    logger.info(f"Chat successfully handled for user_id: {user_id}")
    return jsonify({"status": "success", "response": response}), 200

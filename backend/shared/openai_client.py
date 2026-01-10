import openai
import logging
import os

# Initialize logger
logger = logging.getLogger("openai_client")

# Load OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY", "your_openai_api_key")

# Model configuration
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")


def generate_response(user_input, context=None, model=DEFAULT_MODEL):
    """
    Generate a response for a user input using OpenAI's GPT model.
    :param user_input: User's input message.
    :param context: Optional context to guide the response.
    :param model: The OpenAI model to use (default is GPT-4).
    :return: Dictionary with 'content', 'usage' (input_tokens, output_tokens), and 'model'.
    """
    try:
        logger.info(f"Generating response for input: {user_input}")

        messages = [{"role": "user", "content": user_input}]
        if context:
            messages.insert(0, {"role": "system", "content": context})

        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=150,
            temperature=0.7,
        )

        content = response["choices"][0]["message"]["content"]
        usage = {
            "input_tokens": response.get("usage", {}).get("prompt_tokens"),
            "output_tokens": response.get("usage", {}).get("completion_tokens"),
            "total_tokens": response.get("usage", {}).get("total_tokens")
        }
        
        return {
            "content": content,
            "usage": usage,
            "model": response.get("model", model)
        }
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return {
            "content": "I'm sorry, I couldn't process your request.",
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "model": model
        }


def summarize_chat(chat_history, model=DEFAULT_MODEL):
    """
    Summarize a chat session using OpenAI's GPT model.
    :param chat_history: A list of chat messages as strings.
    :param model: The OpenAI model to use (default is GPT-4).
    :return: Dictionary with 'content', 'usage', and 'model'.
    """
    try:
        logger.info(
            f"Summarizing chat history with {len(chat_history)} messages"
        )

        combined_history = "\n".join(chat_history)
        summary_prompt = (
            f"Summarize the following conversation:\n{combined_history}"
        )

        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": summary_prompt}],
            max_tokens=200,
            temperature=0.5,
        )

        return {
            "content": response["choices"][0]["message"]["content"],
            "usage": {
                "input_tokens": response.get("usage", {}).get("prompt_tokens"),
                "output_tokens": response.get("usage", {}).get("completion_tokens"),
                "total_tokens": response.get("usage", {}).get("total_tokens")
            },
            "model": response.get("model", model)
        }
    except Exception as e:
        logger.error(f"Error summarizing chat: {e}")
        return {
            "content": "I couldn't generate a summary for this session.",
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "model": model
        }


def generate_recommendation(context, preferences, model=DEFAULT_MODEL):
    """
    Generate a recommendation based on context and preferences using OpenAI's GPT model.
    :param context: The user context, e.g., "dinner with friends."
    :param preferences: User preferences as a dictionary, e.g., {"cuisine": "Italian"}.
    :param model: The OpenAI model to use (default is GPT-4).
    :return: Dictionary with 'content', 'usage', and 'model'.
    """
    try:
        logger.info(
            f"Generating recommendation for context: {context} with preferences: {preferences}"
        )

        preferences_str = ", ".join(
            [f"{key}: {value}" for key, value in preferences.items()]
        )
        prompt = f"Based on the context '{context}' and preferences ({preferences_str}), provide a personalized recommendation."

        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7,
        )

        return {
            "content": response["choices"][0]["message"]["content"],
            "usage": {
                "input_tokens": response.get("usage", {}).get("prompt_tokens"),
                "output_tokens": response.get("usage", {}).get("completion_tokens"),
                "total_tokens": response.get("usage", {}).get("total_tokens")
            },
            "model": response.get("model", model)
        }
    except Exception as e:
        logger.error(f"Error generating recommendation: {e}")
        return {
            "content": "I'm sorry, I couldn't generate a recommendation at this time.",
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            "model": model
        }


def generate_title(first_message, model=DEFAULT_MODEL):
    """
    Generate a short, human-readable title for a conversation based on the first message.
    :param first_message: The first message of the conversation.
    :param model: The OpenAI model to use.
    :return: A short title string.
    """
    try:
        logger.info(f"Generating title for message: {first_message[:50]}...")
        prompt = f"Generate a short, concise title (max 5 words) for a conversation that starts with: \"{first_message}\". Return only the title."
        
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.5,
        )

        return response["choices"][0]["message"]["content"].strip().strip('"')
    except Exception as e:
        logger.error(f"Error generating title: {e}")
        return "New Conversation"


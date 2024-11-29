### **Summary for Creating `utils.py` in `shared/`**

The **`utils.py`** file provides utility functions that are shared across all microservices. These include input validation, data formatting, JSON handling, and other reusable helper methods that ensure consistency and reduce redundancy.

---

### **Features to Include in `utils.py`**

1. **Input Validation**
   - Validate required fields in incoming requests.
   - Ensure proper data types and constraints for API inputs.

2. **Response Formatting**
   - Standardize API responses with success or error messages.

3. **Date and Time Utilities**
   - Format and parse dates for consistent usage across services.

4. **JSON Utility**
   - Safely handle JSON serialization and deserialization.

5. **Error Handling**
   - Centralized error logging and standardized error responses.

6. **General Helpers**
   - Add commonly used functions like generating UUIDs or hashing data.

---

### **Code for `utils.py`**

```python
import json
from datetime import datetime
import logging
import uuid

# Initialize logger
logger = logging.getLogger("utils")

# Input Validation
def validate_required_fields(data, required_fields):
    """
    Validate that the required fields are present in the data.
    :param data: The input dictionary to validate.
    :param required_fields: A list of required field names.
    :return: Tuple (is_valid: bool, error: str)
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    return True, None

# Response Formatting
def format_response(status, message, data=None):
    """
    Standardize API responses.
    :param status: "success" or "error"
    :param message: The message string.
    :param data: Optional data to include in the response.
    :return: Formatted dictionary.
    """
    response = {"status": status, "message": message}
    if data is not None:
        response["data"] = data
    return response

# Date and Time Utilities
def format_datetime(dt, format_str="%Y-%m-%d %H:%M:%S"):
    """
    Format a datetime object as a string.
    :param dt: Datetime object.
    :param format_str: Format string.
    :return: Formatted date string.
    """
    return dt.strftime(format_str)

def parse_datetime(date_str, format_str="%Y-%m-%d %H:%M:%S"):
    """
    Parse a date string into a datetime object.
    :param date_str: The date string to parse.
    :param format_str: Format string.
    :return: Datetime object.
    """
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError as e:
        logger.error(f"Error parsing datetime: {e}")
        return None

# JSON Utilities
def safe_json_loads(json_string):
    """
    Safely parse a JSON string into a dictionary.
    :param json_string: JSON string to parse.
    :return: Parsed dictionary or None if invalid.
    """
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {e}")
        return None

def safe_json_dumps(data):
    """
    Safely serialize a dictionary into a JSON string.
    :param data: Dictionary to serialize.
    :return: JSON string or None if invalid.
    """
    try:
        return json.dumps(data)
    except (TypeError, ValueError) as e:
        logger.error(f"Error serializing JSON: {e}")
        return None

# General Helpers
def generate_uuid():
    """
    Generate a unique UUID.
    :return: UUID string.
    """
    return str(uuid.uuid4())

def hash_password(password):
    """
    Hash a password for secure storage.
    :param password: Plain text password.
    :return: Hashed password.
    """
    import hashlib
    salt = "your_salt_here"  # Replace with a secure salt
    return hashlib.sha256((password + salt).encode()).hexdigest()
```

---

### **Examples of Usage**

1. **Input Validation**
   ```python
   from shared.utils import validate_required_fields

   data = {"name": "John", "email": "john@example.com"}
   required_fields = ["name", "email", "password"]

   is_valid, error = validate_required_fields(data, required_fields)
   if not is_valid:
       print(error)  # Output: Missing required fields: password
   ```

2. **Response Formatting**
   ```python
   from shared.utils import format_response

   success_response = format_response("success", "User created", {"user_id": 123})
   print(success_response)
   # Output: {"status": "success", "message": "User created", "data": {"user_id": 123}}
   ```

3. **Date Utilities**
   ```python
   from shared.utils import format_datetime, parse_datetime

   now = datetime.now()
   formatted_date = format_datetime(now)
   print(formatted_date)  # Output: 2024-11-24 12:30:45

   parsed_date = parse_datetime("2024-11-24 12:30:45")
   print(parsed_date)  # Output: 2024-11-24 12:30:45
   ```

4. **JSON Utilities**
   ```python
   from shared.utils import safe_json_loads, safe_json_dumps

   json_str = '{"key": "value"}'
   data = safe_json_loads(json_str)
   print(data)  # Output: {"key": "value"}

   json_str_invalid = '{"key": value}'
   data = safe_json_loads(json_str_invalid)
   print(data)  # Output: None
   ```

5. **General Helpers**
   ```python
   from shared.utils import generate_uuid, hash_password

   print(generate_uuid())  # Output: A unique UUID, e.g., "c56a4180-65aa-42ec-a945-5fd21dec0538"

   hashed_password = hash_password("my_secure_password")
   print(hashed_password)  # Output: A hashed string
   ```

---

### **Next Steps in OpenAI Canva**

1. **Create the file `shared/utils.py`.**
2. Copy the provided code into the file.
3. Test each utility function in isolation to ensure correctness.
4. Integrate utility functions into the microservices where needed.

Would you like assistance testing or integrating these utilities?
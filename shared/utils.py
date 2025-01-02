from shared.utils import validate_required_fields, format_response, format_datetime, generate_uuid

# Test 1: Validate Required Fields
data = {"name": "Alice", "email": "alice@example.com"}
required = ["name", "email", "password"]
is_valid, error = validate_required_fields(data, required)
assert not is_valid and "password" in error

# Test 2: Format Response
response = format_response("success", "Operation completed", {"key": "value"})
assert response["status"] == "success" and response["data"]["key"] == "value"

# Test 3: Generate UUID
unique_id = generate_uuid()
assert len(unique_id) == 36  # UUID length

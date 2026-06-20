"""
Test script for SSE upload endpoint
"""
import requests
import json
import base64

# Read a test PDF
with open(r"C:\Users\hmahm\Downloads\Dec Bank Statment.pdf", "rb") as f:
    pdf_content = base64.b64encode(f.read()).decode('utf-8')

# Prepare request
data = {
    "files": [
        {
            "filename": "test_statement.pdf",
            "content": pdf_content
        }
    ]
}

# Make SSE request
print("Connecting to SSE endpoint...")
response = requests.post(
    "http://localhost:8003/api/onboarding/upload-statement-stream",
    json=data,
    stream=True,
    headers={"Accept": "text/event-stream"}
)

print(f"Status Code: {response.status_code}\n")

if response.status_code == 200:
    print("Receiving events:\n")
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            print(decoded_line)
            
            # Parse and display data nicely
            if decoded_line.startswith('data: '):
                try:
                    event_data = json.loads(decoded_line[6:])
                    print(f"  → {json.dumps(event_data, indent=2)}\n")
                except:
                    pass
else:
    print(f"Error: {response.text}")

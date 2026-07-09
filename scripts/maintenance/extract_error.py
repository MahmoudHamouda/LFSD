import re

try:
    with open('trace_final_4.log', 'r', encoding='utf-16-le') as f:
        content = f.read()
        
    # Look for 'M': '...'
    m = re.search(r"'M': '(.*?)'", content)
    if m:
        print(f"FOUND ERROR MESSAGE: {m.group(1)}")
    else:
        print("No 'M' field found in log.")
        
except Exception as e:
    print(f"Error: {e}")

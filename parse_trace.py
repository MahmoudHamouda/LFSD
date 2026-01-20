import json
import re

try:
    with open('trace_final.log', 'r', encoding='utf-16-le') as f:
        content = f.read()
        # Find the JSON line
        # look for {"detail":
        start = content.find('{"detail":')
        if start != -1:
            blob = content[start:].strip()
            # It might be followed by other junk, so try to parse
            try:
                data = json.loads(blob)
                print(data['detail'])
            except:
                print(blob[:300])
        else:
            print("No JSON found")
except Exception as e:
    print(f"Error: {e}")

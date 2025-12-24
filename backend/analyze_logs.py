import json
import os

def analyze_logs():
    log_file = "app.log"
    if not os.path.exists(log_file):
        print("Log file not found.")
        return

    print(f"Reading {log_file}...")
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    print(f"Total lines: {len(lines)}")
    
    # Check last 500 lines for our specific markers
    found_errors = 0
    # Also check for standard Tracebacks
    capturing_traceback = False
    
    for i, line in enumerate(lines[-1000:]):
        if "[AUTH-ERROR]" in line or "Signup Error" in line or "CRITICAL ERROR" in line:
            print(f"\n--- Error found at line -{1000-i} ---")
            print(line.strip())
            found_errors += 1
            capturing_traceback = True
        elif capturing_traceback:
            # simple heuristic to print following indented lines (traceback)
            if line.startswith(" ") or line.startswith("\t") or line.strip().startswith("File"):
                print(line.strip())
            else:
                capturing_traceback = False

    if found_errors == 0:
        print("No [AUTH-ERROR] or CRITICAL ERROR found in the last 1000 lines.")

if __name__ == "__main__":
    analyze_logs()

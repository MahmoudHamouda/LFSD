import subprocess
import time
import requests
import sys

def run_test():
    print("Starting backend...")
    env = {"PYTHONPATH": ".", "ENV": "dev", "DEBUG": "true"}
    # Merge with current env
    import os
    env.update(os.environ)
    
    proc = subprocess.Popen(
        [sys.executable, "backend/app.py"],
        cwd=".",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    try:
        # Wait for backend to start
        print("Waiting for backend to bind to 8003...")
        start_time = time.time()
        while time.time() - start_time < 120:
            try:
                # Use a simpler endpoint to check if it's binding
                r = requests.get("http://localhost:8003/", timeout=1)
                # If we get any response, even a 404, the server is listening
                print(f"Backend contacted! Status: {r.status_code}")
                break
            except requests.exceptions.ConnectionError:
                pass
            except Exception as e:
                print(f"Waiting... {type(e).__name__}")
                pass
            if proc.poll() is not None:
                print(f"Backend process terminated early with return code {proc.returncode}")
                break
            time.sleep(1)
        else:
            print("Backend failed to start in time.")
            proc.terminate()
            return

        # Run verification
        print("Running verification...")
        headers = {"X-Test-User-Id": "verify-user-123"}
        r = requests.get("http://localhost:8003/api/growth/entitlements", headers=headers)
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text}")
        
    finally:
        print("Stopping backend...")
        proc.terminate()
        # Read the last bits of output
        out, _ = proc.communicate()
        print("--- BACKEND LOGS ---")
        with open("crash.log", "w", encoding="utf-8") as f:
            f.write(out)
        print("Logs written to crash.log")

if __name__ == "__main__":
    run_test()

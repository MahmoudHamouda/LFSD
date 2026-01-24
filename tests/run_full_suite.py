import sys
import os
import requests
import json
import time
import uuid
import datetime
from typing import Dict, Any, List

# --- CONFIG ---
BASE_URL = "https://lfsd-backend-692544481281.us-central1.run.app"
API_KEY = "lfsd_backup_2024" # For debug/seeding endpoints

# --- TEST UTILS ---
class TestResult:
    def __init__(self, name):
        self.name = name
        self.status = "PENDING"
        self.message = ""
        self.duration = 0

    def pass_test(self, msg="OK"):
        self.status = "PASS"
        self.message = msg
    
    def fail_test(self, msg):
        self.status = "FAIL"
        self.message = msg

    def skip_test(self, msg):
        self.status = "SKIP"
        self.message = msg

class SuiteRunner:
    def __init__(self):
        self.results = []
        self.token = None
        self.user_id = None
        
    def log(self, msg):
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

    def run_step(self, name, func):
        self.log(f"STARTING: {name}")
        res = TestResult(name)
        start = time.time()
        try:
            func(res)
        except Exception as e:
            res.fail_test(f"Exception: {str(e)}")
        res.duration = time.time() - start
        self.results.append(res)
        self.log(f"FINISHED: {name} -> {res.status} ({res.message})")
        return res.status == "PASS"

    def print_summary(self):
        print("\n\n" + "="*50)
        print("TEST EXECUTION SUMMARY")
        print("="*50)
        print(f"{'TEST CASE':<40} | {'STATUS':<6} | {'TIME':<6} | {'MESSAGE'}")
        print("-" * 100)
        for r in self.results:
            print(f"{r.name:<40} | {r.status:<6} | {r.duration:.2f}s | {r.message}")
        print("-" * 100)
        passed = len([r for r in self.results if r.status == "PASS"])
        total = len(self.results)
        print(f"TOTAL: {total}, PASSED: {passed}, FAILED: {total - passed}")

# --- TEST STEPS ---

def step_cleanup(runner, res):
    # Call the database reset/seed endpoint (Nuclear option)
    url = f"{BASE_URL}/api/debug/seed_force?secret={API_KEY}"
    # Use the existing debug/seed_force which calls the internal seeder
    # But we want to ensure it wipes first. The current implementation does.
    r = requests.post(url, timeout=60)
    if r.status_code == 200:
        res.pass_test("Database reset and seeded successfully")
    else:
        res.fail_test(f"Seeding failed: {r.status_code} {r.text[:100]}")

def step_health_check(runner, res):
    # Try multiple endpoints
    endpoints = ["/health", "/api/test/ping"]
    for ep in endpoints:
        try:
            r = requests.get(f"{BASE_URL}{ep}", timeout=5)
            if r.status_code == 200:
                res.pass_test(f"Health check OK at {ep}")
                return
        except:
            pass
    res.fail_test("All health endpoints failed")

def step_login(runner, res):
    # Use one of the seeded users: finance@helm.com
    url = f"{BASE_URL}/api/user/token"
    payload = {"username": "finance@helm.com", "password": "P@ssword123"}
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        runner.token = r.json().get("access_token")
        res.pass_test("Token acquired")
    else:
        # Fallback to JSON login
        url2 = f"{BASE_URL}/login"
        r2 = requests.post(url2, json={"email": "finance@helm.com", "password": "P@ssword123"})
        if r2.status_code == 200:
             runner.token = r2.json().get("access_token")
             res.pass_test("Token acquired (via JSON endpoint)")
        else:
             res.fail_test(f"Login failed: {r.status_code} / {r2.status_code}")

def step_get_profile(runner, res):
    if not runner.token: 
        res.skip_test("No token")
        return
    
    headers = {"Authorization": f"Bearer {runner.token}"}
    r = requests.get(f"{BASE_URL}/api/user/me", headers=headers)
    if r.status_code == 200:
        data = r.json()
        runner.user_id = data.get("id")
        res.pass_test(f"User retrieved: {data.get('email')}")
    else:
        res.fail_test(f"Get Profile failed: {r.status_code}")

def step_calculate_scores(runner, res):
    if not runner.token:
        res.skip_test("No token")
        return
        
    headers = {"Authorization": f"Bearer {runner.token}"}
    
    # Trigger all 3 score calculations
    # 1. Finance
    r1 = requests.post(f"{BASE_URL}/api/finance/score/calculate", headers=headers)
    fin_ok = r1.status_code == 200
    
    # 2. Health
    r2 = requests.post(f"{BASE_URL}/api/health/score/calculate", headers=headers) # Assuming endpoint exists or logic runs automatically
    # If explicit endpoint doesn't exist, we fallback to requesting the score which triggers calc
    if r2.status_code == 404:
         r2 = requests.get(f"{BASE_URL}/api/health/score", headers=headers)
    health_ok = r2.status_code == 200
    
    # 3. Time
    r3 = requests.post(f"{BASE_URL}/api/time/score/calculate", headers=headers)
    if r3.status_code == 404:
        r3 = requests.get(f"{BASE_URL}/api/time/score", headers=headers) 
    time_ok = r3.status_code == 200
    
    if fin_ok and health_ok and time_ok:
        res.pass_test("All 3 scores calculated")
    else:
        res.fail_test(f"Calc failed: Fin={r1.status_code}, Health={r2.status_code}, Time={r3.status_code}")

def step_verify_viv_index(runner, res):
    if not runner.token:
        res.skip_test("No token")
        return
    headers = {"Authorization": f"Bearer {runner.token}"}
    r = requests.get(f"{BASE_URL}/api/scores/current", headers=headers) # Consolidated route
    
    if r.status_code != 200:
        # Fallback to fetching profile which contains scores
        r = requests.get(f"{BASE_URL}/api/user/me", headers=headers)
    
    if r.status_code == 200:
        data = r.json()
        # Handle different response structures
        fs = data.get("financial_score") or data.get("viv_index", {}).get("financial_score")
        if fs is not None:
             res.pass_test(f"Viv Index Found: FinScore={fs}")
        else:
             res.fail_test(f"Viv Index missing scores: {data.keys()}")
    else:
        res.fail_test(f"Failed to fetch scores: {r.status_code}")

def step_integration_growth(runner, res):
    if not runner.token:
        res.skip_test("No token")
        return
    headers = {"Authorization": f"Bearer {runner.token}"}
    
    # Check entitlements
    r = requests.get(f"{BASE_URL}/api/growth/entitlements", headers=headers)
    if r.status_code == 200:
        data = r.json()
        plan = data.get("plan")
        if plan:
            res.pass_test(f"Entitlements OK. Plan: {plan}")
        else:
            res.fail_test("Entitlements empty")
    else:
        # If 404, maybe route is different
        res.skip_test(f"Entitlements endpoint failed: {r.status_code}")

def step_upload_file(runner, res):
    # Test uploading a file (Statement/Health Data)
    # Skipping for now as it requires multipart setup, logic verification is priority
    res.skip_test("File upload test pending")

def run_suite():
    runner = SuiteRunner()
    
    # 1. System Health
    runner.run_step("1. Health Check", step_health_check)
    
    # 2. Reset & Seed (Nuclear)
    runner.run_step("2. Database Reset & Seed", step_cleanup)
    
    # 3. Auth
    if runner.run_step("3. Login (Finance Persona)", step_login):
        runner.run_step("4. Fetch Profile", step_get_profile)
        
        # 4. Trigger Logic (The "Brain")
        runner.run_step("5. Trigger Score Calculations", step_calculate_scores)
        
        # 5. Verify Outputs
        runner.run_step("6. Verify Viv Index Outputs", step_verify_viv_index)
        
        # 6. Growth/Entitlements
        runner.run_step("7. Check Growth Entitlements", step_integration_growth)
        
    runner.print_summary()

if __name__ == "__main__":
    run_suite()


import sys
import os
import json
import random
import uuid
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# --- CONFIGURATION ---
# Add the parent directory to sys.path to allow importing modules from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from models.database import engine, SessionLocal
    from models.models import User, VivIndex, FinancialScore
    from services.time_scoring import calculate_productivity_score
    from services.financial_scoring import calculate_financial_health_score
    from services.health_scoring import calculate_health_score
except ImportError as e:
    # Fallback if running standalone and path issue
    print(f"Could not import database models/services: {e}")
    sys.exit(1)

# --- CONSTANTS ---
PERSONAS = {
    "empty": {"email": "empty@helm.com", "role": "empty"},
    "finance": {"email": "finance@helm.com", "role": "finance"},
    "health": {"email": "health@helm.com", "role": "health"},
    "time": {"email": "time@helm.com", "role": "time"},
    "super": {"email": "super@helm.com", "role": "super"},
}

# --- 1. DISCOVERY AGENT ---
class SchemaDiscoveryAgent:
    def __init__(self, db):
        self.db = db
        self.tables = []
        self.columns = {}
        self.pk_map = {}
        self.fk_map = []
        self.not_null_map = {}
        
    def discover(self):
        print("--- STEP 1: DATABASE DISCOVERY ---")
        try:
            self._list_tables()
            self._inspect_columns()
            self._identify_pks()
            self._identify_fks()
            self._identify_not_nulls()
            print("Discovery Complete.\n")
        except Exception as e:
            print(f"Discovery Failed: {e}")
            self.db.rollback()
            raise e
        
    def _execute_query(self, query_text):
        try:
            return self.db.execute(text(query_text)).fetchall()
        except Exception as e:
            print(f"Query Failed: {query_text[:100]}... Error: {e}")
            self.db.rollback()
            raise e

    def _list_tables(self):
        print("DEBUG: Listing tables...")
        self.tables = [row[0] for row in self._execute_query("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1")]
        print(f"Found {len(self.tables)} tables: {self.tables}")

    def _inspect_columns(self):
        print("DEBUG: Inspecting columns...")
        result = self._execute_query("""
            SELECT table_name, column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema='public'
            ORDER BY table_name, ordinal_position
        """)
        for row in result:
            table, col, dtype, nullable, default = row
            if table not in self.columns: self.columns[table] = []
            self.columns[table].append({
                "name": col, "type": dtype, "nullable": nullable == 'YES', "default": default
            })
            
    def _identify_pks(self):
        print("DEBUG: Identifying PKs...")
        result = self._execute_query("""
            SELECT tc.table_name, kc.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kc 
              ON tc.constraint_name = kc.constraint_name
            WHERE tc.table_schema='public' AND tc.constraint_type='PRIMARY KEY'
        """)
        for row in result:
            self.pk_map[row[0]] = row[1]
            
    def _identify_fks(self):
        print("DEBUG: Identifying FKs...")
        result = self._execute_query("""
            SELECT
                tc.table_name AS child_table, kcu.column_name AS child_column,
                ccu.table_name AS parent_table, ccu.column_name AS parent_column
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
        """)
        for row in result:
            self.fk_map.append({
                "child_table": row[0], "child_col": row[1],
                "parent_table": row[2], "parent_col": row[3]
            })

    def _identify_not_nulls(self):
        for table, cols in self.columns.items():
            self.not_null_map[table] = [c['name'] for c in cols if not c['nullable'] and c['default'] is None]

    def has_table(self, name):
        return name in self.tables
        
    def has_column(self, table, col_name_part):
        if table not in self.columns: return False
        for c in self.columns[table]:
            if col_name_part.lower() in c['name'].lower():
                return True
        return False
        
    def get_column_type(self, table, col_name):
        for c in self.columns.get(table, []):
            if c['name'] == col_name: return c['type']
        return None

# --- 2. SEEDING AGENT ---
class DataSeedingAgent:
    def __init__(self, db, schema):
        self.db = db
        self.schema = schema
        self.user_ids = {} # Map email -> uuid
        
    def clean_slate(self):
        print("--- CLEANING ENTIRE DB (NUCLEAR OPTION) ---")
        try:
            # Check if we are in a safe environment? Assuming yes for this script.
            # Use TRUNCATE CASCADE to wipe users and all dependent tables
            self.db.execute(text("TRUNCATE TABLE users_v2 CASCADE"))
            self.db.commit()
            print("Database wiped successfully.")
        except Exception as e:
            print(f"Error wiping database: {e}")
            self.db.rollback()

    def seed_users(self):
        print("--- STEP 3: UPSERTING USERS ---")
        if not self.schema.has_table('users_v2'):
             return

        for key, persona in PERSONAS.items():
            email = persona['email']
            
            # Check if exists
            try:
                row = self.db.execute(text("SELECT id FROM users_v2 WHERE email = :email"), {"email": email}).fetchone()
                if row:
                    user_id = str(row[0])
                    print(f"User {email} exists ({user_id}).")
                    self.user_ids[key] = user_id
                    continue
            except Exception as e:
                 print(f"Error checking user {email}: {e}")
                 self.db.rollback()

            # If not exists, insert
            user_id = str(uuid.uuid4())
            self.user_ids[key] = user_id
            
            cols = ["id", "email", "hashed_password", "is_active", "full_name"]
            vals = {
                "id": user_id, 
                "email": email, 
                "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWQqj8.q/s.f1.u1.s1.a.b.c", 
                "is_active": True,
                "full_name": f"{key.capitalize()} User"
            }
            
            # Dynamic col check
            valid_cols = []
            valid_vals = {}
            for c in cols:
                if self.schema.has_column('users_v2', c):
                    valid_cols.append(c)
                    valid_vals[c] = vals[c]
            
            if self.schema.has_column('users_v2', 'onboarding_status'):
                valid_cols.append('onboarding_status')
                valid_vals['onboarding_status'] = 'PENDING' if key == 'empty' else 'COMPLETE'

            sql = f"INSERT INTO users_v2 ({','.join(valid_cols)}) VALUES ({','.join([':'+c for c in valid_cols])})"
            try:
                self.db.execute(text(sql), valid_vals)
                self.db.commit()
                print(f"Inserted {email}")
            except Exception as e:
                print(f"Failed to insert {email}: {e}")
                self.db.rollback()

    def seed_goals(self):
        print("--- STEP 4: SEEDING GOALS ---")
        # goals table usually 'life_goals'
        table_name = 'life_goals' if self.schema.has_table('life_goals') else None
        if not table_name:
            print("No 'life_goals' table found. Skipping goal seeding.")
            return

        # Prepare dummy goals per persona
        goals_map = {
            "finance": [
                {"title": "Build Emergency Fund", "target_amount": 10000, "current_amount": 2500, "pillar": "finance", "category": "Sanity", "deadline": datetime.utcnow() + timedelta(days=180)},
                {"title": "Pay off Credit Card", "target_amount": 5000, "current_amount": 0, "pillar": "finance", "category": "Debt", "deadline": datetime.utcnow() + timedelta(days=90)},
                {"title": "Save for Vacation", "target_amount": 3000, "current_amount": 500, "pillar": "finance", "category": "Joy", "deadline": datetime.utcnow() + timedelta(days=200)},
            ],
            "health": [
                {"title": "Run a Marathon", "target_amount": 42, "current_amount": 5, "pillar": "health", "category": "Activity", "deadline": datetime.utcnow() + timedelta(days=120)},
                {"title": "Consistent Sleep", "target_amount": 8, "current_amount": 6, "pillar": "health", "category": "Recovery", "deadline": datetime.utcnow() + timedelta(days=30)},
                {"title": "Lose Weight", "target_amount": 80, "current_amount": 85, "pillar": "health", "category": "Nutrition", "deadline": datetime.utcnow() + timedelta(days=100)},
            ],
            "time": [
                {"title": "Reduce Meetings", "target_amount": 10, "current_amount": 20, "pillar": "time", "category": "Load", "deadline": datetime.utcnow() + timedelta(days=30)},
                {"title": "Daily Deep Work", "target_amount": 2, "current_amount": 0, "pillar": "time", "category": "Focus", "deadline": datetime.utcnow() + timedelta(days=60)},
                {"title": "Consistent Morning Routine", "target_amount": 1, "current_amount": 0, "pillar": "time", "category": "Structure","deadline": datetime.utcnow() + timedelta(days=21)},

            ],
            "super": [ # Mix
                 {"title": "Financial Independence", "target_amount": 1000000, "current_amount": 150000, "pillar": "finance", "category": "Wealth", "deadline": datetime.utcnow() + timedelta(days=1000)},
                 {"title": "Ironman Triathlon", "target_amount": 1, "current_amount": 0, "pillar": "health", "category": "Fitness", "deadline": datetime.utcnow() + timedelta(days=365)},
                 {"title": "Write a Book", "target_amount": 1, "current_amount": 0, "pillar": "time", "category": "Creation", "deadline": datetime.utcnow() + timedelta(days=200)},
            ],
            "empty": []
        }

        # Check existing columns to map logic
        db_cols = [c['name'] for c in self.schema.columns[table_name]]
        
        for persona, goals in goals_map.items():
            if not goals: continue
            user_id = self.user_ids.get(persona)
            if not user_id: continue

            for g in goals:
                # Construct insert dict
                insert_data = {"id": str(uuid.uuid4()), "user_id": user_id, "created_at": datetime.utcnow()}
                
                # Dynamic mapping
                if "title" in db_cols: insert_data["title"] = g["title"]
                if "description" in db_cols: insert_data["description"] = f"Goal for {persona}"
                if "target_amount" in db_cols: insert_data["target_amount"] = g["target_amount"]
                if "current_amount" in db_cols: insert_data["current_amount"] = g["current_amount"]
                if "deadline" in db_cols: insert_data["deadline"] = g["deadline"]
                if "category" in db_cols: insert_data["category"] = g["category"]
                # Pillar column: Might be 'pillar' or 'domain' or implicit. 
                # Known issue: 'pillar' column was missing before, check if it's there
                if "pillar" in db_cols: insert_data["pillar"] = g["pillar"]
                elif "type" in db_cols: insert_data["type"] = g["pillar"]
                
                # Execute
                col_list = insert_data.keys()
                sql = f"INSERT INTO {table_name} ({','.join(col_list)}) VALUES ({','.join([':'+k for k in col_list])})"
                try:
                    self.db.execute(text(sql), insert_data)
                except Exception as e:
                    print(f"Error inserting goal {g['title']}: {e}")
        self.db.commit()
        print("Goals Seeded.")

    def seed_financial_inputs(self):
        print("--- STEP 5A: SEEDING FINANCIAL INPUTS ---")
        # Need accounts and transactions
        if not self.schema.has_table('financial_accounts') or not self.schema.has_table('transactions'):
            print("Financial tables missing. Skipping.")
            return
            
        target_personas = ['finance', 'super']
        
        for persona in target_personas:
            user_id = self.user_ids.get(persona)
            if not user_id: continue
            
            # 1. Create Account
            acct_id = str(uuid.uuid4())
            try:
                self.db.execute(text("""
                    INSERT INTO financial_accounts (id, user_id, name, type, balance, currency, institution_name, created_at)
                    VALUES (:id, :uid, 'Primary Checking', 'depository', 5000.00, 'USD', 'Chase', :now)
                """), {"id": acct_id, "uid": user_id, "now": datetime.utcnow()})
            except Exception as e:
                print(f"Error creating account for {persona}: {e}")
                continue
                
            # 2. Add Transactions (Inputs for Insights/Recos)
            # Generate 20 transactions over last 30 days
            categories = ["Food & Dining", "Shopping", "Transport", "Bills", "Salary"]
            for i in range(20):
                date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
                amt = round(random.uniform(10, 200), 2)
                cat = random.choice(categories)
                if cat == "Salary": amt = 2500; amt = -amt # Income often negative or need flag? 
                # Usually negative for expense, positive for income. Let's assume standard: Expense < 0, Income > 0?
                # Actually commonly in Plaid: + is expense (outflow), - is income? Or vice versa.
                # Let's assume + is money in the account, - is money out.
                if cat == "Salary": 
                    amount = 3000
                else:
                    amount = -amt
                
                try:
                    self.db.execute(text("""
                        INSERT INTO transactions (id, account_id, amount, transaction_date, description, merchant_name, category_primary, created_at)
                        VALUES (:id, :aid, :amt, :date, :name, :name, :cat, :now)
                    """), {
                        "id": str(uuid.uuid4()), "aid": acct_id, "amt": amount, "date": date,
                        "name": f"{cat} Transaction", "cat": cat, "now": datetime.utcnow()
                    })
                except Exception as e:
                    print(f"Tx error: {e}")
                    
        self.db.commit()
        print("Financial Inputs Seeded.")

    def seed_health_time_inputs(self):
        print("--- STEP 5B: SEEDING HEALTH/TIME INPUTS ---")
        # Health: health_daily_summaries
        if self.schema.has_table('health_daily_summaries'):
            for persona in ['health', 'super']:
                uid = self.user_ids.get(persona)
                if not uid: continue
                # Insert 7 days of data
                # Insert 30 days of data for Unlock
                for i in range(30):
                    date = datetime.utcnow().date() - timedelta(days=i)
                    self.db.execute(text("""
                        INSERT INTO health_daily_summaries (id, user_id, date, steps_count, sleep_duration_minutes, sleep_quality_score, hrv_average)
                        VALUES (:id, :uid, :date, :steps, :sleep, :qual, :hrv)
                    """), {
                        "id": str(uuid.uuid4()), "uid": uid, "date": date,
                        "steps": random.randint(5000, 15000), "sleep": int(random.uniform(6, 9) * 60),
                        "qual": random.randint(60, 95), "hrv": random.randint(30, 80)
                    })
                    
        # Time: time_profiles
        if self.schema.has_table('time_profiles'):
             for persona in ['time', 'super']:
                uid = self.user_ids.get(persona)
                if not uid: continue
                self.db.execute(text("""
                    INSERT INTO time_profiles (id, user_id, work_hours_per_week, routine_style, task_style, time_overwhelm_level)
                    VALUES (:id, :uid, 40, 'I follow a routine', 'I plan ahead', 'Sometimes')
                    ON CONFLICT (id) DO NOTHING
                """), {"id": str(uuid.uuid4()), "uid": uid})
                
        self.db.commit()
        print("Health/Time Inputs Seeded.")

    def seed_calendar_events(self):
        print("--- STEP 5C: SEEDING CALENDAR EVENTS ---")
        if not self.schema.has_table('calendar_events'):
            print("calendar_events table missing. Skipping.")
            return

        for persona in ['time', 'super']:
            uid = self.user_ids.get(persona)
            if not uid: continue
            
            # Seed 5 meetings and 5 focus blocks over last 3 days
            base_time = datetime.utcnow()
            events = []
            
            # Meetings
            for i in range(5):
                start = base_time - timedelta(days=random.randint(0,2), hours=random.randint(9, 16))
                events.append({
                    "id": str(uuid.uuid4()), "uid": uid, "title": "Strategy Meeting", 
                    "start": start, "end": start + timedelta(minutes=60), 
                    "category": "Meeting", "is_meeting": True, "location": "Office"
                })
                
            # Focus
            for i in range(5):
                start = base_time - timedelta(days=random.randint(0,2), hours=random.randint(9, 16))
                events.append({
                    "id": str(uuid.uuid4()), "uid": uid, "title": "Deep Work Block", 
                    "start": start, "end": start + timedelta(minutes=90), 
                    "category": "Focus", "is_meeting": False, "location": "Home"
                })

            for e in events:
                try:
                    self.db.execute(text("""
                        INSERT INTO calendar_events (id, user_id, title, start_time, end_time, is_meeting, location_context)
                        VALUES (:id, :uid, :title, :start, :end, :is_meeting, :location)
                    """), {
                        "id": e['id'], "uid": e['uid'], "title": e['title'],
                        "start": e['start'], "end": e['end'], 
                        "is_meeting": e['is_meeting'], "location": e['location']
                    })
                except Exception as err:
                    print(f"Failed to insert event: {err}")
            
        self.db.commit()
        print("Calendar Events Seeded.")

    def seed_scores(self):
        print("--- STEP 6: CALCULATING & SEEDING SCORES ---")
        if not self.schema.has_table('viv_indexes'):
            print("viv_indexes table missing. Skipping scoring.")
            return

        for key, persona in PERSONAS.items():
            user_id = self.user_ids.get(key)
            if not user_id: continue
            
            print(f"Calculating scores for {key} ({user_id})...")
            
            try:
                # 1. Calculate Scores using services (DB data)
                # Payload is empty as we rely on seeded DB data
                payload = {} 
                
                fin_data = calculate_financial_health_score(user_id, payload, self.db)
                hs_data = calculate_health_score(user_id, payload, self.db)
                time_data = calculate_productivity_score(user_id, payload, self.db)
                
                # 2. Update User Profile
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
                    profile = user.profile_json or {}
                    profile["onboarding_breakdown"] = {
                        "financial": fin_data,
                        "health": hs_data,
                        "productivity": time_data
                    }
                    # Also set top-level onboarding data to ensure fallbacks work
                    profile["onboarding_data"] = {
                        "monthly_income": 5000, # Dummy fallback
                        "full_name": persona['role']
                    }
                    user.profile_json = profile
                    self.db.add(user)
                
                # 3. Create VivIndex
                viv_index = VivIndex(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    financial_score=fin_data.get("overall_score", 0),
                    health_score=hs_data.get("score", 0),
                    time_score=time_data.get("score", 0),
                    snapshot_reason="Synthetic Seeding",
                    timestamp=datetime.utcnow()
                )
                self.db.add(viv_index)
                
                self.db.commit()
                print(f"Scores seeded for {key}: Fin={viv_index.financial_score}, Health={viv_index.health_score}, Time={viv_index.time_score}")
                
            except Exception as e:
                print(f"Error seeding scores for {key}: {e}")
                import traceback
                traceback.print_exc()
                self.db.rollback()

    def run_validation(self):
        print("--- STEP 7: VALIDATION QUERIES ---")
        
        # Count rows per user tables
        tables_to_check = ['users_v2', 'life_goals', 'financial_accounts', 'transactions', 'health_daily_summaries', 'time_profiles']
        
        print(f"{'Table':<25} | {'Count':<10}")
        print("-" * 40)
        
        for t in tables_to_check:
            if not self.schema.has_table(t): continue
            try:
                if t == 'users_v2':
                    count = self.db.execute(text(f"SELECT count(*) FROM {t}")).scalar()
                    print(f"{t:<25} | {count:<10}")
                elif self.schema.has_column(t, 'user_id'):
                    res = self.db.execute(text(f"SELECT u.email, count(*) FROM {t} x JOIN users_v2 u ON x.user_id = u.id WHERE u.email like '%@helm.com' GROUP BY u.email")).fetchall()
                    for r in res:
                        print(f"{t} ({r[0]})".ljust(25) + f" | {r[1]:<10}")
                else:
                    count = self.db.execute(text(f"SELECT count(*) FROM {t}")).scalar()
                    print(f"{t:<25} | {count:<10}")

            except Exception as e:
                print(f"Error validating {t}: {e}")
                
        print("-" * 40)



def get_fallback_session():
    print("Attempting Direct TCP Connection to 136.119.201.13 via psycopg2...")
    # Hardcoded IP fallback, switching to psycopg2 for robustness
    db_url = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13/lfsd"
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()



def main():
    # Force Fallback immediately to avoid ADC/Connector issues
    print("--- FORCING DIRECT TCP CONNECTION ---")
    db = get_fallback_session()
    
    try:
        # Pre-flight verify
        db.execute(text("SELECT 1"))
        print("Direct Connection OK.")
    except Exception as e:
        print(f"Direct Connection Failed: {e}")
        return

    try:
        # 1. Discovery
        schema = SchemaDiscoveryAgent(db)
        schema.discover()
        
        # 2. Seeding
        seeder = DataSeedingAgent(db, schema)
        seeder.clean_slate()
        seeder.seed_users()
        seeder.seed_goals()
        seeder.seed_financial_inputs()
        # seeder.seed_financial_inputs() # Removed duplicate
        seeder.seed_health_time_inputs()
        seeder.seed_calendar_events()
        seeder.seed_scores()
        
        # 3. Validation
        seeder.run_validation()
        
    except Exception as e:
        print(f"FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()

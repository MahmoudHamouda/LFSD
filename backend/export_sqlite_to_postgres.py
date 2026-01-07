"""
Export SQLite database to PostgreSQL-compatible SQL
"""
import sqlite3
import json

# Connect to SQLite database
conn = sqlite3.connect('test_gov_final.db')
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
tables = [row[0] for row in cursor.fetchall()]

print(f"Found {len(tables)} tables: {', '.join(tables)}\n")

# Open output file
with open('test_gov_final_export_postgres.sql', 'w', encoding='utf-8') as f:
    f.write("-- PostgreSQL Export from SQLite\n")
    f.write("-- Generated for CloudSQL Import\n\n")
    
    for table in tables:
        print(f"Exporting table: {table}")
        
        # Get CREATE TABLE statement from sqlite_master
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
        create_sql = cursor.fetchone()[0]
        
        # Get column info for INSERT statements
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        # Convert SQLite types/syntax to PostgreSQL
        # This is a basic conversion - might need more robust handling for complex schemas
        create_sql = create_sql.replace('INTEGER PRIMARY KEY', 'SERIAL PRIMARY KEY')
        create_sql = create_sql.replace('AUTOINCREMENT', '')
        create_sql = create_sql.replace('datetime', 'TIMESTAMP')
        create_sql = create_sql.replace('DATETIME', 'TIMESTAMP')
        create_sql = create_sql.replace('BLOB', 'BYTEA')
        
        # Patch for users table: Add auth0_id if missing
        if table == 'users' and 'auth0_id' not in create_sql:
            # Simple injection before the closing parenthesis or primary key definition
            create_sql = create_sql.replace('email VARCHAR UNIQUE NOT NULL,', 'email VARCHAR UNIQUE NOT NULL, auth0_id VARCHAR UNIQUE,')
        
        f.write(f"-- Schema for {table}\n")
        f.write(f"DROP TABLE IF EXISTS {table} CASCADE;\n")
        f.write(f"{create_sql};\n\n")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        print(f"  - {row_count} rows")
        
        if row_count > 0:
            # Get all data
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            # Get column names
            col_names = [col[1] for col in columns]
            
            # Write INSERT statements
            f.write(f"\n-- Table: {table} ({row_count} rows)\n")
            for row in rows:
                values = []
                for val in row:
                    if val is None:
                        values.append('NULL')
                    elif isinstance(val, (int, float)):
                        values.append(str(val))
                    elif isinstance(val, str):
                        # Escape single quotes for SQL
                        escaped = val.replace("'", "''")
                        values.append(f"'{escaped}'")
                    else:
                        # Try to serialize as JSON
                        try:
                            json_val = json.dumps(val)
                            values.append(f"'{json_val}'")
                        except:
                            values.append(f"'{str(val)}'")
                
                f.write(f"INSERT INTO {table} ({', '.join(col_names)}) VALUES ({', '.join(values)});\n")
    
    f.write("\n-- Export complete\n")

conn.close()
print("\n✓ Export complete: test_gov_final_export_postgres.sql")

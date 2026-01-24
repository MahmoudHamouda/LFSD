
import os

def read_chunks():
    file_path = 'e2e_results.log'
    if not os.path.exists(file_path):
        print("Log file not found.")
        return

    with open(file_path, 'r', encoding='utf-16le') as f:
        content = f.read()
    
    chunk_size = 1000
    for i in range(0, len(content), chunk_size):
        print(f"--- CHUNK {i//chunk_size} ---")
        print(content[i:i+chunk_size])
        print("--- END CHUNK ---")

if __name__ == "__main__":
    read_chunks()

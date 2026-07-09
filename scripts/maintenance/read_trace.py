
import sys
import os

def read_file():
    try:
        # PowerShell redirects are often UTF-16LE
        with open('e2e_results.log', 'r', encoding='utf-16le') as f:
            print(f.read())
    except Exception as e:
        print(f"UTF-16LE failed: {e}")
        try:
            with open('schema_dump.txt', 'r', encoding='utf-8') as f:
                print(f.read())
        except Exception as e2:
            print(f"UTF-8 failed: {e2}")

if __name__ == "__main__":
    read_file()

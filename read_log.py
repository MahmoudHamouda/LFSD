
import time

def read():
    try:
        with open('e2e_results.log', 'r', encoding='utf-16le') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                print(line.strip())
                if i % 20 == 0 and i > 0:
                    time.sleep(0.01) # tiny pause to help buffer?
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    read()

try:
    with open("compile_errors.txt", "r", encoding="utf-16") as f:
        for line in f:
            if "***" in line:
                print(line.strip())
except Exception as e:
    print(e)

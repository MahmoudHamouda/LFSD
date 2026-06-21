import os

for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            try:
                # Check for null bytes / UTF-16 artifact
                is_corrupt = False
                with open(path, "rb") as f:
                    content = f.read()
                    if b"\x00" in content:
                        is_corrupt = True

                if is_corrupt:
                    print(f"Fixing corrupted file: {path}")

                    # Try reading as UTF-16
                    try:
                        with open(path, "r", encoding="utf-16") as f:
                            text = f.read()
                    except:
                        # Fallback: Treat as empty if it's just garbage
                        text = ""

                    # Write back as UTF-8
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(text.strip())

            except Exception as e:
                print(f"Error processing {path}: {e}")

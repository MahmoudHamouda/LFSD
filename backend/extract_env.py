import yaml

try:
    with open("backend_config.yaml", "r", encoding="utf-16") as f:
        data = yaml.safe_load(f)
except:
    try:
        with open("backend_config.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"Error reading yaml: {e}")
        exit(1)

containers = (
    data.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
)
for c in containers:
    env = c.get("env", [])
    for e in env:
        print(f"{e.get('name')}={e.get('value')}")

import os

# Force offline mock mode regardless of a local .env (load_dotenv does not override existing env).
os.environ["DEMO_MODE"] = "mock"

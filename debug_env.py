import os
from code.extraction import _load_env_file

print(f"Current working directory: {os.getcwd()}")
_load_env_file()
print(f"GEMINI_API_KEY in environ: {os.environ.get('GEMINI_API_KEY') is not None}")
print(f"GOOGLE_API_KEY in environ: {os.environ.get('GOOGLE_API_KEY') is not None}")

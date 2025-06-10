import os
from os import environ as env
from tempfile import gettempdir


TIMEOUT = 5  # seconds
SANDBOX_USER_UID = int(env.get('SANDBOX_USER_UID', os.getuid()))
SANDBOX_DIR = env.get('SANDBOX_DIR', gettempdir())

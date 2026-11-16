"""
Collection of 20+ vulnerable code snippets for security scanner testing.

This test suite covers:
- SQL Injection (3 variants)
- Command Injection (3 variants)
- Hardcoded Secrets (4 variants)
- Insecure Deserialization (2 variants)
- Insecure Cryptography (3 variants)
- Path Traversal (2 variants)
- XXE Injection (1 variant)
- Unsafe YAML Loading (1 variant)
- Weak Random (1 variant)
- Eval injection (1 variant)
"""

# ===== SQL Injection (3) =====

VULN_01_SQL_INJECTION_BASIC = """
def get_user_by_id(user_id):
    query = "SELECT * FROM users WHERE id = '" + user_id + "'"
    return db.execute(query)
"""

VULN_02_SQL_INJECTION_FORMATTED = """
def search_products(search_term):
    query = f"SELECT * FROM products WHERE name LIKE '%{search_term}%'"
    cursor.execute(query)
    return cursor.fetchall()
"""

VULN_03_SQL_INJECTION_PERCENT = """
def get_user_info(username):
    query = "SELECT * FROM users WHERE username = '%s'" % username
    return database.query(query)
"""

# ===== Command Injection (3) =====

VULN_04_COMMAND_INJECTION_OS_SYSTEM = """
import os

def ping_host(hostname):
    os.system("ping -c 1 " + hostname)
"""

VULN_05_COMMAND_INJECTION_SUBPROCESS = """
import subprocess

def compress_file(filename):
    subprocess.call("tar -czf backup.tar.gz " + filename, shell=True)
"""

VULN_06_COMMAND_INJECTION_POPEN = """
import os

def list_directory(path):
    os.popen("ls -la " + path).read()
"""

# ===== Hardcoded Secrets (4) =====

VULN_07_HARDCODED_API_KEY = """
API_KEY = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
STRIPE_SECRET = "sk_live_51234567890"

def authenticate():
    headers = {"Authorization": f"Bearer {API_KEY}"}
    return requests.get("https://api.example.com", headers=headers)
"""

VULN_08_HARDCODED_PASSWORD = """
DATABASE_PASSWORD = "MySecretP@ssw0rd123"

def connect_db():
    connection = psycopg2.connect(
        host="localhost",
        database="myapp",
        user="admin",
        password="admin123"
    )
"""

VULN_09_HARDCODED_JWT_SECRET = """
JWT_SECRET_KEY = "supersecretkey12345"

def generate_token(user_id):
    payload = {"user_id": user_id}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
"""

VULN_10_HARDCODED_AWS_CREDENTIALS = """
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

def upload_to_s3(file_path):
    s3 = boto3.client("s3", 
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
"""

# ===== Insecure Deserialization (2) =====

VULN_11_PICKLE_DESERIALIZATION = """
import pickle

def load_user_data(data):
    user = pickle.loads(data)  # Unsafe deserialization
    return user
"""

VULN_12_YAML_UNSAFE_LOAD = """
import yaml

def load_config(config_file):
    with open(config_file) as f:
        config = yaml.load(f)  # Should use yaml.safe_load()
    return config
"""

# ===== Insecure Cryptography (3) =====

VULN_13_MD5_HASH = """
import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()
"""

VULN_14_WEAK_CIPHER = """
from Crypto.Cipher import DES

def encrypt_data(data, key):
    cipher = DES.new(key, DES.MODE_ECB)  # Weak cipher and mode
    return cipher.encrypt(data)
"""

VULN_15_HARDCODED_CRYPTO_KEY = """
from cryptography.fernet import Fernet

ENCRYPTION_KEY = b'9x-very-secret-key-12345678901234567890='

def encrypt_message(message):
    f = Fernet(ENCRYPTION_KEY)
    return f.encrypt(message.encode())
"""

# ===== Path Traversal (2) =====

VULN_16_PATH_TRAVERSAL_OPEN = """
def read_file(filename):
    with open(f"/var/www/uploads/{filename}") as f:
        return f.read()
"""

VULN_17_PATH_TRAVERSAL_SEND_FILE = """
from flask import send_file

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(f"/data/files/{filename}")
"""

# ===== XXE Injection (1) =====

VULN_18_XXE_VULNERABLE_XML_PARSER = """
import xml.etree.ElementTree as ET

def parse_xml(xml_string):
    root = ET.fromstring(xml_string)  # Vulnerable to XXE
    return root
"""

# ===== Eval Injection (1) =====

VULN_19_EVAL_INJECTION = """
def calculate_expression(expr):
    result = eval(expr)  # Arbitrary code execution
    return result
"""

# ===== Weak Random (1) =====

VULN_20_WEAK_RANDOM = """
import random

def generate_session_token():
    token = ''.join(random.choice('0123456789abcdef') for _ in range(32))
    return token
"""

# ===== Assert Usage (1) =====

VULN_21_ASSERT_IN_PRODUCTION = """
def validate_user(user):
    assert user.is_authenticated, "User must be authenticated"
    return process_request(user)
"""

# ===== SQL Injection with ORM bypass (1) =====

VULN_22_ORM_RAW_SQL = """
from django.db import connection

def search_users(search_term):
    with connection.cursor() as cursor:
        query = f"SELECT * FROM auth_user WHERE username = '{search_term}'"
        cursor.execute(query)
        return cursor.fetchall()
"""

# Test cases mapping
VULNERABLE_SNIPPETS = {
    "sql_injection_basic": VULN_01_SQL_INJECTION_BASIC,
    "sql_injection_formatted": VULN_02_SQL_INJECTION_FORMATTED,
    "sql_injection_percent": VULN_03_SQL_INJECTION_PERCENT,
    "command_injection_os_system": VULN_04_COMMAND_INJECTION_OS_SYSTEM,
    "command_injection_subprocess": VULN_05_COMMAND_INJECTION_SUBPROCESS,
    "command_injection_popen": VULN_06_COMMAND_INJECTION_POPEN,
    "hardcoded_api_key": VULN_07_HARDCODED_API_KEY,
    "hardcoded_password": VULN_08_HARDCODED_PASSWORD,
    "hardcoded_jwt_secret": VULN_09_HARDCODED_JWT_SECRET,
    "hardcoded_aws_credentials": VULN_10_HARDCODED_AWS_CREDENTIALS,
    "pickle_deserialization": VULN_11_PICKLE_DESERIALIZATION,
    "yaml_unsafe_load": VULN_12_YAML_UNSAFE_LOAD,
    "md5_hash": VULN_13_MD5_HASH,
    "weak_cipher": VULN_14_WEAK_CIPHER,
    "hardcoded_crypto_key": VULN_15_HARDCODED_CRYPTO_KEY,
    "path_traversal_open": VULN_16_PATH_TRAVERSAL_OPEN,
    "path_traversal_send_file": VULN_17_PATH_TRAVERSAL_SEND_FILE,
    "xxe_vulnerable_parser": VULN_18_XXE_VULNERABLE_XML_PARSER,
    "eval_injection": VULN_19_EVAL_INJECTION,
    "weak_random": VULN_20_WEAK_RANDOM,
    "assert_in_production": VULN_21_ASSERT_IN_PRODUCTION,
    "orm_raw_sql": VULN_22_ORM_RAW_SQL,
}

# Vulnerability categories for organized testing
VULNERABILITY_CATEGORIES = {
    "injection": [
        "sql_injection_basic",
        "sql_injection_formatted",
        "sql_injection_percent",
        "command_injection_os_system",
        "command_injection_subprocess",
        "command_injection_popen",
        "eval_injection",
        "orm_raw_sql",
    ],
    "secrets": [
        "hardcoded_api_key",
        "hardcoded_password",
        "hardcoded_jwt_secret",
        "hardcoded_aws_credentials",
        "hardcoded_crypto_key",
    ],
    "deserialization": [
        "pickle_deserialization",
        "yaml_unsafe_load",
    ],
    "cryptography": [
        "md5_hash",
        "weak_cipher",
        "hardcoded_crypto_key",
    ],
    "path_traversal": [
        "path_traversal_open",
        "path_traversal_send_file",
    ],
    "other": [
        "xxe_vulnerable_parser",
        "weak_random",
        "assert_in_production",
    ],
}

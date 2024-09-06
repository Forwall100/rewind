import os
import time
import sqlite3
import subprocess
from datetime import datetime
import pytesseract
from PIL import Image
import io
import yaml
import json
import configparser
import hashlib

config_dir = os.path.expanduser("~/.config/rewind")
if not os.path.exists(config_dir):
    os.makedirs(config_dir)

db_path = os.path.join(config_dir, "screenshots.db")
config_path = os.path.join(config_dir, "config.yaml")


def load_config():
    for ext in ["", ".yaml", ".yml", ".json", ".ini"]:
        full_path = config_path + ext
        if os.path.exists(full_path):
            with open(full_path, "r") as f:
                if ext in [".yaml", ".yml"]:
                    return yaml.safe_load(f)
                elif ext == ".json":
                    return json.load(f)
                elif ext == ".ini":
                    config = configparser.ConfigParser()
                    config.read(full_path)
                    return {s: dict(config.items(s)) for s in config.sections()}
                else:
                    return dict(line.strip().split("=") for line in f if "=" in line)
    return {
        "languages": "eng+rus",
        "max_db_size_mb": 20_000,
        "screenshot_period_sec": 30,
    }


config = load_config()
languages = config.get("languages", "eng+rus")
max_db_size_mb = int(config.get("max_db_size_mb", 1000))
screenshot_period_sec = int(config.get("screenshot_period_sec", 30))

conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS screenshots (
        id INTEGER PRIMARY KEY,
        image BLOB,
        text TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        hash TEXT
    )
"""
)
conn.commit()


def is_wayland():
    return os.environ.get("WAYLAND_DISPLAY") is not None


def take_screenshot():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    screenshot_path = f"screenshot_{timestamp}.png"
    try:
        if is_wayland():
            subprocess.run(["grim", screenshot_path], check=True)
        else:
            subprocess.run(["scrot", "-z", screenshot_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error taking screenshot: {e}")
        return None

    with open(screenshot_path, "rb") as file:
        image_blob = file.read()
    os.remove(screenshot_path)
    return image_blob


def extract_text_from_image(image_blob):
    if image_blob is None:
        return ""
    image = Image.open(io.BytesIO(image_blob))
    text = pytesseract.image_to_string(image, lang=languages)
    return text


def get_db_size():
    return os.path.getsize(db_path) / (1024 * 1024)  # Size in MB


def delete_oldest_record():
    cursor.execute(
        """
        DELETE FROM screenshots
        WHERE id = (SELECT id FROM screenshots ORDER BY timestamp ASC LIMIT 1)
    """
    )
    conn.commit()


def calculate_image_hash(image_blob):
    return hashlib.md5(image_blob).hexdigest()


def is_duplicate_image(image_hash):
    cursor.execute("SELECT COUNT(*) FROM screenshots WHERE hash = ?", (image_hash,))
    count = cursor.fetchone()[0]
    return count > 0


def save_to_database(image_blob, text):
    if image_blob is None:
        return

    image_hash = calculate_image_hash(image_blob)

    if is_duplicate_image(image_hash):
        print("Duplicate image detected. Skipping...")
        return

    while get_db_size() >= max_db_size_mb:
        delete_oldest_record()

    cursor.execute(
        """
        INSERT INTO screenshots (image, text, hash)
        VALUES (?, ?, ?)
    """,
        (image_blob, text, image_hash),
    )
    conn.commit()


def main():
    while True:
        image_blob = take_screenshot()
        print("Screenshot taken")
        extracted_text = extract_text_from_image(image_blob)
        save_to_database(image_blob, extracted_text)
        time.sleep(screenshot_period_sec)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        conn.close()
        print("Program terminated by user.")

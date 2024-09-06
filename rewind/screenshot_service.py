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
import numpy as np
from scipy.fftpack import dct
from Levenshtein import distance as levenshtein_distance

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
        "similarity_threshold": 0.9,
        "text_similarity_threshold": 0.8,
    }


config = load_config()
languages = config.get("languages", "eng+rus")
max_db_size_mb = int(config.get("max_db_size_mb", 1000))
screenshot_period_sec = int(config.get("screenshot_period_sec", 30))
similarity_threshold = float(config.get("similarity_threshold", 0.9))
text_similarity_threshold = float(config.get("text_similarity_threshold", 0.8))


conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS screenshots (
        id INTEGER PRIMARY KEY,
        image BLOB,
        text TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        phash TEXT
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


def calculate_phash(image_blob, hash_size=8):
    image = (
        Image.open(io.BytesIO(image_blob))
        .convert("L")
        .resize((hash_size * 4, hash_size * 4), Image.LANCZOS)
    )
    pixels = np.array(image, dtype=np.float32)
    dct_result = dct(dct(pixels, axis=0), axis=1)
    dct_low = dct_result[:hash_size, :hash_size]
    med = np.median(dct_low)
    hash_bits = (dct_low > med).flatten()
    return "".join(["1" if b else "0" for b in hash_bits])


def hamming_distance(hash1, hash2):
    return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))


def is_similar_image(phash, text):
    cursor.execute(
        "SELECT phash, text FROM screenshots ORDER BY timestamp DESC LIMIT 10"
    )
    recent_screenshots = cursor.fetchall()

    for recent_phash, recent_text in recent_screenshots:
        if recent_phash is None or recent_text is None:
            continue

        hash_similarity = 1 - hamming_distance(phash, recent_phash) / len(phash)
        if hash_similarity >= similarity_threshold:
            text_similarity = 1 - levenshtein_distance(text, recent_text) / max(
                len(text), len(recent_text)
            )
            if text_similarity >= text_similarity_threshold:
                return True

    return False


def save_to_database(image_blob, text):
    if image_blob is None:
        return

    phash = calculate_phash(image_blob)

    if is_similar_image(phash, text):
        print("Similar image detected. Skipping...")
        return

    while get_db_size() >= max_db_size_mb:
        delete_oldest_record()

    cursor.execute(
        """
        INSERT INTO screenshots (image, text, phash)
        VALUES (?, ?, ?)
    """,
        (image_blob, text, phash),
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

from flask import Flask, render_template, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
import time
import uuid
from datetime import datetime
import requests 

app = Flask(__name__)

MONGO_URI = ""  # Insert your MongoDB URI here
client = MongoClient(MONGO_URI)
db = client["StirTech"]
collection = db["TwitterTrends"]

def get_ip():
    try:
        response = requests.get('https://httpbin.org/ip')
        return response.json()['origin']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching IP: {str(e)}")
        return "Unknown IP"

def scrape_twitter():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://x.com/login")
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "text")))

        username = driver.find_element(By.NAME, "text")
        username.send_keys("your_username_here")  # Replace with your username
        username.send_keys(Keys.RETURN)
        time.sleep(2)

        password = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password.send_keys("your_password_here")  # Replace with your password
        password.send_keys(Keys.RETURN)
        time.sleep(5)

        trends = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//div[@aria-label='Timeline: Trending now']//span")
            )
        )
        
        trending_topics = []
        for trend in trends:
            text = trend.text.strip()
            if text and text not in ["What’s happening", "Show more", "Trending in India"] and not any(char.isdigit() for char in text) and "Trending" not in text:
                trending_topics.append(text)
        
        trending_topics = list(dict.fromkeys(trending_topics))[:5]

        unique_id = str(uuid.uuid4())
        ip_address = get_ip()  
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "_id": unique_id,
            "trends": trending_topics,
            "timestamp": timestamp,
            "ip_address": ip_address,
        }
        collection.insert_one(record)

        return record
    except Exception as e:
        print(f"Error encountered: {str(e)}")
        raise
    finally:
        driver.quit()


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/run_script", methods=["GET"])
def run_script():
    try:
        record = scrape_twitter()
        return jsonify(record)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

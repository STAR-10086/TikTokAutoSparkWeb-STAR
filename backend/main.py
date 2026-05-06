"""
TikTok Auto Spark - Backend API
FastAPI + Selenium automation service
"""

import os
import json
import time
import base64
import hashlib
import secrets
import threading
import re
from datetime import datetime
from typing import Optional

import uvicorn
import schedule
import requests
from fastapi import FastAPI, Header, Request, Query, Body, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, SessionNotCreatedException

# =============================================================================
# Configuration
# =============================================================================

PORT = int(os.environ.get("PORT", "5000"))
DEFAULT_PASSWORD = os.environ.get("ADMIN_PASSWORD", "123456")
DISPLAY_BROWSER = os.environ.get("DISPLAY_BROWSER", "true").lower() == "true"

# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(title="TikTok Auto Spark API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# State
# =============================================================================

class AppState:
    def __init__(self):
        self.driver = None
        self.douyin = None
        self.browser_initialized = False
        self.user_logged_in = False
        self.password = DEFAULT_PASSWORD
        self.valid_tokens = set()
        self.last_login_ip = "N/A"
        self.scheduled_tasks = {}
        self.start_time = datetime.now()

state = AppState()

# =============================================================================
# Auth Utils
# =============================================================================

def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

def generate_token() -> str:
    token = secrets.token_hex(32)
    state.valid_tokens.add(token)
    return token

def verify_token(token: str) -> bool:
    return token in state.valid_tokens

def remove_token(token: str):
    state.valid_tokens.discard(token)

def require_auth(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization[7:]
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token

# =============================================================================
# Browser Utils
# =============================================================================

def create_chrome_options() -> webdriver.ChromeOptions:
    options = webdriver.ChromeOptions()
    if not DISPLAY_BROWSER:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-web-security")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--start-maximized")
    options.add_argument("--force-device-scale-factor=0.25")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/110.0.5481.177 Safari/537.36"
    )
    return options

# =============================================================================
# Douyin Automation
# =============================================================================

class DouyinBot:
    def __init__(self, driver):
        self.driver = driver
        self.friends_cache = {}

    def get_friends_list(self):
        """Get list of friends from Douyin chat page"""
        xpath = '//div[@class="conversationConversationListwrapper"]/div/div/div'
        try:
            msg_list = self.driver.find_elements(By.XPATH, xpath)
            friends = []
            self.friends_cache = {}

            for i in range(1, len(msg_list) + 1):
                try:
                    name_xpath = f'{xpath}[{i + 1}]/div[1]/div[2]/div[1]/div[1]'
                    avatar_xpath = f'{xpath}[{i + 1}]/div[1]/div[1]/div/span/img'
                    avatar_xpath2 = f'{xpath}[{i + 1}]/div/div/img'
                    fire_xpath = f'{xpath}[{i + 1}]/div[1]/div[2]/div[1]/div[2]/div[1]/div/div'

                    name = self.driver.find_element(By.XPATH, name_xpath).text
                    try:
                        avatar = self.driver.find_element(By.XPATH, avatar_xpath).get_attribute("src")
                    except:
                        avatar = self.driver.find_element(By.XPATH, avatar_xpath2).get_attribute("src")

                    try:
                        fire = self.driver.find_element(By.XPATH, fire_xpath).text.strip()
                    except:
                        fire = ""

                    self.friends_cache[name] = {"avatar": avatar, "fire": fire}
                    friends.append({"name": name, "avatar": avatar, "fire": fire})
                except:
                    continue

            return friends
        except Exception as e:
            raise Exception(f"Failed to get friends list: {str(e)}")

    def send_message(self, name: str, text: str) -> bool:
        """Send message to a friend"""
        if not self.friends_cache:
            self.get_friends_list()

        if name not in self.friends_cache:
            raise Exception(f"Friend '{name}' not found")

        try:
            xpath = '//div[@class="conversationConversationListwrapper"]/div/div/div'
            for i in range(1, len(self.friends_cache) + 2):
                try:
                    name_xpath = f'{xpath}[{i + 1}]/div[1]/div[2]/div[1]/div[1]'
                    el = self.driver.find_element(By.XPATH, name_xpath)
                    if el.text == name:
                        el.click()
                        time.sleep(1.5)
                        input_xpath = '//div[@class="messageEditorimChatEditorContainer"]/div/div'
                        input_el = self.driver.find_element(By.XPATH, input_xpath)
                        input_el.send_keys(text)
                        input_el.send_keys(Keys.ENTER)
                        return True
                except:
                    continue
            raise Exception(f"Could not click on friend '{name}'")
        except Exception as e:
            raise Exception(f"Failed to send message: {str(e)}")

    def find_friend(self, name: str) -> bool:
        """Check if friend exists"""
        if not self.friends_cache:
            self.get_friends_list()
        return name in self.friends_cache

    def init_login(self):
        """Click login button to show QR code"""
        try:
            # Wait for page to load
            time.sleep(3)
            # Try multiple possible login button selectors
            selectors = [
                '//*[@id="douyin_login_comp_flat_panel"]/div/div[2]/div/div[4]/p',
                '//p[contains(text(), "登录")]',
                '//button[contains(text(), "登录")]',
                '//div[contains(@class, "login")]//p',
            ]
            for selector in selectors:
                try:
                    btn = self.driver.find_element(By.XPATH, selector)
                    btn.click()
                    time.sleep(2)
                    return
                except:
                    continue
        except:
            pass

# =============================================================================
# Scheduled Tasks
# =============================================================================

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

def format_time(time_str: str) -> str:
    if not time_str:
        return "22:00"
    time_str = time_str.replace("：", ":").strip()
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            return "22:00"
        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return "22:00"
        return f"{h:02d}:{m:02d}"
    except:
        return "22:00"

def get_daily_quote() -> str:
    try:
        resp = requests.get("https://v2.xxapi.cn/api/aiqinggongyu", timeout=5)
        if resp.status_code == 200:
            data = resp.json().get("data")
            if data:
                return data
    except:
        pass
    return "今日份的思念，已送达~"

# =============================================================================
# API Routes - Auth
# =============================================================================

@app.post("/api/auth/login")
async def auth_login(username: str = Body(...), password: str = Body(...)):
    if username == "admin" and hash_password(password) == hash_password(state.password):
        token = generate_token()
        return {"code": 200, "data": {"token": token}}
    return {"code": 400, "data": "Invalid credentials"}

@app.post("/api/auth/logout")
async def auth_logout(token: str = Depends(require_auth)):
    remove_token(token)
    return {"code": 200, "data": "Logged out"}

@app.post("/api/auth/change-password")
async def change_password(
    old_password: str = Body(...),
    new_password: str = Body(...),
    token: str = Depends(require_auth)
):
    if hash_password(old_password) != hash_password(state.password):
        return {"code": 400, "data": "Incorrect old password"}
    state.password = new_password
    return {"code": 200, "data": "Password changed"}

# =============================================================================
# API Routes - Browser
# =============================================================================

@app.get("/api/browser/status")
async def browser_status(token: str = Depends(require_auth)):
    return {
        "code": 200,
        "data": {
            "initialized": state.browser_initialized,
            "logged_in": state.user_logged_in,
            "uptime": str(datetime.now() - state.start_time),
        }
    }

@app.post("/api/browser/init")
async def browser_init(token: str = Depends(require_auth)):
    if state.browser_initialized:
        return {"code": 200, "data": "Already initialized"}

    try:
        options = create_chrome_options()
        state.driver = webdriver.Chrome(options=options)
        state.driver.set_window_size(1400, 3200)
        state.driver.get("https://www.douyin.com/chat?isPopup=1")
        state.douyin = DouyinBot(state.driver)
        state.browser_initialized = True
        return {"code": 200, "data": "Browser initialized"}
    except SessionNotCreatedException as e:
        return {"code": 500, "data": f"Session creation failed: {str(e)}"}
    except Exception as e:
        return {"code": 500, "data": f"Init failed: {str(e)}"}

@app.post("/api/browser/login-cookie")
async def login_cookie(
    cookie: str = Body(...),
    gzip_flag: bool = Body(False),
    token: str = Depends(require_auth)
):
    """Login with cookie data"""
    if not state.browser_initialized:
        return {"code": 400, "data": "Browser not initialized"}

    try:
        import gzip
        decoded = base64.b64decode(cookie)
        if gzip_flag:
            decoded = gzip.decompress(decoded)
        cookie_list = decoded.decode("utf-8")
        cookies = eval(base64.b64decode(cookie_list).decode("utf-8").replace("false", "False").replace("true", "True"))
        for c in cookies:
            state.driver.add_cookie(c)
        state.driver.refresh()

        try:
            state.driver.find_element(By.XPATH, '//*[@id="douyin_login_comp_flat_panel"]/picture')
            return {"code": 400, "data": "Login failed with cookie"}
        except NoSuchElementException:
            state.user_logged_in = True
            return {"code": 200, "data": "Login successful"}
    except Exception as e:
        return {"code": 400, "data": f"Cookie parse error: {str(e)}"}

@app.get("/api/browser/qrcode")
async def get_qrcode(token: str = Depends(require_auth)):
    """Get QR code for scanning"""
    if not state.browser_initialized:
        return {"code": 400, "data": "Browser not initialized"}

    try:
        state.douyin.init_login()
        time.sleep(2)

        # Try multiple possible QR code selectors
        qr_selectors = [
            '//*[@id="animate_qrcode_container"]/div[2]/img',
            '//img[contains(@src, "qrcode")]',
            '//div[contains(@class, "qrcode")]//img',
            '//div[contains(@class, "QRCode")]//img',
            '//canvas[contains(@class, "qrcode")]',
        ]

        src = None
        for selector in qr_selectors:
            try:
                element = state.driver.find_element(By.XPATH, selector)
                src = element.get_attribute("src")
                if src:
                    break
            except:
                continue

        # If no src found, try to take screenshot of QR area
        if not src:
            try:
                # Take screenshot and return it
                state.driver.save_screenshot("/tmp/qrcode.png")
                with open("/tmp/qrcode.png", "rb") as f:
                    img_data = base64.b64encode(f.read()).decode("utf-8")
                os.remove("/tmp/qrcode.png")
                return {"code": 200, "data": f"data:image/png;base64,{img_data}"}
            except:
                pass

        if src:
            return {"code": 200, "data": src}
        return {"code": 400, "data": "QR code not found"}
    except Exception as e:
        return {"code": 400, "data": f"QR code error: {str(e)}"}

@app.get("/api/browser/check-login")
async def check_login(token: str = Depends(require_auth)):
    """Check if user is logged in"""
    if not state.browser_initialized:
        return {"code": 200, "data": {"logged_in": False}}

    try:
        state.driver.find_element(By.XPATH, '//*[@id="douyin_login_comp_flat_panel"]/picture')
        state.user_logged_in = False
    except NoSuchElementException:
        state.user_logged_in = True

    return {"code": 200, "data": {"logged_in": state.user_logged_in}}

@app.get("/api/browser/screenshot")
async def screenshot(token: str = Depends(require_auth)):
    """Take browser screenshot"""
    if not state.browser_initialized:
        return {"code": 400, "data": "Browser not initialized"}

    try:
        state.driver.save_screenshot("/tmp/screenshot.png")
        with open("/tmp/screenshot.png", "rb") as f:
            img_data = base64.b64encode(f.read()).decode("utf-8")
        os.remove("/tmp/screenshot.png")
        return {"code": 200, "data": img_data}
    except Exception as e:
        return {"code": 400, "data": f"Screenshot error: {str(e)}"}

@app.post("/api/browser/logout")
async def browser_logout(token: str = Depends(require_auth)):
    """Logout from Douyin"""
    if not state.browser_initialized:
        return {"code": 400, "data": "Browser not initialized"}

    state.driver.delete_all_cookies()
    state.driver.refresh()
    state.user_logged_in = False
    return {"code": 200, "data": "Logged out from Douyin"}

# =============================================================================
# API Routes - Friends
# =============================================================================

@app.get("/api/friends/list")
async def friends_list(token: str = Depends(require_auth)):
    if not state.browser_initialized:
        return {"code": 400, "data": "Browser not initialized"}

    try:
        friends = state.douyin.get_friends_list()
        return {"code": 200, "data": {"count": len(friends), "list": friends}}
    except Exception as e:
        return {"code": 400, "data": str(e)}

# =============================================================================
# API Routes - Tasks
# =============================================================================

@app.get("/api/tasks/list")
async def tasks_list(token: str = Depends(require_auth)):
    tasks = []
    for task_id, job in state.scheduled_tasks.items():
        parts = task_id.split("_", 1)
        if len(parts) == 2:
            tasks.append({
                "id": task_id,
                "time": parts[0],
                "friend": parts[1],
                "next_run": str(job.next_run) if job.next_run else None,
            })
    return {"code": 200, "data": {"count": len(tasks), "tasks": tasks}}

@app.post("/api/tasks/add")
async def tasks_add(
    time: str = Body(...),
    friend: str = Body(...),
    message: str = Body(None),
    token: str = Depends(require_auth)
):
    if not state.browser_initialized or not state.douyin:
        return {"code": 400, "data": "Browser not initialized"}

    # Check duplicate
    for task_id in state.scheduled_tasks:
        if task_id.endswith(f"_{friend}"):
            return {"code": 400, "data": f"Friend '{friend}' already has a scheduled task"}

    if not state.douyin.find_friend(friend):
        return {"code": 400, "data": f"Friend '{friend}' not found"}

    play_time = format_time(time)
    msg = message or get_daily_quote()

    job = schedule.every().day.at(play_time).do(state.douyin.send_message, friend, msg)
    task_id = f"{play_time}_{friend}"
    state.scheduled_tasks[task_id] = job

    return {"code": 200, "data": {"id": task_id, "time": play_time, "friend": friend}}

@app.delete("/api/tasks/{task_id}")
async def tasks_delete(task_id: str, token: str = Depends(require_auth)):
    if task_id in state.scheduled_tasks:
        schedule.cancel_job(state.scheduled_tasks[task_id])
        del state.scheduled_tasks[task_id]
        return {"code": 200, "data": f"Task '{task_id}' deleted"}
    return {"code": 404, "data": "Task not found"}

@app.put("/api/tasks/{task_id}")
async def tasks_update(
    task_id: str,
    new_time: str = Body(...),
    token: str = Depends(require_auth)
):
    if task_id not in state.scheduled_tasks:
        return {"code": 404, "data": "Task not found"}

    old_job = state.scheduled_tasks[task_id]
    schedule.cancel_job(old_job)

    parts = task_id.split("_", 1)
    friend = parts[1] if len(parts) == 2 else "Unknown"

    new_play_time = format_time(new_time)
    msg = get_daily_quote()
    new_job = schedule.every().day.at(new_play_time).do(state.douyin.send_message, friend, msg)

    new_task_id = f"{new_play_time}_{friend}"
    state.scheduled_tasks[new_task_id] = new_job
    del state.scheduled_tasks[task_id]

    return {"code": 200, "data": {"old_id": task_id, "new_id": new_task_id}}

# =============================================================================
# API Routes - System
# =============================================================================

@app.get("/api/system/info")
async def system_info(token: str = Depends(require_auth)):
    return {
        "code": 200,
        "data": {
            "version": "2.0.0",
            "uptime": str(datetime.now() - state.start_time),
            "browser_initialized": state.browser_initialized,
            "user_logged_in": state.user_logged_in,
            "scheduled_tasks": len(state.scheduled_tasks),
            "last_login_ip": state.last_login_ip,
        }
    }

# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=False)

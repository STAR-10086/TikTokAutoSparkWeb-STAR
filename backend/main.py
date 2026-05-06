"""
TikTok Auto Spark - Backend API
FastAPI + Selenium automation service
"""

import os
import time
import base64
import hashlib
import secrets
import threading
from datetime import datetime
from typing import Optional

import uvicorn
import schedule
import requests
from fastapi import FastAPI, Header, Request, Query, Body, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
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

CREATOR_CHAT_URL = "https://creator.douyin.com/creator-micro/data/following/chat"

class DouyinBot:
    def __init__(self, driver):
        self.driver = driver
        self.friends_cache = {}

    def _ensure_all_tab(self):
        """Click the '全部' tab to show all conversations"""
        time.sleep(2)
        tab_selectors = ['.semi-tabs-tab', '.sub-tab-item-yeJmWL', '[class*="sub-tab-item-"]']
        for sel in tab_selectors:
            try:
                tabs = self.driver.find_elements(By.CSS_SELECTOR, sel)
                for tab in tabs:
                    if tab.text.strip() == '全部':
                        # Check if already active
                        cls = tab.get_attribute('class') or ''
                        aria = tab.get_attribute('aria-selected') or ''
                        if 'active' in cls or aria == 'true':
                            return
                        tab.click()
                        time.sleep(1.5)
                        return
            except:
                continue
        # Fallback: xpath
        for xpath in ['//div[contains(@class, "semi-tabs-tab")]//span[contains(text(), "全部")]',
                       '//span[contains(@class, "semi-tabs-tab-text") and contains(text(), "全部")]']:
            try:
                tab = self.driver.find_element(By.XPATH, xpath)
                tab.click()
                time.sleep(1.5)
                return
            except:
                continue

    def _collect_visible_friends(self, seen_names: set) -> list:
        """Collect currently visible conversation items"""
        items = []
        msg_list = []
        for sel in ['[class*="conversation-list-item-"]', '[class*="list-item-"]']:
            try:
                msg_list = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if msg_list:
                    break
            except:
                continue
        if not msg_list:
            for xpath in ['//div[contains(@class, "conversation-list")]//div[contains(@class, "item")]',
                          '//div[contains(@class, "chat-list")]//div[contains(@class, "item")]']:
                try:
                    msg_list = self.driver.find_elements(By.XPATH, xpath)
                    if msg_list:
                        break
                except:
                    continue

        for item in msg_list:
            try:
                name = None
                for sel in ['[class*="item-header-name-"]', '[class*="nick-name-"]', '[class*="name-"]']:
                    try:
                        el = item.find_element(By.CSS_SELECTOR, sel)
                        name = el.text.strip()
                        if name:
                            break
                    except:
                        continue
                if not name:
                    for xpath_sel in ['.//div[contains(@class, "name")]', './/span[contains(@class, "name")]']:
                        try:
                            name = item.find_element(By.XPATH, xpath_sel).text.strip()
                            if name:
                                break
                        except:
                            continue
                if not name or name in seen_names:
                    continue
                seen_names.add(name)
                avatar = ""
                try:
                    avatar = item.find_element(By.CSS_SELECTOR, 'img').get_attribute("src") or ""
                except:
                    pass
                items.append({"name": name, "avatar": avatar, "fire": ""})
            except:
                continue
        return items

    def get_friends_list(self):
        """Get list of friends from creator platform chat page (with scroll for virtual list)"""
        time.sleep(3)
        self._ensure_all_tab()

        friends = []
        self.friends_cache = {}
        seen_names = set()

        # Find the scrollable conversation list container
        scroll_container = None
        container_selectors = [
            '[class*="conversation-list-"]',
            '[class*="session-list-"]',
            '//div[contains(@class, "conversation-list")]',
        ]
        for sel in container_selectors:
            try:
                if sel.startswith('//'):
                    scroll_container = self.driver.find_element(By.XPATH, sel)
                else:
                    scroll_container = self.driver.find_element(By.CSS_SELECTOR, sel)
                if scroll_container:
                    break
            except:
                continue

        # Collect with incremental scrolling (virtual list loads more on scroll)
        max_scrolls = 30
        no_new_count = 0
        last_scroll_top = -1
        stuck_count = 0
        for _ in range(max_scrolls):
            new_items = self._collect_visible_friends(seen_names)
            if new_items:
                friends.extend(new_items)
                for f in new_items:
                    self.friends_cache[f["name"]] = {"avatar": f["avatar"], "fire": ""}
                no_new_count = 0
            else:
                no_new_count += 1

            if no_new_count >= 3:
                break

            # Check if reached bottom
            try:
                no_more = self.driver.find_elements(By.CSS_SELECTOR, '[class*="no-more-tip-"]')
                if no_more:
                    break
            except:
                pass

            # Incremental scroll down
            if scroll_container:
                try:
                    self.driver.execute_script(
                        "arguments[0].scrollTop += 500", scroll_container
                    )
                except:
                    break
            else:
                try:
                    self.driver.execute_script("window.scrollBy(0, 500)")
                except:
                    break
            time.sleep(0.5)
            # Check if actually scrolled
            if scroll_container:
                cur_top = self.driver.execute_script("return arguments[0].scrollTop", scroll_container)
            else:
                cur_top = self.driver.execute_script("return window.scrollY")
            if cur_top == last_scroll_top:
                stuck_count += 1
                if stuck_count >= 4:
                    break
            else:
                stuck_count = 0
            last_scroll_top = cur_top

        return friends

    def _find_and_click_user(self, name: str) -> bool:
        """Find and click a user in the conversation list, with scroll support"""
        list_selectors = ['[class*="conversation-list-item-"]', '[class*="list-item-"]']
        name_selectors = ['[class*="item-header-name-"]', '[class*="nick-name-"]', '[class*="name-"]']

        def _try_click_visible():
            list_items = []
            for sel in list_selectors:
                try:
                    list_items = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    if list_items:
                        break
                except:
                    continue
            for item in list_items:
                try:
                    for name_sel in name_selectors:
                        try:
                            name_el = item.find_element(By.CSS_SELECTOR, name_sel)
                            if name_el.text.strip() == name:
                                item.click()
                                return True
                        except:
                            continue
                except:
                    continue
            return False

        # Try without scroll first
        if _try_click_visible():
            return True

        # Scroll to find the user (virtual list)
        scroll_container = None
        sample = None
        for sel in ['[class*="item-header-name-"]']:
            try:
                sample = self.driver.find_element(By.CSS_SELECTOR, sel)
                break
            except:
                continue

        if sample:
            el = sample
            for _ in range(10):
                el = el.parent
                if not el or el.tag_name == 'body':
                    break
                overflow = self.driver.execute_script(
                    "return window.getComputedStyle(arguments[0]).overflowY", el
                )
                scroll_h = self.driver.execute_script("return arguments[0].scrollHeight", el)
                client_h = self.driver.execute_script("return arguments[0].clientHeight", el)
                if overflow in ('auto', 'scroll') and scroll_h > client_h + 10:
                    scroll_container = el
                    break

        if not scroll_container:
            return False

        no_more_sel = '[class*="no-more-tip-"]'
        last_scroll_top = -1
        stuck_count = 0
        for _ in range(30):
            if _try_click_visible():
                return True
            # Check if reached bottom
            try:
                self.driver.find_element(By.CSS_SELECTOR, no_more_sel)
                break
            except:
                pass
            self.driver.execute_script(
                "arguments[0].scrollTop += 500", scroll_container
            )
            time.sleep(0.4)
            cur_top = self.driver.execute_script("return arguments[0].scrollTop", scroll_container)
            if cur_top == last_scroll_top:
                stuck_count += 1
                if stuck_count >= 4:
                    break
            else:
                stuck_count = 0
            last_scroll_top = cur_top

        return False

    def send_message(self, name: str, text: str) -> bool:
        """Send message to a friend on creator platform"""
        if not self.friends_cache:
            self.get_friends_list()

        if name not in self.friends_cache:
            raise Exception(f"Friend '{name}' not found")

        try:
            if not self._find_and_click_user(name):
                raise Exception(f"Could not click on friend '{name}'")

            time.sleep(2)

            # Find input box (contenteditable div)
            input_el = None
            for sel in ['[class*="chat-input-"]', '[class*="message-input-"]', '[class*="editor-"]']:
                try:
                    input_el = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if input_el:
                        break
                except:
                    continue

            if not input_el:
                raise Exception("Could not find message input box")

            # Set content via JS (contenteditable div, send_keys won't work properly)
            lines = text.split('\n')
            inner_html = '<br>'.join(
                line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') or '<br>'
                for line in lines
            )
            self.driver.execute_script("arguments[0].textContent = ''", input_el)
            self.driver.execute_script("arguments[0].innerHTML = arguments[1]", input_el, inner_html)
            self.driver.execute_script("""
                arguments[0].dispatchEvent(new InputEvent('input', {
                    bubbles: true, cancelable: true, inputType: 'insertText', data: arguments[1]
                }))
            """, input_el, text)
            time.sleep(0.5)

            # Click send button
            send_btn = None
            for sel in ['.chat-btn', '[class*="chat-btn"]', '[class*="send-btn"]']:
                try:
                    send_btn = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if send_btn:
                        break
                except:
                    continue

            if send_btn:
                send_btn.click()
            else:
                input_el.send_keys(Keys.ENTER)

            time.sleep(1)
            return True
        except Exception as e:
            raise Exception(f"Failed to send message: {str(e)}")

    def find_friend(self, name: str) -> bool:
        """Check if friend exists"""
        if not self.friends_cache:
            self.get_friends_list()
        return name in self.friends_cache

    def init_login(self):
        """Click login button to show QR code on creator platform"""
        try:
            time.sleep(3)
            selectors = [
                '//button[contains(text(), "登录")]',
                '//p[contains(text(), "登录")]',
                '//div[contains(@class, "login")]//button',
                '//span[contains(text(), "登录")]',
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
        state.driver.get(CREATOR_CHAT_URL)
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
        state.driver.get(CREATOR_CHAT_URL)

        # Check if still on login page (login failed)
        time.sleep(2)
        for xpath in ['//button[contains(text(), "登录")]', '//p[contains(text(), "登录")]']:
            try:
                state.driver.find_element(By.XPATH, xpath)
                return {"code": 400, "data": "Login failed with cookie"}
            except NoSuchElementException:
                continue
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
        logged_in = False
        # Check for conversation list items (logged in)
        for sel in ['[class*="conversation-list-item-"]', '[class*="item-header-name-"]']:
            try:
                els = state.driver.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    logged_in = True
                    break
            except:
                continue
        if not logged_in:
            # Check if login button exists
            for xpath in ['//button[contains(text(), "登录")]', '//p[contains(text(), "登录")]']:
                try:
                    state.driver.find_element(By.XPATH, xpath)
                    logged_in = False
                    break
                except:
                    continue
            else:
                if "creator.douyin.com" in state.driver.current_url:
                    logged_in = True
        state.user_logged_in = logged_in
        return {"code": 200, "data": {"logged_in": state.user_logged_in}}
    except Exception as e:
        return {"code": 200, "data": {"logged_in": False, "error": str(e)}}

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
    state.driver.get(CREATOR_CHAT_URL)
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
    # Check login status if browser is initialized
    if state.browser_initialized:
        try:
            # Check for conversation list (means logged in and page loaded)
            logged_in = False
            check_selectors = [
                '[class*="conversation-list-item-"]',
                '[class*="item-header-name-"]',
            ]
            for sel in check_selectors:
                try:
                    els = state.driver.find_elements(By.CSS_SELECTOR, sel)
                    if els:
                        logged_in = True
                        break
                except:
                    continue
            if not logged_in:
                # Check if login button exists (not logged in)
                login_selectors = [
                    '//button[contains(text(), "登录")]',
                    '//p[contains(text(), "登录")]',
                ]
                for selector in login_selectors:
                    try:
                        state.driver.find_element(By.XPATH, selector)
                        logged_in = False
                        break
                    except:
                        continue
                else:
                    # No login button found, check page URL
                    if "creator.douyin.com" in state.driver.current_url:
                        logged_in = True
            state.user_logged_in = logged_in
        except:
            pass

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

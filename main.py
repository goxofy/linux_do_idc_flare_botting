import os
import random
import time
import logging
from dotenv import load_dotenv

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DiscourseAutoRead:
    def __init__(self, url, username=None, password=None, cookie_str=None):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.cookie_str = cookie_str
        self.driver = None

    def start(self):
        """Main entry point"""
        try:
            # Setup Chrome options
            options = uc.ChromeOptions()
            
            headless = os.getenv('HEADLESS', 'true').lower() == 'true'
            if headless:
                options.add_argument('--headless=new')
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--start-maximized')
            options.add_argument('--lang=zh-CN,zh,en-US,en')
            
            # Use Chrome installed by workflow if available
            chrome_path = "/opt/hostedtoolcache/setup-chrome/chromium/143.0.7499.192/x64/chrome"
            if os.path.exists(chrome_path):
                options.binary_location = chrome_path
                logger.info(f"Using Chrome from: {chrome_path}")
            else:
                logger.info("Chrome 143 not found at expected path, using system Chrome")
            
            logger.info("Launching undetected Chrome (v143)...")
            self.driver = uc.Chrome(
                options=options,
                use_subprocess=True,
                version_main=143
            )
            self.driver.set_page_load_timeout(60)
            
            user_agent = self.driver.execute_script("return navigator.userAgent")
            logger.info(f"User-Agent: {user_agent}")
            
            # Perform login
            if self.username and self.password:
                self.login_with_credentials()
            elif self.cookie_str:
                self.login_with_cookies()
            else:
                raise Exception("No authentication method provided")
            
            # Read unread posts
            self.read_posts()
            
            # Read new posts
            self.read_new_posts()
            
        except Exception as e:
            logger.error(f"Error: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()

    def start_without_quit(self):
        """Main entry point - keeps browser open for subsequent operations"""
        try:
            # Setup Chrome options
            options = uc.ChromeOptions()
            
            headless = os.getenv('HEADLESS', 'true').lower() == 'true'
            if headless:
                options.add_argument('--headless=new')
            
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--start-maximized')
            options.add_argument('--lang=zh-CN,zh,en-US,en')

            # Use Chrome installed by workflow if available
            chrome_path = "/opt/hostedtoolcache/setup-chrome/chromium/143.0.7499.192/x64/chrome"
            if os.path.exists(chrome_path):
                options.binary_location = chrome_path
                logger.info(f"Using Chrome from: {chrome_path}")
            else:
                logger.info("Chrome 143 not found at expected path, using system Chrome")

            logger.info("Launching undetected Chrome (v143)...")
            self.driver = uc.Chrome(
                options=options,
                use_subprocess=True,
                version_main=143
            )
            self.driver.set_page_load_timeout(60)

            user_agent = self.driver.execute_script("return navigator.userAgent")
            logger.info(f"User-Agent: {user_agent}")

            # Perform login
            if self.username and self.password:
                self.login_with_credentials()
            elif self.cookie_str:
                self.login_with_cookies()
            else:
                raise Exception("No authentication method provided")
            
            # Read unread posts
            self.read_posts()
            
            # Read new posts
            self.read_new_posts()
            
            # Note: Driver is NOT quit here - will be used for TuneHub check-in
            logger.info("Forum tasks completed. Browser kept alive for TuneHub check-in.")
            
        except Exception as e:
            logger.error(f"Error: {e}")
            if self.driver:
                self.driver.quit()
            raise

    def login_with_credentials(self):
        """Login using username and password"""
        login_url = f"{self.url}/login"
        logger.info(f"Navigating to {login_url}...")
        self.driver.get(login_url)
        
        time.sleep(5)
        self.handle_cloudflare()
        
        try:
            wait = WebDriverWait(self.driver, 30)
            username_field = wait.until(
                EC.presence_of_element_located((By.ID, "login-account-name"))
            )
            logger.info("Login form detected.")
            
            username_field.clear()
            username_field.send_keys(self.username)
            logger.info(f"Filled username: {self.username[:3]}***")
            time.sleep(0.5)
            
            password_field = self.driver.find_element(By.ID, "login-account-password")
            password_field.clear()
            password_field.send_keys(self.password)
            logger.info("Filled password: ***")
            time.sleep(0.5)
            
            login_button = self.driver.find_element(By.ID, "login-button")
            login_button.click()
            logger.info("Clicked login button.")
            
            login_timeout = int(os.getenv('LOGIN_TIMEOUT', '60'))
            logger.info(f"Waiting for login (timeout: {login_timeout}s)...")
            
            time.sleep(3)
            self.handle_cloudflare()
            
            try:
                wait = WebDriverWait(self.driver, login_timeout)
                wait.until(EC.presence_of_element_located((By.ID, "current-user")))
                logger.info("Login successful! User avatar detected.")
            except TimeoutException:
                raise Exception("Login failed: timeout waiting for user avatar")
                
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise

    def login_with_cookies(self):
        """Login using cookies"""
        logger.info("Using cookie-based authentication...")
        
        self.driver.get(self.url)
        time.sleep(3)
        self.handle_cloudflare()
        
        for chunk in self.cookie_str.split(';'):
            if '=' in chunk:
                name, value = chunk.strip().split('=', 1)
                if name and value:
                    try:
                        self.driver.add_cookie({'name': name, 'value': value})
                    except Exception as e:
                        logger.warning(f"Failed to add cookie {name}: {e}")
        
        logger.info("Cookies added. Refreshing page...")
        self.driver.refresh()
        time.sleep(3)
        self.handle_cloudflare()
        
        try:
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.ID, "current-user")))
            logger.info("Cookie login successful!")
        except TimeoutException:
            raise Exception("Cookie login failed")

    def handle_cloudflare(self):
        """Handle Cloudflare challenge if present"""
        try:
            title = self.driver.title
            if "Just a moment" in title or "Cloudflare" in title:
                logger.info("Cloudflare challenge detected. Waiting...")
                
                for i in range(30):
                    time.sleep(2)
                    new_title = self.driver.title
                    if "Just a moment" not in new_title and "Cloudflare" not in new_title:
                        logger.info("Cloudflare challenge passed!")
                        return
                    logger.info(f"Still waiting for Cloudflare... ({i+1}/30)")
                
                logger.warning("Cloudflare challenge timeout")
        except Exception as e:
            logger.info(f"Cloudflare check: {e}")

    def read_posts(self):
        """Read unread posts"""
        logger.info("Starting to read posts...")
        
        max_topics = int(os.getenv('MAX_TOPICS', 10))
        count = 0
        
        while count < max_topics:
            target_page = f"{self.url}/unread"
            logger.info(f"Navigating to {target_page}")
            self.driver.get(target_page)
            
            time.sleep(3)
            self.handle_cloudflare()
            
            try:
                wait = WebDriverWait(self.driver, 15)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".topic-list")))
                logger.info("Topic list loaded.")
            except TimeoutException:
                logger.warning("No topic list found.")
                break
            
            badge = self.get_first_unread_badge()
            if not badge:
                logger.info("No more unread topics. All caught up!")
                break
            
            logger.info(f"Reading topic ({count+1}/{max_topics})...")
            
            try:
                badge.click()
                time.sleep(2)
                
                if self.check_topic_error():
                    logger.error("Topic load error detected")
                    continue
                
                self.simulate_reading()
                count += 1
                logger.info(f"Finished reading topic {count}/{max_topics}")
                
            except Exception as e:
                logger.error(f"Failed to read topic: {e}")
                continue
        
        logger.info(f"Completed reading {count} topics.")

    def read_new_posts(self):
        """Read new posts from /new page"""
        max_new_topics = int(os.getenv('MAX_NEW_TOPICS', 20))
        logger.info(f"Starting to read new posts (max: {max_new_topics})...")
        
        count = 0
        visited_urls = set()
        
        while count < max_new_topics:
            target_page = f"{self.url}/new"
            logger.info(f"Navigating to {target_page}")
            self.driver.get(target_page)
            
            time.sleep(3)
            self.handle_cloudflare()
            
            try:
                wait = WebDriverWait(self.driver, 15)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".topic-list")))
                logger.info("Topic list loaded.")
            except TimeoutException:
                logger.warning("No topic list found on /new page.")
                break
            
            # Get topic links
            topic_link = self.get_first_new_topic(visited_urls)
            if not topic_link:
                logger.info("No more new topics to read.")
                break
            
            topic_url = topic_link.get_attribute('href')
            visited_urls.add(topic_url)
            
            logger.info(f"Reading new topic ({count+1}/{max_new_topics})...")
            
            try:
                topic_link.click()
                time.sleep(2)
                
                if self.check_topic_error():
                    logger.error("Topic load error detected")
                    continue
                
                self.simulate_reading()
                count += 1
                logger.info(f"Finished reading new topic {count}/{max_new_topics}")
                
            except Exception as e:
                logger.error(f"Failed to read new topic: {e}")
                continue
        
        logger.info(f"Completed reading {count} new topics.")

    def get_first_new_topic(self, visited_urls):
        """Find the first unvisited topic link on /new page"""
        try:
            topic_links = self.driver.find_elements(
                By.CSS_SELECTOR, ".topic-list-item .main-link a.title"
            )
            for link in topic_links:
                href = link.get_attribute('href')
                if href and href not in visited_urls and link.is_displayed():
                    logger.info(f"Found new topic: {link.text[:50]}...")
                    return link
        except Exception as e:
            logger.error(f"Error finding new topic: {e}")
        return None

    def get_first_unread_badge(self):
        """Find the first unread badge"""
        selectors = [
            "a.badge.badge-notification.unread-posts",
            ".badge-posts.badge-notification",
            "a.badge-posts[href*='?u=']",
            ".topic-list-item .badge-notification.new-posts",
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed():
                        logger.info(f"Found unread badge: {selector}")
                        return elem
            except Exception:
                continue
        
        try:
            elements = self.driver.find_elements(
                By.CSS_SELECTOR, ".topic-list-item a.badge-notification"
            )
            for elem in elements:
                if elem.is_displayed():
                    return elem
        except Exception:
            pass
        
        return None

    def check_topic_error(self):
        """Check if topic failed to load"""
        error_texts = ["无法加载", "连接问题", "error"]
        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            for error in error_texts:
                if error in page_text.lower():
                    return True
        except Exception:
            pass
        return False

    def simulate_reading(self):
        """Simulate reading by scrolling"""
        logger.info("Simulating reading...")
        
        viewport_height = self.driver.execute_script("return window.innerHeight")
        scroll_step = min(400, viewport_height - 100)
        
        start_time = time.time()
        max_time = 300
        bottom_count = 0
        
        while (time.time() - start_time) < max_time:
            pause = random.uniform(3.5, 5.0)
            time.sleep(pause)
            
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_y = self.driver.execute_script("return window.scrollY")
            
            if (scroll_y + viewport_height) >= (scroll_height - 50):
                bottom_count += 1
                if bottom_count >= 3:
                    logger.info("Reached bottom of topic.")
                    break
            else:
                bottom_count = 0
            
            self.driver.execute_script(f"window.scrollBy(0, {scroll_step})")
            time.sleep(0.5)
        
        # Random like before leaving the topic
        self.random_like()
        
        time.sleep(random.uniform(4, 6))
        logger.info("Finished reading topic.")

    def find_likeable_elements(self):
        """Find all likeable elements on the current page"""
        like_containers = []
        
        # Primary selector: Discourse Reactions plugin container
        try:
            containers = self.driver.find_elements(
                By.CSS_SELECTOR, "div.discourse-reactions-reaction-button"
            )
            for c in containers:
                try:
                    if c.is_displayed():
                        # Check if not already liked by looking for unliked icon
                        svg = c.find_element(By.CSS_SELECTOR, "svg.d-icon-d-unliked")
                        if svg:
                            like_containers.append(c)
                except Exception:
                    pass
        except Exception:
            pass
        
        # Fallback: Standard Discourse selectors
        if not like_containers:
            fallback_selectors = [
                "button.widget-button.like:not(.has-like):not(.my-likes)",
                "button.toggle-like:not(.has-like):not(.my-likes)",
            ]
            for selector in fallback_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    like_containers.extend([b for b in buttons if b.is_displayed()])
                except Exception:
                    continue
        
        return like_containers

    def random_like(self):
        """Random like 2-3 posts during reading"""
        # like_count = random.randint(2, 3)
        max_likes = int(os.getenv('MAX_LIKES', 5))
        like_count = random.randint((max_likes-1), max_likes)
        
        logger.info(f"Attempting to like {like_count} posts...")
        
        liked = 0
        liked_positions = set()  # Track positions we've already liked
        max_attempts = like_count * 3  # Prevent infinite loops
        attempts = 0
        
        while liked < like_count and attempts < max_attempts:
            attempts += 1
            
            try:
                # Re-find elements each time to avoid stale references
                like_containers = self.find_likeable_elements()
                
                if not like_containers:
                    if liked == 0:
                        logger.info("No likeable posts found.")
                    break
                
                if liked == 0:
                    logger.info(f"Found {len(like_containers)} likeable posts.")
                
                # Filter out positions we've already tried
                available = []
                for i, elem in enumerate(like_containers):
                    try:
                        # Use element location as position identifier
                        loc = elem.location
                        pos_key = f"{loc['x']},{loc['y']}"
                        if pos_key not in liked_positions:
                            available.append((elem, pos_key))
                    except Exception:
                        continue
                
                if not available:
                    logger.info("No more unliked posts available.")
                    break
                
                # Pick a random element
                element, pos_key = random.choice(available)
                liked_positions.add(pos_key)
                
                # Scroll to element
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                    element
                )
                time.sleep(random.uniform(0.5, 1.0))
                
                # Try regular click first, fallback to JavaScript click
                try:
                    element.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", element)
                
                liked += 1
                logger.info(f"Liked post {liked}/{like_count}")
                
                # Random delay between likes
                time.sleep(random.uniform(1.0, 2.0))
                
            except Exception as e:
                logger.warning(f"Failed to like post: {e}")
                continue
        
        logger.info(f"Successfully liked {liked} posts.")

    def tunehub_checkin(self):
        """Perform TuneHub daily check-in using Linux DO SSO"""
        logger.info("Starting TuneHub check-in...")
        
        tunehub_login_url = "https://tunehub.sayqz.com/login?redirect=/dashboard"
        
        try:
            # Step 1: Navigate to TuneHub login page
            logger.info(f"Navigating to {tunehub_login_url}...")
            self.driver.get(tunehub_login_url)
            time.sleep(3)
            
            # Step 2: Click "使用 Linux DO 账号一键登录" button
            try:
                wait = WebDriverWait(self.driver, 15)
                login_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//*[@id='app']/div/section/main/div[2]/div[2]/button"))
                )
                logger.info("Found TuneHub login button. Clicking...")
                login_button.click()
                time.sleep(3)
            except TimeoutException:
                # Try alternative selector
                try:
                    login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Linux')]")
                    login_button.click()
                    time.sleep(3)
                except Exception:
                    logger.error("Failed to find TuneHub login button")
                    return False
            
            # Step 3: Handle Linux DO OAuth authorization page
            # Check if we're on the authorization page (connect.linux.do)
            current_url = self.driver.current_url
            if "connect.linux.do" in current_url:
                logger.info("On Linux DO OAuth page. Looking for authorize button...")
                try:
                    wait = WebDriverWait(self.driver, 10)
                    # Try the XPath first
                    authorize_button = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/a[1]"))
                    )
                    logger.info("Found authorize button. Clicking '允许'...")
                    authorize_button.click()
                    time.sleep(3)
                except TimeoutException:
                    # Try alternative selectors for the authorize button
                    try:
                        authorize_button = self.driver.find_element(By.XPATH, "//a[contains(text(), '允许')]")
                        authorize_button.click()
                        time.sleep(3)
                    except Exception:
                        logger.warning("Could not find authorize button - may already be authorized")
            
            # Step 4: Wait for redirect to dashboard
            logger.info("Waiting for TuneHub dashboard...")
            try:
                wait = WebDriverWait(self.driver, 20)
                wait.until(EC.url_contains("tunehub.sayqz.com/dashboard"))
                logger.info("Successfully logged into TuneHub!")
                time.sleep(2)
            except TimeoutException:
                # Check if already on dashboard
                if "dashboard" not in self.driver.current_url:
                    logger.error("Failed to reach TuneHub dashboard")
                    return False
            
            # Step 5: Get current points before check-in
            try:
                points_element = self.driver.find_element(
                    By.XPATH, "//*[@id='app']/section/main/div/div[2]/div[1]/div/div/div/div[2]/span"
                )
                current_points = points_element.text.strip()
                logger.info(f"Current points before check-in: {current_points}")
            except Exception:
                # Try alternative selector for points
                try:
                    points_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'points') or ancestor::div[contains(text(), '积分')]]")
                    current_points = points_element.text.strip()
                    logger.info(f"Current points before check-in: {current_points}")
                except Exception:
                    current_points = "unknown"
                    logger.warning("Could not get current points")
            
            # Step 6: Click the daily check-in button
            logger.info("Looking for check-in button...")
            checkin_clicked = False
            try:
                checkin_button = self.driver.find_element(
                    By.XPATH, "//*[@id='app']/section/main/div/div[1]/button"
                )
                if checkin_button.is_displayed() and checkin_button.is_enabled():
                    logger.info("Found check-in button. Clicking '每日签到'...")
                    # Try regular click first
                    try:
                        checkin_button.click()
                    except Exception:
                        # Fallback to JavaScript click
                        self.driver.execute_script("arguments[0].click();", checkin_button)
                    checkin_clicked = True
                else:
                    logger.warning("Check-in button not clickable - may have already checked in today")
                    return True
            except Exception:
                # Try alternative selector
                try:
                    checkin_button = self.driver.find_element(By.XPATH, "//button[contains(text(), '签到')]")
                    try:
                        checkin_button.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", checkin_button)
                    checkin_clicked = True
                except Exception as e:
                    logger.warning(f"Could not find check-in button: {e}")
                    return True
            
            if not checkin_clicked:
                logger.warning("Check-in button was not clicked")
                return True
            
            # Step 7: Wait for check-in to complete
            # Primary method: wait for button text to change to "已签到"
            logger.info("Waiting for check-in to complete...")
            success_detected = False
            
            # Wait for button state change (button text becomes "已签到" or similar)
            for attempt in range(10):  # Try for up to 10 seconds
                time.sleep(1)
                try:
                    # Look for button with "已签到" text
                    checked_button = self.driver.find_element(
                        By.XPATH, "//button[contains(text(), '已签到')]"
                    )
                    if checked_button.is_displayed():
                        logger.info("Check-in successful! Button changed to '已签到'")
                        success_detected = True
                        break
                except Exception:
                    pass
                
                # Also check for success message
                try:
                    success_msg = self.driver.find_element(
                        By.XPATH, "//*[contains(text(), '签到成功')]"
                    )
                    if success_msg.is_displayed():
                        logger.info(f"Check-in success message: {success_msg.text}")
                        success_detected = True
                        break
                except Exception:
                    pass
                
                logger.info(f"Waiting for check-in response... ({attempt + 1}/10)")
            
            # Wait a bit more for points to update
            time.sleep(2)
            
            # Step 8: Get new points after check-in
            try:
                # Refresh to get updated points
                self.driver.refresh()
                time.sleep(3)
                
                # Wait for page to load
                try:
                    wait = WebDriverWait(self.driver, 10)
                    wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='app']")))
                except Exception:
                    pass
                
                time.sleep(2)
                
                points_element = self.driver.find_element(
                    By.XPATH, "//*[@id='app']/section/main/div/div[2]/div[1]/div/div/div/div[2]/span"
                )
                new_points = points_element.text.strip()
                logger.info(f"Points after check-in: {new_points}")
                
                if current_points != "unknown" and new_points != current_points:
                    logger.info(f"Check-in successful! Points changed: {current_points} -> {new_points}")
                elif success_detected:
                    logger.info("Check-in completed (success message was shown)")
                else:
                    logger.info("Check-in completed (points unchanged - may have already checked in today)")
                    
            except Exception:
                if success_detected:
                    logger.info("Check-in completed (success message was shown)")
                else:
                    logger.info("Check-in completed (could not verify new points)")
            
            return True

        except Exception as e:
            logger.error(f"TuneHub check-in failed: {e}")
            return False

    def _close_anyrouter_announcement(self):
        """Close AnyRouter system announcement dialog if present"""
        # XPath matches button/a/span/div with common close-dialog text
        close_xpath = (
            "//*[self::button or self::a or self::span or self::div]"
            "[contains(text(), '今日关闭') or contains(text(), '关闭公告') "
            "or contains(text(), '关闭') or contains(text(), '我知道了') "
            "or contains(text(), 'OK') or contains(text(), 'Close')]"
        )

        for attempt in range(3):
            try:
                wait = WebDriverWait(self.driver, 10)
                close_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, close_xpath))
                )
                logger.info(f"Found announcement dialog close button: "
                            f"<{close_button.tag_name}> '{close_button.text.strip()}'")
                self.driver.execute_script("arguments[0].click();", close_button)
                time.sleep(1)
                logger.info("System announcement dialog closed.")
                return
            except TimeoutException:
                if attempt < 2:
                    logger.debug(f"Announcement dialog not found (attempt {attempt + 1}/3), retrying...")
                    time.sleep(2)
                    continue
                # Final attempt failed - log page state for debugging and try ESC
                logger.info("No announcement dialog found after 3 attempts.")
                try:
                    from selenium.webdriver.common.keys import Keys
                    self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    logger.info("Sent ESC key as fallback to dismiss any overlay.")
                    time.sleep(1)
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Error closing announcement dialog: {e}")
                return

    def _clear_anyrouter_cookies(self):
        """Clear only anyrouter.top cookies (preserve linux.do cookies)"""
        logger.info("Clearing anyrouter.top cookies...")
        try:
            all_cookies = self.driver.get_cookies()
            removed = 0
            for cookie in all_cookies:
                domain = cookie.get('domain', '')
                if 'anyrouter' in domain:
                    self.driver.delete_cookie(cookie['name'])
                    removed += 1
            logger.info(f"Cleared {removed} anyrouter.top cookies (linux.do cookies preserved).")
        except Exception as e:
            logger.warning(f"Error clearing anyrouter cookies: {e}")

    def anyrouter_checkin(self):
        """Perform AnyRouter sign-in using Linux DO SSO with retry logic"""
        logger.info("Starting AnyRouter sign-in...")

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            logger.info(f"AnyRouter sign-in attempt {attempt}/{max_retries}")
            result = self._anyrouter_checkin_attempt()
            if result:
                logger.info("AnyRouter sign-in completed successfully!")
                return True

            if attempt < max_retries:
                logger.warning(f"AnyRouter sign-in attempt {attempt} failed. Clearing cookies and retrying...")
                self._clear_anyrouter_cookies()
                time.sleep(2)

        logger.error(f"AnyRouter sign-in failed after {max_retries} attempts.")
        return False

    def _anyrouter_checkin_attempt(self):
        """Single attempt of AnyRouter sign-in flow. Returns True on success, False on failure."""
        try:
            # Remember the original window handle
            original_window = self.driver.current_window_handle

            # Step 1: Navigate to AnyRouter login page
            login_url = "https://anyrouter.top/login"
            logger.info(f"Navigating to {login_url}...")
            self.driver.get(login_url)
            time.sleep(3)

            # Step 2: Close system announcement dialog
            self._close_anyrouter_announcement()

            # Step 3: Refresh the page
            logger.info("Refreshing page...")
            self.driver.refresh()
            time.sleep(3)

            # Step 4: Close system announcement dialog again (reappears after refresh)
            self._close_anyrouter_announcement()

            # Step 5: Find and click '使用 LinuxDO 继续' button (opens new tab)
            logger.info("Looking for '使用 LinuxDO 继续' button...")
            try:
                wait = WebDriverWait(self.driver, 15)
                linuxdo_button = wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(., 'LinuxDO') or contains(., 'Linux DO')]"
                    ))
                )
                logger.info("Found '使用 LinuxDO 继续' button. Clicking via JS...")
                self.driver.execute_script("arguments[0].click();", linuxdo_button)
                time.sleep(3)
            except TimeoutException:
                try:
                    linuxdo_button = self.driver.find_element(
                        By.XPATH, "//*[contains(text(), '使用 LinuxDO 继续')]"
                    )
                    logger.info("Found LinuxDO button via text match. Clicking...")
                    self.driver.execute_script("arguments[0].click();", linuxdo_button)
                    time.sleep(3)
                except Exception:
                    logger.error("Failed to find '使用 LinuxDO 继续' button")
                    return False

            # Step 6: Switch to the new tab (connect.linux.do/oauth2/authorize)
            logger.info("Waiting for new tab to open...")
            try:
                wait = WebDriverWait(self.driver, 10)
                wait.until(lambda d: len(d.window_handles) > 1)
                new_window = [w for w in self.driver.window_handles if w != original_window][0]
                self.driver.switch_to.window(new_window)
                logger.info(f"Switched to new tab. URL: {self.driver.current_url}")
                time.sleep(2)
            except TimeoutException:
                # No new tab opened - might have navigated in same tab
                logger.info(f"No new tab detected. Current URL: {self.driver.current_url}")
                if "connect.linux.do" not in self.driver.current_url:
                    logger.error("Not on OAuth authorization page and no new tab opened")
                    return False

            # Step 7: Click '允许' (authorize) button
            logger.info("Looking for '允许' (authorize) button...")
            try:
                wait = WebDriverWait(self.driver, 15)
                authorize_button = wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//*[contains(text(), '允许') and (self::button or self::a)]"
                    ))
                )
                logger.info("Found '允许' button. Clicking...")
                authorize_button.click()
                time.sleep(5)
            except TimeoutException:
                logger.warning("Could not find '允许' button - may already be authorized")

            # Step 8: Handle outcomes - check which tab has the result
            # After authorization, the new tab may redirect to anyrouter.top
            current_url = self.driver.current_url
            logger.info(f"URL after authorization: {current_url}")

            # Wait for redirect to anyrouter.top in current tab
            try:
                wait = WebDriverWait(self.driver, 20)
                wait.until(lambda d: "anyrouter.top" in d.current_url)
                current_url = self.driver.current_url
                logger.info(f"Redirected to AnyRouter: {current_url}")
                time.sleep(3)
            except TimeoutException:
                logger.warning(f"Timeout waiting for AnyRouter redirect. Current URL: {self.driver.current_url}")

            # Close extra tabs and switch back to a single window
            current_url = self.driver.current_url
            for handle in self.driver.window_handles:
                if handle != self.driver.current_window_handle:
                    self.driver.switch_to.window(handle)
                    self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            # Check for success: redirected to /console/token
            if "anyrouter.top/console/token" in current_url:
                logger.info("AnyRouter sign-in successful! Redirected to /console/token.")
                return True

            # Check for failure: error message or redirected back to /login
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            if "请尝试清除 Cookie 后重新登录" in page_text or "/login" in self.driver.current_url:
                logger.warning("AnyRouter sign-in failed: error message detected or redirected to /login.")
                return False

            # If on anyrouter.top but not on /login, navigate to /console/token to verify
            if "anyrouter.top" in self.driver.current_url and "login" not in self.driver.current_url:
                logger.info("On AnyRouter but not on token page. Navigating to /console/token...")
                self.driver.get("https://anyrouter.top/console/token")
                time.sleep(3)
                if "login" not in self.driver.current_url:
                    logger.info("AnyRouter sign-in successful!")
                    return True
                else:
                    logger.warning("Redirected back to login page.")
                    return False

            logger.warning(f"AnyRouter sign-in unclear. Current URL: {self.driver.current_url}")
            return False

        except Exception as e:
            logger.error(f"AnyRouter sign-in attempt failed: {e}")
            return False

def main():
    configs = []
    
    if os.getenv('TARGET_URL'):
        configs.append({
            'url': os.getenv('TARGET_URL'),
            'username': os.getenv('USERNAME'),
            'password': os.getenv('PASSWORD'),
            'cookie': os.getenv('COOKIE_STRING')
        })
    
    if os.getenv('TARGET_URL_2'):
        configs.append({
            'url': os.getenv('TARGET_URL_2'),
            'username': os.getenv('USERNAME_2'),
            'password': os.getenv('PASSWORD_2'),
            'cookie': os.getenv('COOKIE_STRING_2')
        })
    
    if not configs:
        logger.error("No TARGET_URL found.")
        return
    
    for cfg in configs:
        logger.info(f"Starting auto-read for: {cfg['url']}")
        is_linux_do = 'linux.do' in cfg['url'].lower()
        
        try:
            bot = DiscourseAutoRead(
                url=cfg['url'],
                username=cfg.get('username'),
                password=cfg.get('password'),
                cookie_str=cfg.get('cookie')
            )
            
            if is_linux_do:
                # For linux.do: keep browser open for TuneHub check-in
                try:
                    bot.start_without_quit()
                except Exception as e:
                    logger.error(f"LinuxDO forum browsing error: {e}")
                    logger.info("Continuing to check-in flow despite forum error...")
                
                # Immediately perform TuneHub check-in while session is active
                # This runs even if start_without_quit() failed, as we might already be logged in
                try:
                    logger.info("=" * 50)
                    logger.info("Proceeding to TuneHub check-in using Linux DO session...")
                    bot.tunehub_checkin()
                except Exception as e:
                    logger.error(f"TuneHub check-in error: {e}")

                # Immediately perform AnyRouter sign-in using the same session
                try:
                    logger.info("=" * 50)
                    logger.info("Proceeding to AnyRouter sign-in using Linux DO session...")
                    bot.anyrouter_checkin()
                except Exception as e:
                    logger.error(f"AnyRouter sign-in error: {e}")
                finally:
                    if bot.driver:
                        bot.driver.quit()
                        logger.info("Linux DO browser closed.")
            else:
                # For other forums: normal start with auto-quit
                bot.start()
                
        except Exception as e:
            logger.error(f"Error processing {cfg['url']}: {e}")


if __name__ == "__main__":
    main()

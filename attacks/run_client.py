import subprocess
import time
import psutil
import pyautogui
import shutil
import copy
import pytesseract
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

clients = ['claude-desktop', 'librechat']

LIBRECHAT_EMAIL_ENV = "LIBRECHAT_EMAIL"
LIBRECHAT_PASSWORD_ENV = "LIBRECHAT_PASSWORD"

NO_APP = 0
START_APP = 1
OPEN_CHAT_PROJECT = 2
TALK_START = 3
INPUT = 4
TALK_WAIT = 5
TALK_END = 6
EXIT_APP = 0

class MCPClient():
    def __init__(self, name):
        if name not in clients:
            print(f'do not support {name}')
        if name == 'claude':
            name ='claude-desktop'
        self.client = name
        self.menu_location = None
        self.chat_location = None
        self.status = NO_APP
        self.mode = ''

    def run_client(self):
        if self.client == 'claude-desktop':
            proc = subprocess.Popen(self.client)    
            self.menu_location = self.is_there_any_btn('claude_menu.png', 120)
            if not self.menu_location:
                return False
        elif self.client == 'windsurf':
            proc = subprocess.Popen(self.client)
            open_cascade = self.is_there_any_btn('windsurf_cascade_menu_pressed.png', timeout = 3)
            if not open_cascade:
                pyautogui.hotkey('ctrl', 'L')
            self.chat_location = self.is_there_any_btn('windsurf_input_box.png', timeout=30)
            if not self.chat_location:
                return False
            location = self.is_there_any_btn('windsurf_chat_mode.png', timeout=3)
            if not location:
                pyautogui.click(self.chat_location)
                pyautogui.hotkey('ctrl', '.')
        elif self.client == 'librechat':
            proc = subprocess.Popen('cd ~/LibreChat && npm run backend > log.txt', shell=True)
            time.sleep(80)
        self.starter_pid = proc.pid
        self.status = START_APP
        return True

    @staticmethod
    def get_descendants(pid):
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            return children
        except psutil.NoSuchProcess:
            return []

    def terminate_client(self):
        descendants = self.get_descendants(self.starter_pid)

        for proc in descendants:
            try:
                print(f"[-] Terminate PID={proc.pid}, CMD={' '.join(proc.cmdline())}")
                proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        try:
            psutil.Process(self.starter_pid).terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        gone, alive = psutil.wait_procs([psutil.Process(self.starter_pid)] + self.get_descendants(self.starter_pid), timeout=5)

        for proc in alive:
            try:
                print(f"[!] Forcing kill of PID {proc.pid}")
                proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        print("[OK] termination completed.")


    def exit_client(self):
        if self.client == 'claude-desktop':
            location = pyautogui.locateCenterOnScreen('claude_exit_btn.png', confidence=0.9)
            pyautogui.click(location)
            
            pyautogui.press('down', presses = 2, interval = 0.5)
            pyautogui.press('enter')
            self.status = NO_APP
        if self.client == 'librechat':
            self.driver.quit()

    def kill_daemon(self):
        if self.client == 'librechat':
            self.terminate_client()

    def load_mcp_tools(self):
        if self.client == 'librechat':
            mcp_button = self.driver.find_element(By.XPATH, '//div[@class="badge-icon min-w-fit"]/button[@role="combobox"]')
            label_span = mcp_button.find_element(By.XPATH, './/span[@class="mr-auto hidden truncate md:block"]')
            mcp_button.click()
            time.sleep(0.5)
            options = self.driver.find_elements(By.XPATH, '//div[@role="option"]')
            for option in options:
                is_selected = option.get_attribute("aria-selected") == "true"
                if not is_selected:
                    option.click()
            ActionChains(self.driver).move_by_offset(10, 10).click().perform()

    def input_operations(self, prompt, timeout = 240, skip_alert=True):
        if self.client == 'claude-desktop':
            self.chat_location = self.is_there_any_btn('claude_in_chat_project.png', timeout=1)
            if self.chat_location or self.status == OPEN_CHAT_PROJECT:
                self.status = OPEN_CHAT_PROJECT
            else:
                print('has not opened the chat project')
                return False
            start_time = time.time()
            temp_status = 0
            start_time = time.time()
            location = self.is_there_any_btn("claude_talk_waiting.png", timeout=timeout)
            temp_status = 1
            duration = time.time() - start_time
            timeout -= duration

            if not location:
                return False
            pyautogui.click(self.chat_location)
            #clear
            pyautogui.hotkey('space')
            pyautogui.hotkey('ctrl', 'a')
            pyautogui.press('backspace')
            #input
            self.status = INPUT
            pyautogui.write(prompt, interval=0.1)
            pyautogui.press('enter')
            pyautogui.hotkey('ctrl', 'enter')
            if skip_alert:
                if self.wait_and_click_button('claude_permission_button.png', timeout=timeout) == False:
                    return False
            else:
                time.sleep(timeout)
            
        elif self.client == 'windsurf':
            if self.chat_location is None:
                self.chat_location = self.is_there_any_btn('windsurf_input_box.png', timeout=1)
            if self.chat_location is None:
                return False
            pyautogui.click(self.chat_location)
            pyautogui.write(prompt, interval=0.1)
            pyautogui.press('enter')
            pyautogui.hotkey('ctrl', 'enter')
            time.sleep(timeout)

        elif self.client == 'librechat':
            WebDriverWait(self.driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
            textarea = self.driver.find_element(By.ID, "prompt-textarea")
            time.sleep(0.2)
            textarea.clear()
            textarea.send_keys(prompt)
            send_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="send-button"]')
            send_button.click()
            start_time = time.time()
            system_status = 0 #not starting
            while time.time() - start_time < timeout:
                s = self.running_status()
                if system_status == 0 and s == 0:
                    system_status = 0 # not start
                elif system_status == 0 and s == 1:
                    system_status = 1 # has run
                elif system_status == 1 and s == 0:
                    system_status = 2 # completed
                    break
                time.sleep(0.8)
            
            if s == 2: #error
                return False
            if system_status == 0:
                return False
            elif system_status == 1:#timeout
                running_btn = self.driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Stop generating"]')
                print('timeout')
                try:
                    running_btn.click() #manually stop
                except:
                    pass
                return False
            else:
                if self._is_librechat_error():
                    return False
                elif self._has_librechat_sent_empty():
                    return False
                else:
                    return True
        return True

    def new_chat(self):
        if self.client == 'librechat':
            nav = self.driver.find_element(By.CSS_SELECTOR, 'div[data-testid="nav"]')
            nav_style = nav.get_attribute('style')
            if 'translateX(-100%)' in nav_style and 'width: 0px' in nav_style:
                #nav not opened
                button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="wide-header-new-chat-button"]')
            else:
                button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="nav-new-chat-button"]')
            button.click()
            if 'http://localhost:3080/c/new' not in self.driver.current_url:
                return False
        if self.client == 'claude-desktop':
            self.status = INPUT
            if self.status == INPUT:
                print(' back to project')
                self.back_to_upper_chat_project()
                self.status = OPEN_CHAT_PROJECT
        
        return True

    def librechat_web_login(self):
        if '/login' not in self.driver.current_url:
            return
        email_input = self.driver.find_element(By.ID, "email")
        email_input.clear()
        email = os.environ.get(LIBRECHAT_EMAIL_ENV)
        password = os.environ.get(LIBRECHAT_PASSWORD_ENV)
        if not email or not password:
            return
        email_input.send_keys(email)

        password_input = self.driver.find_element(By.ID, "password")
        password_input.clear()
        password_input.send_keys(password)

        login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="login-button"]')
        login_button.click()
        time.sleep(1)


    def open_chat_project(self, timeout=20):
        if self.client == 'claude-desktop':
            if not self.is_there_any_btn('claude_nav_bar.png', timeout=0.5):
                if self.menu_location == None:
                    try:
                        self.menu_location = self.is_there_any_btn('claude_menu.png', timeout=0.5)
                    except:
                        print('hahha')
                        return False
                pyautogui.click(self.menu_location)
                time.sleep(2)
            location = self.is_there_any_btn('claude_project_menu.png', timeout=2)
            if not location:
                print('hahahah')
                return False
            pyautogui.click(location)
            time.sleep(4)

            start_time = time.time()
            self.chat_location = self.is_there_any_btn('claude_test_btn.png', timeout=3)
            if not self.chat_location:
                print('hahahah1')
                return False
            pyautogui.click(self.chat_location)
            self.status = OPEN_CHAT_PROJECT
            time.sleep(1)
        elif self.client == 'librechat':
            options = webdriver.ChromeOptions()
            self.driver.get("http://localhost:3080")
            WebDriverWait(self.driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
            if '/login' in self.driver.current_url:
                self.librechat_web_login()
                time.sleep(1)
        return True

    def back_to_upper_chat_project(self):
        if self.client == 'claude-desktop':
            self.status = INPUT
            if self.status == INPUT:
                self.upper_proj = self.is_there_any_btn('claude_chat_project_directory.png', timeout=3)
                if self.upper_proj is None:
                    return False
                pyautogui.click(self.upper_proj)
                self.status = OPEN_CHAT_PROJECT
        time.sleep(0.5)
        return True

    def is_there_any_btn(self, btn_name, timeout=3, confidence=0.9):    
        start_time = time.time()
        newname = btn_name.removesuffix('.png')
        btn_name_list = [btn_name]
        for i in range(5):
            t = newname + str(i) + '.png'
            if os.path.exists(t):
                btn_name_list.append(t)
        while time.time() - start_time < timeout:
            try:
                location = pyautogui.locateCenterOnScreen(btn_name, confidence=confidence)
                return location
            except Exception as e:
                continue
            time.sleep(0.8)
        return None
    
    def is_there_any_text(self, key, timeout=40):
        from PIL import Image
        start_time = time.time()
        while time.time() - start_time < timeout:        
            screenshot = pyautogui.screenshot()
            text = pytesseract.image_to_string(screenshot, lang='eng')
            if isinstance(key, str):
                if key in text:
                    return key
            elif isinstance(key, list):
                for k in key:
                    if k in text:
                        return k
            time.sleep(1)
        
        return None
    

    def is_there_any_multi_btns(self, btn_lists, timeout=3):    
        start_time = time.time()
        while time.time() - start_time < timeout:            
            for b in btn_lists:
                try:
                    location = pyautogui.locateCenterOnScreen(b, confidence=0.8)
                    print('found')
                    return location
                except:
                    continue
            time.sleep(0.5)
        return None

    def select_model(self, name):
        if self.client == 'librechat':
            Provider = "openAI"
            if "gpt" in name:
                Provider = "openAI"
            if "claude" in name:
                Provider = "anthropic"
            if "deepseek" in name:
                Provider = 'Deepseek'
            wait = WebDriverWait(self.driver, 10)
            model_menu = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Select a model"]')))
            ActionChains(self.driver).move_to_element(model_menu).perform()
            model_menu.click()

            openai_option = wait.until(EC.element_to_be_clickable((By.ID, f"endpoint-{Provider}-menu")))
            ActionChains(self.driver).move_to_element(openai_option).perform()

            model_option = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH, f'//div[@role="option"]//span[text()="{name}"]'
                ))
            )
            model_option.click()


    def delete_talks(self, num=-1, offset=0):
        if self.client == 'claude-desktop':
            time.sleep(1)
            talk_waiting_btn = self.is_there_any_btn('claude_talk_waiting.png', timeout=0.5)
            if self.status != OPEN_CHAT_PROJECT:
                if not talk_waiting_btn:
                    return False
                self.status = OPEN_CHAT_PROJECT
            deletion = 0
            print('start deletion ...')
            i = 0
            if talk_waiting_btn is not None:
                pyautogui.click(talk_waiting_btn.x, talk_waiting_btn.y + 80)
                deletion = 1
                while deletion == 1:
                    location = self.is_there_any_btn('claude_talk_deletion.png', timeout=1.5)
                    if not location:
                        deletion = 0
                        break
                    pyautogui.click(location)
                    i += 1
                    if num > 0 and i >= num:
                        break
                    time.sleep(0.5)
                    pyautogui.click(talk_waiting_btn.x, talk_waiting_btn.y + 80)
            print('end deletion')
            return True
 
    
        if self.client == 'librechat':
            nav = self.driver.find_element(By.CSS_SELECTOR, 'div[data-testid="nav"]')
            nav_style = nav.get_attribute('style')
            if 'translateX(-100%)' in nav_style and 'width: 0px' in nav_style:
                #nav not opened
                button = self.driver.find_element(By.CSS_SELECTOR, 'button[data-testid="open-sidebar-button"]')
                button.click()
            conversaton_area = self.driver.find_element(By.CSS_SELECTOR, 'div[aria-label="Conversations"]')
            self.driver.execute_script("arguments[0].scrollTop = 0;", conversaton_area)
            i = 0
            while True:
                if num >= 0 and i >= num:
                    print(i, num)
                    break
                items = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="convo-item"]')
                if len(items) <= offset:
                    break
                i += 1
                item = items[offset]
                
                actions = ActionChains(self.driver)
                actions.move_to_element(item).click().perform()
    
                print('delete', offset, i, item.text)
                time.sleep(0.5)
     
                btn = item.find_element(By.CSS_SELECTOR, 'button[id^="conversation-menu-"]')
                btn.click()

                portal = self.driver.find_element(By.CSS_SELECTOR, 'div[role="menu"].popover-ui')
                menu_items = portal.find_elements(By.CSS_SELECTOR, 'button[role="menuitem"]')
                delete_btn = menu_items[-1]
                delete_btn.click()
                wait = WebDriverWait(self.driver, 5)
                dialog = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="dialog"]')))
                btns = dialog.find_elements(By.XPATH, '//button')
                btns[-1].click()
                time.sleep(0.5)

        return True
        

    def wait_and_click_button(self, permission_image_path, timeout=120, interval=0.8, confidence=0.9):
        start_time = time.time()
        system_status = 0
        while time.time() - start_time < timeout:
            s = self.running_status()
            if system_status == 0 and s == 0:
                system_status = 0 # not start
            elif system_status == 0 and s == 1:
                system_status = 1 # running
            elif system_status == 1 and s == 0:
                system_status = 2 # completed
                break
            if system_status == 1:
                location = self.is_there_any_btn(permission_image_path, timeout = 0.01)
                if location:
                    pyautogui.click(location)
                time.sleep(1)
            time.sleep(0.8) 
        if s == 2:#error
            return False
        if system_status == 0:
            return False
        elif system_status == 1: #timeout
            print(f'timeout > {timeout}')
            location = self.is_there_any_btn('claude_talk_running.png', timeout=0.1)
            pyautogui.click(location)
            return False
        else:
            if self._is_claude_error(): #error
                return False
            return True

    def _is_claude_running(self):
        location = self.is_there_any_btn('claude_talk_running.png', timeout = 0.01)
        if not location:
            return False
        return True

    def _is_claude_waiting(self):
        location = self.is_there_any_btn('claude_talk_waiting.png', timeout = 0.01)
        if not location:
            return False
        return True

    def _is_librechat_running(self):
        running_btns = self.driver.find_elements(By.CSS_SELECTOR, 'button[aria-label="Stop generating"]')
        if len(running_btns) > 0:
            return True
        running_btns = self.driver.find_elements(By.CSS_SELECTOR, 'button[aria-label="\u505c\u6b62\u751f\u6210"]')
        if len(running_btns) > 0:
            return True
        return False

    def _is_librechat_to_submit(self):
        to_submit_btns = self.driver.find_elements(By.CSS_SELECTOR, 'button[aria-label="Send message"]')
        if len(to_submit_btns) > 0:
            return True
        to_submit_btns = self.driver.find_elements(By.CSS_SELECTOR, 'button[aria-label="\u53d1\u9001\u6d88\u606f"]')
        if len(to_submit_btns) > 0:
            return True
        return False

    def _is_librechat_error(self):
        errors = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="alert"][aria-live="assertive"]')
        return len(errors) > 0

    def _is_claude_error(self):
        location = self.is_there_any_btn('claude_internal_error.png', timeout = 0.01)
        if location:
            return True
        return False

    def _has_librechat_sent_empty(self):
        agent_turns = self.driver.find_elements(By.CSS_SELECTOR, ".agent-turn")
        if len(agent_turns) == 0:
            return True
        last_agent_turn = agent_turns[-1]
        content_div = last_agent_turn.find_element(By.CSS_SELECTOR, ".flex.max-w-full.flex-grow.flex-col.gap-0")
        content_text = content_div.text
        if content_text.strip() == "":
            return True
        return False

    def running_status(self):
        if self.client == 'librechat':
            if self._is_librechat_running() == True:
                return 1 #running
            elif self._is_librechat_to_submit() == True:
                return 0 #to_submit
        if self.client == 'claude-desktop':
            if self._is_claude_running() == True:
                return 1 #running
            elif self._is_claude_waiting() == True:
                return 0 #to_submit
        return 2
    


if __name__ == '__main__':
    c = MCPClient("claude-desktop")

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from pathlib import Path

class WebScraper:

    def __init__(self, game_url):
        # Create Chrome options
        chrome_options = Options()
        
        # Set up user data directory to persist login sessions
        # This keeps you logged in between runs
        user_data_dir = Path.home() / '.linkedin_games_solver_chrome'
        user_data_dir.mkdir(exist_ok=True)
        
        # Add user data directory to Chrome options to persist sessions
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
        # Prevent Chrome from showing "Chrome is being controlled by automated software" banner
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Try using webdriver-manager first for automatic ChromeDriver management
        # This downloads the correct version matching your Chrome browser
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        except ImportError:
            # Fallback to Selenium Manager (Selenium 4.6+)
            # Service() without arguments should use Selenium Manager to auto-download the driver
            try:
                service = Service()
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception:
                # Final fallback: try without Service (may still have version issues)
                self.driver = webdriver.Chrome(options=chrome_options)
        
        self.driver.maximize_window()
        self.open_url(game_url)

    def open_url(self, url):
        self.driver.get(url)

    @staticmethod
    def print_error_output_screenshot(driver, e, error_message, file_name):
        print(error_message)
        driver.save_screenshot(file_name + ".png")
        raise e

    def get_driver(self):
        return self.driver

    def quit_driver(self):
        self.driver.quit()

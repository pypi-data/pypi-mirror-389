# pip install selenium
# pip install webdriver-manager
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager

from os import getcwd

Chrome_options =webdriver.ChromeOptions()
Chrome_options.add_argument("--use-fake-ui-for-media-stream")

Chrome_options.add_argument("--headless=new")

driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=Chrome_options)

# website=f"{getcwd()}\\index.html"
website="https://gauravch.netlify.app"

driver.get(website)

rec_file =f"{getcwd()}\\input.txt"

def listen():
    try:
        start_button = WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.ID,'startButton')))
        start_button.click()
        print("Start Listening...")
        output_text=""
        is_second_click =False
        while True:
            output_element= WebDriverWait(driver,20).until(EC.presence_of_element_located((By.ID,'output')))
            current_text=output_element.text.strip()

            if "Start Listening" in start_button.text and is_second_click:
                if output_text:
                    is_second_click =False
            elif "listening..." in start_button.text:
                is_second_click=True
            if current_text != output_text:
                output_text = current_text
                with open(rec_file,"w") as file:
                 file.write(output_text.lower())
                print("USER : "+ output_text)
                time.sleep(0.3) # small delay to prevent high CPU usage
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)
    finally:
        driver.quit()
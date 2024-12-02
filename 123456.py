import requests
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# GitHub raw 文件 URL
earthquake_data_url = "https://raw.githubusercontent.com/BILILICHENG/JPJSJH-DV-AUTO/refs/heads/main/earthquake_data.txt"
latest_earthquake_data_url = "https://raw.githubusercontent.com/BILILICHENG/JPJSJH-DV-AUTO/refs/heads/main/latest_earthquake_data.txt"

def fetch_earthquake_data():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    url = "https://www.data.jma.go.jp/multi/quake/index.html?lang=jp"
    driver.get(url)

    time.sleep(5)

    try:
        table = driver.find_element(By.CLASS_NAME, 'quakeindex_table')
        rows = table.find_elements(By.TAG_NAME, 'tr')

        data = []
        for row in rows[1:]:
            cols = row.find_elements(By.TAG_NAME, 'td')
            if len(cols) > 4:
                earthquake_time = cols[0].text.strip()
                location = cols[1].text.strip()
                magnitude = cols[2].text.strip()
                max_intensity = cols[3].text.strip()
                announcement_time = cols[4].text.strip()

                data.append([earthquake_time, location, magnitude, max_intensity, announcement_time])

        if data:
            df = pd.DataFrame(data, columns=['地震検知日時', '震央地名', 'マグニチュード', '最大震度', '発表日時'])

            formatted_data = [f"{row[0]}={row[1]}={row[2]}={row[3]}={row[4]}" for row in data]

            # 通过 requests 获取文件内容
            try:
                saved_data = requests.get(earthquake_data_url).text.splitlines()
            except Exception as e:
                saved_data = []

            try:
                latest_data = requests.get(latest_earthquake_data_url).text.splitlines()
            except Exception as e:
                latest_data = []

            new_data = [line for line in formatted_data if line + "\n" not in saved_data]

            if new_data:
                # 更新 latest_earthquake_data.txt 文件
                with open('latest_earthquake_data.txt', 'w', encoding='utf-8') as f:
                    f.writelines([line + "\n" for line in new_data])

                # 更新 earthquake_data.txt 文件
                with open('earthquake_data.txt', 'w', encoding='utf-8') as f:
                    f.writelines([line + "\n" for line in formatted_data])

                message = ""
                for line in new_data:
                    parts = line.strip().split('=')
                    formatted_message = f"震央地名：{parts[1]}\nマグニチュード：{parts[2]}\n最大震度：{parts[3]}\n地震検知日時：{parts[0]}\n気象庁発表日時：{parts[4]}"
                    message += formatted_message + "\n------------\n"
                
                print("发送的消息内容：", message)

                payload = {
                    "content": message
                }
                response = requests.post(DISCORD_WEBHOOK_URL, json=payload)

                if response.status_code == 204:
                    print("已成功发送 Discord！")
                else:
                    # 打印 Discord 返回的错误信息
                    print(f"发送 Discord 时发生错误：{response.status_code}")
                    print("错误信息：", response.text)
            else:
                print("没有新的数据。")

        else:
            print("没有数据。")

    except Exception as e:
        print(f"错误: {e}")
    
    finally:
        driver.quit()

fetch_earthquake_data()

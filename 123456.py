import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
import os

# GitHub 上的原始文件链接
GITHUB_REPO = "https://raw.githubusercontent.com/BILILICHENG/JPJSJH-DV-AUTO/refs/heads/main/earthquake_data.txt"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# 获取远程文件内容
def get_remote_file(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text.splitlines()
        else:
            print(f"Error fetching file from {url}, status code {response.status_code}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []

# 更新地震数据
def fetch_earthquake_data():
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
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

            # 通过 URL 获取已存储的地震数据
            saved_data = get_remote_file(f"{GITHUB_REPO}earthquake_data.txt")
            latest_data = get_remote_file(f"{GITHUB_REPO}latest_earthquake_data.txt")

            # 找到新数据
            new_data = [line for line in formatted_data if line + "\n" not in saved_data]

            if new_data:
                # 将新数据发送到 Discord
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
                    print(f"发送 Discord 时发生错误：{response.status_code}")
                    print("错误信息：", response.text)

                # 更新 GitHub 上的文本文件
                with open('earthquake_data.txt', 'w', encoding='utf-8') as f:
                    f.writelines([line + "\n" for line in formatted_data])

                with open('latest_earthquake_data.txt', 'w', encoding='utf-8') as f:
                    f.writelines([line + "\n" for line in new_data])

            else:
                print("没有新的数据。")

        else:
            print("没有数据。")

    except Exception as e:
        print(f"错误: {e}")
    
    finally:
        driver.quit()

fetch_earthquake_data()

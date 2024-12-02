import requests
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd

# 设置无头浏览器选项
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')

# 从环境变量读取 Discord Webhook URL
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def fetch_earthquake_data():
    # 打开浏览器并访问目标网站
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    url = "https://www.data.jma.go.jp/multi/quake/index.html?lang=jp"
    driver.get(url)

    # 等待页面加载
    time.sleep(5)

    try:
        # 抓取地震数据表格
        table = driver.find_element(By.CLASS_NAME, 'quakeindex_table')
        rows = table.find_elements(By.TAG_NAME, 'tr')

        data = []
        for row in rows[1:]:  # 跳过表头
            cols = row.find_elements(By.TAG_NAME, 'td')
            if len(cols) > 4:
                earthquake_time = cols[0].text.strip()
                location = cols[1].text.strip()
                magnitude = cols[2].text.strip()
                max_intensity = cols[3].text.strip()
                announcement_time = cols[4].text.strip()
                data.append([earthquake_time, location, magnitude, max_intensity, announcement_time])

        if data:
            # 转换为 DataFrame 并格式化为字符串列表
            formatted_data = [f"{row[0]}={row[1]}={row[2]}={row[3]}={row[4]}" for row in data]

            # 尝试读取本地文件内容
            saved_data = []
            latest_data = []
            try:
                with open('earthquake_data.txt', 'r', encoding='utf-8') as f:
                    saved_data = f.readlines()
            except FileNotFoundError:
                pass

            try:
                with open('latest_earthquake_data.txt', 'r', encoding='utf-8') as f:
                    latest_data = f.readlines()
            except FileNotFoundError:
                pass

            # 找出新的地震数据
            new_data = [line for line in formatted_data if line + "\n" not in saved_data]

            # 如果有新数据，则更新文件并发送到 Discord
            if new_data:
                with open('latest_earthquake_data.txt', 'w', encoding='utf-8') as f:
                    f.writelines([line + "\n" for line in new_data])

                with open('earthquake_data.txt', 'w', encoding='utf-8') as f:
                    f.writelines([line + "\n" for line in formatted_data])

                message = ""
                for line in new_data:
                    parts = line.strip().split('=')
                    formatted_message = f"震央地名：{parts[1]}\nマグニチュード：{parts[2]}\n最大震度：{parts[3]}\n地震検知日時：{parts[0]}\n気象庁発表日時：{parts[4]}"
                    message += formatted_message + "\n------------\n"

                # 打印调试信息
                print("发送的消息内容：", message)

                # 发送到 Discord
                payload = {
                    "content": message
                }
                response = requests.post(DISCORD_WEBHOOK_URL, json=payload)

                if response.status_code == 204:
                    print("已成功发送 Discord！")
                else:
                    print(f"发送 Discord 时发生错误：{response.status_code}")
                    print("错误信息：", response.text)
            else:
                print("没有新的数据。")
        else:
            print("没有抓取到数据。")

    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        driver.quit()

fetch_earthquake_data()

import requests
import time
import os
import difflib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

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

            # 从GitHub raw链接获取存储的地震数据
            url = "https://raw.githubusercontent.com/BILILICHENG/JPJSJH-DV-AUTO/refs/heads/main/earthquake_data.txt"  # 替换为实际的raw文件链接
            response = requests.get(url)
            saved_data = response.text.splitlines()

            # 比对气象厅获取到的数据和GitHub存储的数据
            new_data = []
            for line in formatted_data:
                if line not in saved_data:
                    new_data.append(line)

            # 如果有新数据
            if new_data:
                # 保存新数据到latest_earthquake_data.txt
                with open('latest_earthquake_data.txt', 'w', encoding='utf-8') as f:
                    f.writelines([line + "\n" for line in new_data])

                # 更新完整数据文件
                with open('earthquake_data.txt', 'w', encoding='utf-8') as f:
                    f.writelines([line + "\n" for line in formatted_data])

                # 生成Discord消息
                message = ""
                for line in new_data:
                    parts = line.strip().split('=')
                    formatted_message = f"震央地名：{parts[1]}\nマグニチュード：{parts[2]}\n最大震度：{parts[3]}\n地震検知日時：{parts[0]}\n気象庁発表日時：{parts[4]}"
                    message += formatted_message + "\n------------\n"
                
                # 发送Discord通知
                payload = {"content": message}
                response = requests.post(DISCORD_WEBHOOK_URL, json=payload)

                if response.status_code == 204:
                    print("已成功发送 Discord！")
                else:
                    print(f"发送 Discord 时发生错误：{response.status_code}")
                    print("错误信息：", response.text)

            else:
                print("没有新的数据。")
                # 即使没有新数据，还是保存气象厅的最新数据
                with open('earthquake_data.txt', 'w', encoding='utf-8') as f:
                    f.writelines([line + "\n" for line in formatted_data])

        else:
            print("没有数据。")

    except Exception as e:
        print(f"错误: {e}")
    
    finally:
        driver.quit()

fetch_earthquake_data()

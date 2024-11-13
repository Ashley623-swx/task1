import os
import json

# 文件夹路径
folder_path = r"D:\Documents\Desktop\data\candidates\5156"
# 替换成想查找的案件id来查找不同的案件
target_ajId = "ced4ec95-8d88-4b7e-ad4d-64fa2e568340"

# 遍历文件夹中的每个.json文件
for filename in os.listdir(folder_path):
    if filename.endswith(".json"):
        file_path = os.path.join(folder_path, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            if data.get("ajId") == target_ajId:
                print(f"{filename}")

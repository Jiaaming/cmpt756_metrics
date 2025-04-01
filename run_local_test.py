import subprocess
import time

websites = [
    "http://34.55.148.209",  # baseline
    "http://34.122.196.51",  # replica
    "http://34.133.176.226", # CPU/memory 
    "http://34.29.21.137",   # HPA
    "http://34.16.90.199",   # istio
]

users = 100  
spawn_rate = 10  
run_time = "1m" 

for website in websites:
    print(f"开始测试网站: {website}")
    command = [
        "locust",
        "--host", website,
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", run_time,
        "--headless",  
        "--csv", f"results_{website.replace('http://', '').replace('.', '_')}"  # 保存结果为 CSV
    ]
    subprocess.run(command)
    print(f"完成测试网站: {website}")
    time.sleep(10)
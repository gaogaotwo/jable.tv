import os
import re
from Crypto.Cipher import AES
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
import time
################ 以下参数需进行配置
# 该网站需要代理相关的操作，需进行相关配置
proxy_url = "http://127.0.0.1:10810"
# 视频下载链接
url = "https://jable.tv/videos/stars-244/"
# 线程池数量
thread_nums = 20
#################

file_tile = url.split('/')[4]
req_url = ""
iv = ""
# 创建的临时目录
temp_dir = Path('./temp_dir')
temp_sol_dir = Path('./temp_sol')
vedio_dir = Path('./vedio')

# 获取m3u8 ts列表
def jable_init(proxy_url, url):
    global req_url
    global iv
    # 相关命令，字符串缩进需注意一下，可能会报错
    cmd = 'curl -L -o ./hlsUrl.txt -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36" -H "Referer: https://jable.tv/" -H "Accept-L: zh-CN,zh;q=0.9" -H "Sec-Fetch-User: ?1" -H "Sec-Ch-Ua: \"Not?A_Brand\";v=\"99\", \"Chromium\";v=\"90\", \"Google  Chrome\";v=\"90\"" -H "Sec-Ch-Ua-Mobile: ?0" -H "Sec-Ch-Ua-Platform: \"Windows\"" -H "Cache-Control: no-cache" -H "Pragma: no-cache" -x ' + proxy_url + " " + url + ' >hlsUrl.txt'
    print(cmd)
    os.system(cmd)
    with open('./hlsUrl.txt', 'rb') as f:
        text = f.read()
    hlsUrl = re.findall(r"var hlsUrl = '(.*?)';", text.decode('utf-8'))
    rls = hlsUrl[0].split('/')
    # 修复一下，URL链接并不确定，需修复
    for i in range(len(rls) - 1):
        req_url = req_url + rls[i] + "/"
        
    cmd = 'curl -L  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36" -H "Referer: https://jable.tv/" -H "Accept-L: zh-CN,zh;q=0.9" -H "Sec-Fetch-User: ?1" -H "Sec-Ch-Ua: \"Not?A_Brand\";v=\"99\", \"Chromium\";v=\"90\", \"Google  Chrome\";v=\"90\"" -H "Sec-Ch-Ua-Mobile: ?0" -H "Sec-Ch-Ua-Platform: \"Windows\"" -H "Cache-Control: no-cache" -H "Pragma: no-cache" -x ' + proxy_url + "  " +"\"" +hlsUrl[0] +"\"" +' > ./ts.txt'
    print(cmd)
    os.system(cmd)
    with open('./ts.txt', 'rb') as f:
        text = f.read()
    m3u8_ts = re.findall(r"\n(\d+\.ts)\n", text.decode('utf-8'))
    m3u8_key = re.findall(r'URI="([^"]+)"', text.decode('utf-8'))
    m3u8_iv = re.findall(r'IV=0x([0-9a-fA-F]+)', text.decode('utf-8'))
    iv = bytes.fromhex(m3u8_iv[0])
    # 获取m3u8 加密密钥
    cmd = 'curl -L -o ./temp_dir/m3u8.key -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36" -H "Referer: https://jable.tv/" -H "Accept-L: zh-CN,zh;q=0.9" -H "Sec-Fetch-User: ?1" -H "Sec-Ch-Ua: \"Not?A_Brand\";v=\"99\", \"Chromium\";v=\"90\", \"Google  Chrome\";v=\"90\"" -H "Sec-Ch-Ua-Mobile: ?0" -H "Sec-Ch-Ua-Platform: \"Windows\"" -H "Cache-Control: no-cache" -H "Pragma: no-cache" -x  ' + proxy_url + " " + "\"" + req_url + m3u8_key[0]+"\"" + ' > ./temp_dir/m3u8.key'
    os.system(cmd)
    return m3u8_ts

# 下载ts视频片段
def get_content(u):
    cotent = "\""+req_url + u+"\""
    cmd = 'curl --connect-timeout 15 --retry 5 -L -o ./temp_dir/' + u + ' -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36" -H "Referer: https://jable.tv/" -H "Accept-L: zh-CN,zh;q=0.9" -H "Sec-Fetch-User: ?1" -H "Sec-Ch-Ua: \"Not?A_Brand\";v=\"99\", \"Chromium\";v=\"90\", \"Google  Chrome\";v=\"90\"" -H "Sec-Ch-Ua-Mobile: ?0" -H "Sec-Ch-Ua-Platform: \"Windows\"" -H "Cache-Control: no-cache" -H "Pragma: no-cache" -x ' + proxy_url + " " + cotent + ' > ./temp_dir/' + u
    os.system(cmd)
    
# ts视频片段解密
def m3u8_fix(m3u8_ts):
    key = open('./temp_dir/m3u8.key', 'rb')
    cipher = AES.new(key.read(), AES.MODE_CBC, iv)
    for ts in m3u8_ts:
        try:
            t = open('./temp_dir/' + ts, 'rb')
            tf = open('./temp_sol/' + ts, 'wb')
            tf.write(cipher.decrypt(t.read()))
            t.close()
            tf.close()
        except:
            print("ts子文件未成功下载")
    key.close()
# ts视频片段合并
def file_merging(m3u8_ts):
    with open('./vedio/' + file_tile + ".mp4" , 'wb') as f:
        for ts in m3u8_ts:
            # 异常捕捉，存在部分子视频片段未成功下载
            try:
                # 注意文件名称是否符号规范,r以二进制的形式打开二进制文件
                with open('./temp_sol/' + ts, 'rb') as tf:
                    f.write(tf.read())
            except:
                print("ts子文件未成功下载", ts)
    tf.close()
    f.close()
    shutil.rmtree('./temp_dir')
    shutil.rmtree('./temp_sol')
    print("合并文件完成")

if __name__ == '__main__':
    print('jable.tv多线程下载工具')
    start_time = time.time()
    temp_dir.mkdir(exist_ok=True)
    temp_sol_dir.mkdir(exist_ok=True)
    vedio_dir.mkdir(exist_ok=True)

    m3u8_ts = jable_init(proxy_url, url)
    print(m3u8_ts)
    # 开启线程池
    executor = ThreadPoolExecutor(max_workers=int(thread_nums))
    result = executor.map(get_content, m3u8_ts)
    # 关闭线程池
    executor.shutdown(wait=True)
    # m3u8 解密
    m3u8_fix(m3u8_ts)
    # 合并视频片段
    file_merging(m3u8_ts)
    end_time = time.time()
    print(" 已加载完毕" + " 花费时间: " + str(end_time - start_time) + ' s \n')

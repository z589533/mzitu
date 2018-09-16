import re
import os
import time
import threading
import hashlib

from urllib.parse import quote
from multiprocessing import Pool, cpu_count

from PIL import Image, ImageDraw, ImageFont

import requests
from bs4 import BeautifulSoup

HEADERS = {
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Referer': 'http://www.mzitu.com'
}
# http://www.xicidaili.com/ 代理服务器
proxies = {"http": "http://120.92.74.189:3128"}
# proxies = {}
# test下载图片保存路径
# DIR_PATH = r"C:\love\mzitu\jpg"

DIR_PATH = r"/application/image"

# 指定要使用的字体和大小；/Library/Fonts/是macOS字体目录；Linux的字体目录是/usr/share/fonts/
font = ImageFont.truetype(r"./font/msyh.ttf", 21)

# 保存路径
reques_url = r"http://127.0.0.1:9999/lovehot/api/v1/rest/postImageData"


# DIR_PATH = r"D:\mzitu"

def get_urls():
    """
    获取 mzitu 网站下所有套图的 url
    """
    page_urls = ['http://www.mzitu.com/page/{cnt}'.format(cnt=cnt)
                 for cnt in range(1, 193)]
    print("Please wait for second ...")
    img_urls = []
    for page_url in page_urls:
        try:
            bs = BeautifulSoup(
                requests.get(page_url, headers=HEADERS, timeout=60, proxies=proxies).text,
                'lxml').find('ul', id="pins")
            result = re.findall(r"(?<=href=)\S+", str(bs))  # 匹配所有 urls
            img_url = [url.replace('"', "") for url in result]
            img_urls.extend(img_url)
        except Exception as e:
            print("http请求异常================>")
            print(e)
    return set(img_urls)  # 利用 set 去重 urls


lock = threading.Lock()  # 全局资源锁


def urls_crawler(url):
    """
    爬虫入口，主要爬取操作
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, proxies=proxies).text
        folder_name = BeautifulSoup(r, 'lxml').find(
            'div', class_="main-image").find('img')['alt'].replace("?", " ")

        type_name = BeautifulSoup(r, 'lxml').find(
            'div', class_="main-meta").find('a').get_text()

        print(type_name)
        with lock:
            # folder_name 套图名称
            m = hashlib.md5(folder_name.encode(encoding='utf-8'))
            filename = m.hexdigest()[8:-8]
            if make_dir(filename):
                # 套图里图片张数
                max_count = BeautifulSoup(r, 'lxml').find(
                    'div', class_='pagenavi').find_all('span')[-2].get_text()
                page_urls = [url + "/" + str(i) for i in range(1, int(max_count) + 1)]
                img_urls = []

                for _, page_url in enumerate(page_urls):
                    time.sleep(0.25)
                    result = requests.get(page_url, headers=HEADERS, timeout=60, proxies=proxies).text
                    img_url = BeautifulSoup(result, 'lxml').find(
                        'div', class_="main-image").find(
                        'p').find('a').find('img')['src']
                    img_urls.append(img_url)
                for cnt, url in enumerate(img_urls):
                    save_pic(url, cnt)

                print(len(img_urls))
                aItem = {}
                aItem["filename"] = filename
                aItem["source"] = "mzitu"
                aItem["title"] = quote(folder_name, 'utf-8')
                aItem["typename"] = type_name
                aItem["imgsize"] = len(img_urls)
                requests.post(reques_url, aItem, timeout=60).text
    except Exception as e:
        print(e)


def save_pic(pic_src, pic_cnt):
    """
    保存图片到本地
    """
    try:
        time.sleep(0.10)
        print("图片地址===" + pic_src)
        img = requests.get(pic_src, headers=HEADERS, timeout=60, proxies=proxies)
        img_name = "love_img_{}.jpg".format(pic_cnt + 1)
        with open(img_name, 'ab') as f:
            f.write(img.content)
            print("图片文件名========>" + img_name)
            im = Image.open(img_name)
            # 图片的宽度和高度
            img_size = im.size
            # print("图片宽度和高度分别是{}".format(img_size))
            w = img_size[0]
            h = img_size[1] - 22
            x = 0
            y = 0
            region = im.crop((x, y, w, h))
            region.save(img_name)
            add_text_to_image(region, img_name, 'h.love5868.com')
    except Exception as e:
        print("截图异常=====>")
        print(e)


# image: 图片  text：要添加的文本 font：字体
def add_text_to_image(image, img_name, text, font=font):
    try:
        draw = ImageDraw.Draw(image)
        text_size_x, text_size_y = draw.textsize(text, font=font)
        # 设置文本文字位置
        text_xy = (image.size[0] - text_size_x - 10, image.size[1] - text_size_y - 20)
        draw.text(text_xy, text, (255, 0, 0), font=font)  # 设置文字位置/内容/颜色/字体
        draw = ImageDraw.Draw(image)
        image.save(img_name)
    except Exception as e:
        print("水印异常=====>")
        print(e)


def make_dir(folder_name):
    """
    新建文件夹并切换到该目录下
    """
    path = os.path.join(DIR_PATH, folder_name)
    # 如果目录已经存在就不用再次爬取了，去重，提高效率。存在返回 False，否则反之
    if not os.path.exists(path):
        os.makedirs(path)
        print(path)
        os.chdir(path)
        return True
    print("Folder has existed!")
    return False


def delete_empty_dir(save_dir):
    """
    如果程序半路中断的话，可能存在已经新建好文件夹但是仍没有下载的图片的
    情况但此时文件夹已经存在所以会忽略该套图的下载，此时要删除空文件夹
    """
    if os.path.exists(save_dir):
        if os.path.isdir(save_dir):
            for d in os.listdir(save_dir):
                path = os.path.join(save_dir, d)  # 组装下一级地址
                if os.path.isdir(path):
                    delete_empty_dir(path)  # 递归删除空文件夹
        if not os.listdir(save_dir):
            os.rmdir(save_dir)
            print("remove the empty dir: {}".format(save_dir))
    else:
        print("Please start your performance!")  # 请开始你的表演


if __name__ == "__main__":
    urls = get_urls()
    pool = Pool(processes=cpu_count())
    try:
        delete_empty_dir(DIR_PATH)
        pool.map(urls_crawler, urls)
    except Exception:
        time.sleep(30)
        delete_empty_dir(DIR_PATH)
        pool.map(urls_crawler, urls)

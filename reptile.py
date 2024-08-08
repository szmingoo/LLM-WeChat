url = "https://mp.weixin.qq.com/s/m-bhr27BcdCOS7mQjIztEw"  # 替换为您的目标 URL

import os
import random
import string
import asyncio
import aiohttp
from playwright.async_api import async_playwright


async def extract_image_data_src(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle')

        image_urls = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('img[data-src]'))
                .map(img => img.getAttribute('data-src'))
                .filter(src => 
                    src.startsWith('https://mmbiz.qpic.cn/sz_mmbiz_jpg/') || 
                    src.startsWith('https://mmbiz.qpic.cn/mmbiz_png/')
                );
        }''')

        await browser.close()
        return image_urls


def generate_random_filename(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


async def download_image(session, url, folder):
    async with session.get(url) as response:
        if response.status == 200:
            filename = f"{generate_random_filename()}.jpg"
            filepath = os.path.join(folder, filename)
            with open(filepath, 'wb') as f:
                f.write(await response.read())
            print(f"Downloaded {url} to {filepath}")


async def save_text(url, output_txt_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle')
        # 提取所有 p 标签下第一个 span 标签的文本，过滤特定内容
        span_texts = await page.evaluate('''() => {
            const paragraphs = document.querySelectorAll('p');
            let texts = [];
            paragraphs.forEach(p => {
                const firstSpan = p.querySelector('span');
                if (firstSpan) {
                    const text = firstSpan.innerText.trim();
                    if (text !== '愚昧成为主流 清醒便是犯罪' && text !== '- THE END -') {
                        texts.push(text);
                    }
                }
            });
            return texts;
        }''')

        # 将提取的文本保存到 txt 文件中
        with open(output_txt_path, 'a+', encoding='utf-8') as f:
            for text in span_texts:
                f.write(text + '\n')

        await browser.close()


async def main(url, folder, output_txt_path):
    if not os.path.exists(folder):
        os.makedirs(folder)

    image_urls = await extract_image_data_src(url)
    print(f"Total matching image URLs found: {len(image_urls)}")

    async with aiohttp.ClientSession() as session:
        tasks = [download_image(session, image_url, folder) for image_url in image_urls]
        await asyncio.gather(*tasks)

    await save_text(url, output_txt_path)

folder = "images"  # Folder to save images
output_txt_path = "content.txt"
asyncio.run(main(url, folder, output_txt_path))


import os
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
import random
import string


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text(), response.status


async def get_og_title(session, url):
    html, status = await fetch(session, url)
    if status == 200:
        soup = BeautifulSoup(html, 'html.parser')
        og_title_meta = soup.find('meta', property="og:title")
        if og_title_meta and og_title_meta.get('content'):
            return og_title_meta['content']
        else:
            return 'og:title meta tag not found'
    else:
        return f'Failed to retrieve content, status code: {status}'


async def get_og_image(session, url):
    html, status = await fetch(session, url)
    if status == 200:
        soup = BeautifulSoup(html, 'html.parser')
        og_image_meta = soup.find('meta', property="og:image")
        if og_image_meta and og_image_meta.get('content'):
            return og_image_meta['content']
        else:
            return 'og:image meta tag not found'
    else:
        return f'Failed to retrieve content, status code: {status}'


async def download_cover_image(session, url, directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

    random_filename = f"{generate_random_filename()}.jpg"
    img_path = os.path.join(directory, random_filename)

    async with session.get(url) as response:
        if response.status == 200:
            img_data = await response.read()
            with open(img_path, 'wb') as handler:
                handler.write(img_data)
            return img_path
        else:
            return f'Failed to download image, status code: {response.status}'

async def header_main(url):
    async with aiohttp.ClientSession() as session:
        og_title = await get_og_title(session, url)
        og_image_url = await get_og_image(session, url)

        print(og_image_url)
        print(og_title)

        with open('title.txt', 'a+', encoding='utf-8') as file:
            file.write(og_title + '\n')

        if "http" in og_image_url:
            img_path = await download_cover_image(session, og_image_url, 'cover')
            print(f"Image downloaded and saved at: {img_path}")
        else:
            print(og_image_url)

asyncio.run(header_main(url))

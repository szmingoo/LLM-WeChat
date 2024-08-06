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


async def save_page_as_pdf(url, output_pdf_path):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle')

        # 使用 JavaScript 删除指定的 div、img 标签和 select 标签
        await page.evaluate('''() => {
            const metaContent = document.getElementById('meta_content');
            if (metaContent) {
                metaContent.remove();
            }
            const images = document.querySelectorAll('img');
            images.forEach(img => img.remove());
            const profileCards = document.querySelectorAll('.appmsg_card_context.wx_profile_card.wx-root.wx_tap_card.wx_card_root.common-webchat');
            profileCards.forEach(card => card.remove());
        }''')

        # 保存页面为 PDF
        await page.pdf(path=output_pdf_path, format='A4')
        await browser.close()


async def main(url, folder, output_pdf_path):
    if not os.path.exists(folder):
        os.makedirs(folder)

    image_urls = await extract_image_data_src(url)
    print(f"Total matching image URLs found: {len(image_urls)}")

    async with aiohttp.ClientSession() as session:
        tasks = [download_image(session, image_url, folder) for image_url in image_urls]
        await asyncio.gather(*tasks)

    await save_page_as_pdf(url, output_pdf_path)


if __name__ == "__main__":
    url = "https://mp.weixin.qq.com/s/s7OnAoKuLM4UFdO_jIicUw"  # 替换为您的目标 URL
    folder = "images"  # Folder to save images
    output_pdf_path = "output.pdf"
    asyncio.run(main(url, folder, output_pdf_path))

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime

seeds = ['https://www.bbc.com/portuguese', 'https://www.bbc.com/', 'https://g1.globo.com/', 'https://www.cnnbrasil.com.br/', 'https://edition.cnn.com/']

numberRequests = 0
limitNumberRequests = 100000

CONCURRENT_REQUESTS = 10

async def fetch_page(session, url, file, semaphore):
    global numberRequests
    async with semaphore:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    numberRequests += 1
                    file.write(url + '\n')
                    html = await response.text()
                    soup = BeautifulSoup(html, features='html.parser')
                    return soup
                else:
                    print(f'Erro ao acessar a página. Código: {response.status}')
                    return None
        except Exception as e:
            print(f'Erro ao acessar a página: {e}')
            return None

async def scrape(baseUrl, file, semaphore):
    pagesToVisit = [baseUrl]
    async with aiohttp.ClientSession() as session:
        tasks = []
        while pagesToVisit:
            currentUrl = pagesToVisit.pop(0)

            task = asyncio.create_task(fetch_page(session, currentUrl, file, semaphore))
            tasks.append(task)

            soup = await task
            if soup and numberRequests < limitNumberRequests:
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link.get('href')
                    if href.startswith(baseUrl) and href not in pagesToVisit:
                        pagesToVisit.append(href)

        await asyncio.gather(*tasks)


async def main():
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)
    with open('urls_acessadas2.txt', 'w', encoding='utf-8') as file:
        file.write(datetime.now().strftime("%H:%M:%S") + '\n')
        tasks = [scrape(seed, file, semaphore) for seed in seeds]
        await asyncio.gather(*tasks)
        file.write(f'\n>>>>>Quantidade de páginas visitadas: {numberRequests}')
        file.write(datetime.now().strftime("%H:%M:%S") + '\n')

asyncio.run(main())

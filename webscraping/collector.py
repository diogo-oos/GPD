import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime
import json
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import re

seeds = ['https://www.bbc.com/portuguese', 'https://www.bbc.com/', 'https://g1.globo.com/', 'https://www.cnnbrasil.com.br/', 'https://edition.cnn.com/']

numberRequests = 0
limitNumberRequests = 100000

CONCURRENT_REQUESTS = 10

nltk.download('stopwords')

stop_words = set(stopwords.words('portuguese'))
stemmer = SnowballStemmer('portuguese')

def clean_text(text):
    # Remover HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Remover caracteres especiais e números
    text = re.sub(r'\W+', ' ', text)
    # Transformar em minúsculas
    text = text.lower()
    # Tokenização e remoção de stopwords
    tokens = [word for word in text.split() if word not in stop_words]
    # Stemming
    tokens = [stemmer.stem(word) for word in tokens]
    return ' '.join(tokens)

def process_data(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    processed_data = []
    for entry in data:
        url = entry['url']
        content = clean_text(entry['content'])
        processed_data.append({'url': url, 'content': content})
    
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(processed_data, file, ensure_ascii=False, indent=4)

async def fetch_page(session, url, semaphore, data):
    global numberRequests
    async with semaphore:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    numberRequests += 1
                    html = await response.text()
                    soup = BeautifulSoup(html, features='html.parser')
                    data.append({'url': url, 'content': html})
                    return soup
                else:
                    print(f'Erro ao acessar a página. Código: {response.status}')
                    return None
        except Exception as e:
            print(f'Erro ao acessar a página: {e}')
            return None

async def scrape(baseUrl, semaphore, data):
    pagesToVisit = [baseUrl]
    async with aiohttp.ClientSession() as session:
        tasks = []
        while pagesToVisit:
            currentUrl = pagesToVisit.pop(0)

            task = asyncio.create_task(fetch_page(session, currentUrl, semaphore, data))
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
    data = []
    tasks = [scrape(seed, semaphore, data) for seed in seeds]
    await asyncio.gather(*tasks)
    with open('collected_data.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    print(f'\n>>>>>Quantidade de páginas visitadas: {numberRequests}')

print("running")
asyncio.run(main())
process_data('collected_data.json', 'processed_data.json')
print("finished")
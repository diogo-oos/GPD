from abc import ABC, abstractmethod
from redis_config.redis import Redis
from aiohttp import ClientSession
from bs4 import BeautifulSoup
import asyncio
import hashlib
from spacy_config.nlp_load import nlp
from unidecode import unidecode

class BaseScraper(ABC):
  def __init__(self, seeds: str, source: str):
      self.seeds = seeds
      self.source = source
      self.redis = Redis()
      self.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
      }

  async def make_request(self, url: str) -> str:
    async with ClientSession() as session:
      async with session.get(url, headers=self.headers) as response:
        return await response.text()
      
  async def build_seeds_soups(self) -> None:
    tasks = [self.make_request(url) for url in self.seeds]
    responses = await asyncio.gather(*tasks)
    return [BeautifulSoup(response, 'html.parser') for response in responses]
  
  async def get_all_cached_news(self) -> list[dict]:
    return await self.redis.get_all_by_pattern(f'{self.source}:*')

  @abstractmethod
  async def paginate_soup(seed: str, soup: BeautifulSoup) -> None:
    pass

  @abstractmethod
  async def scrape_page(self, soup: BeautifulSoup) -> list[dict]:
    pass

  @abstractmethod
  async def scrape_news_from_page(self, news: BeautifulSoup) -> dict:
    pass

  def build_news_hash(self, news_title: str, seed: str) -> str:
    hash = hashlib.md5()
    hash.update(f'{seed};{news_title}'.encode())
    return f'{self.source}:{hash.hexdigest()}'
  
  def load_news_tokens(self, news_title: str, news_hash: str) -> None:
    doc = nlp(news_title)
    tokens = [unidecode(token.lemma_) for token in doc if not token.is_stop and not token.is_punct]
    tasks = [self.redis.append_to_list(token.lower(), news_hash) for token in tokens]
    return asyncio.gather(*tasks)

  async def scrape(self) -> None:
    soups = await self.build_seeds_soups()
    tasks = [self.paginate_soup(self.seeds[index], soup) for index, soup in enumerate(soups)]
    await asyncio.gather(*tasks)
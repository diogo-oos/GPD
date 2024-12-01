from redis_config.redis import Redis
from spacy_config.nlp_load import nlp
from unidecode import unidecode
import asyncio
from scrapers.bbc_scraper import BBCScraper
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.utils import flat_list

class SearchEngine:
  def __init__(self):
    self.redis = Redis()

  async def get_hash_list(self, query: str) -> list[str]:
    doc = nlp(query)
    tokens = [unidecode(token.lemma_) for token in doc if not token.is_stop and not token.is_punct]
    tasks = [self.redis.get_list_by_pattern(token.lower()) for token in tokens]
    return flat_list(await asyncio.gather(*tasks))
  
  async def lemmatize_text(self, text: str) -> str:
    doc = nlp(text)
    return ' '.join([unidecode(token.lemma_) for token in doc if not token.is_stop and not token.is_punct])
  
  async def sort_news_by_similarity(self, news: list[dict], query: str) -> list[dict]:
    lemmatize_titles_tasks = [self.lemmatize_text(news_item['title']) for news_item in news]
    lemmatized_titles = await asyncio.gather(*lemmatize_titles_tasks)
    
    vectorizer = TfidfVectorizer()
    
    title_vectors = vectorizer.fit_transform(lemmatized_titles)
    query_vector = vectorizer.transform([query])

    similarities = cosine_similarity(title_vectors, query_vector).flatten()

    scores = {key: similarities[i] for i, key in enumerate(lemmatized_titles)}

    title_lemmatized_title_map = {news_item['title']: lemmatized_titles[i] for i, news_item in enumerate(news)}

    return sorted(news, key=lambda item: scores[title_lemmatized_title_map[item['title']]], reverse=True)
  
  def remove_duplicates(self, news: list[dict]) -> list[dict]:
    seen = set()
    unique_news = []
    for news_item in news:
      if news_item['link'] not in seen:
        unique_news.append(news_item)
        seen.add(news_item['link'])
    return unique_news

  
  async def search_news(self, query: str) -> list[dict]:
    sanitized_query = await self.lemmatize_text(query)
    scrape = BBCScraper()
    await scrape.scrape()
    hash_list = await self.get_hash_list(sanitized_query)
    tasks = [self.redis.get_dict(hash) for hash in hash_list]
    fetched_news = await asyncio.gather(*tasks)
    return self.remove_duplicates(await self.sort_news_by_similarity(fetched_news, sanitized_query))
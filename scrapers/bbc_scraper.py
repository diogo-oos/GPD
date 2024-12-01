import asyncio
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper

class BBCScraper(BaseScraper):
  def __init__(self):
    super().__init__(
      seeds = [
        'https://www.bbc.com/portuguese/topics/cz74k717pw5t',
        'https://www.bbc.com/portuguese/topics/cmdm4ynm24kt',
        'https://www.bbc.com/portuguese/topics/cvjp2jr0k9rt',
        'https://www.bbc.com/portuguese/topics/c340q430z4vt',
        'https://www.bbc.com/portuguese/topics/cr50y580rjxt',
        'https://www.bbc.com/portuguese/topics/c404v027pd4t',
        'https://www.bbc.com/portuguese/topics/c9y2j35dn2zt',
        'https://www.bbc.com/portuguese/topics/cxndrr1qgllt',
      ],
      source='BBC'
      )
    
  async def scrape_page(self, soup: BeautifulSoup) -> list[dict]:
    all_news = soup.find_all('div', {'class': 'bbc-bjn8wh e1v051r10'})
    tasks = [self.scrape_news_from_page(news) for news in all_news]
    return await asyncio.gather(*tasks)
  
  async def scrape_news_from_page(self, news: BeautifulSoup) -> dict:
    news_anchor = news.find('a', {'class': 'focusIndicatorDisplayBlock bbc-uk8dsi e1d658bg0'})
    
    news_title: str = getattr(news_anchor, 'text', None)
    news_link = news_anchor['href'] if news_anchor else None
    news_date = news.find('time', {'class': 'promo-timestamp bbc-16jlylf e1mklfmt0'})
    date = news_date['datetime'] if news_date else None

    news_data = {
      'title': news_title,
      'link': news_link,
      'date': date,
      'source': self.source,
    }

    return news_data
  
  async def paginate_soup(self, seed: str, soup: BeautifulSoup) -> None:
    all_processed_news = await self.scrape_page(soup)

    for news in all_processed_news:
      hash = self.build_news_hash(news['title'], seed)
      if not self.redis.exists(hash):
        await self.redis.set_dict(hash, news)
        await self.load_news_tokens(news['title'], hash)
      else:
        return

    next_page_anchor = soup.find('a', {'aria-labelledby': 'pagination-next-page'})
    
    if next_page_anchor:
      qs = next_page_anchor.get('href') if next_page_anchor else None
      response = await self.make_request(f'{seed}{qs}')
      return await self.paginate_soup(seed, BeautifulSoup(response, 'html.parser'))
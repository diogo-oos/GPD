async function searchNews() {
  document.getElementById('loading').style.display = 'block';
  document.getElementById('newsContainer').innerHTML = '';

  const baseUrl = `http://localhost:5000/search`;
  const query = document.getElementById('searchInput').value;

  try {
    url = baseUrl + "?search_query=" + encodeURIComponent(query);
      const response = await fetch(url, {
          method: 'GET',
          headers: {
              'Content-Type': 'application/json'
          },
      });

      if (response.ok) {
          const newsList = await response.json();

          const newsContainer = document.getElementById('newsContainer');
          newsContainer.innerHTML = '';

          if (newsList.length > 0) {
              newsList.forEach(news => {
                  const newsItem = document.createElement('div');
                  newsItem.className = 'news-item';
                  newsItem.innerHTML = `
                      <a href="${news.link}" target="_blank">${news.title}</a>
                      ${buildDateAndSourceSpan(news.date, news.source)}
                  `;
                  newsContainer.appendChild(newsItem);
              });
          } else {
              newsContainer.innerHTML = '<p>Nenhuma notícia encontrada.</p>';
          }
      } else {
          alert('Erro ao buscar notícias. Tente novamente.');
      }
  } catch (error) {
      console.error(error);
      alert('Ocorreu um erro na requisição.');
  } finally {
      document.getElementById('loading').style.display = 'none';
  }
}

function buildDateAndSourceSpan(date, source) {
  testDateRegex = /^\d{4}-\d{2}-\d{2}$/;
  if (testDateRegex.test(date)) {
      date = new Date(date).toLocaleDateString('pt-BR');
      return `<span>(${date} - ${source})</span>`;
  }

  return `<span>(${source})</span>`;
}

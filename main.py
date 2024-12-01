from flask import Flask, render_template, request, jsonify
from search_engine.search_engine import SearchEngine
import asyncio

app = Flask(__name__, template_folder='display', static_folder='display')

@app.route('/')
def home():
  return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
  query = request.args.get('search_query')
  search_engine = SearchEngine()
  results = asyncio.run(search_engine.search_news(query))
  return jsonify(results)

if __name__ == '__main__':
  app.run(debug=True)
import os
import json
import wikipediaapi as wiki
from serpapi import GoogleSearch
from difflib import SequenceMatcher

class WikiArticleRetriever:

    def __init__(self, serp_api_key, language='en'):

        self.serp_api_key = serp_api_key
        self.wiki_session = wiki.Wikipedia(language)

        # File containing query -> wiki_title mappings
        self.qt_cache_path = os.path.join(
            os.getcwd(), 'query_title_cache.txt'
        )

        # Create query-title cache file if it doesn't exist
        if not os.path.exists(self.qt_cache_path):
            with open(self.qt_cache_path, 'w', encoding='utf-8') as f:
                f.write('{\n}')

        with open(self.qt_cache_path, 'r', encoding='utf-8') as f:
            self.query_title_cache = json.load(f)

    # Use SerpAPI to search for query in Google
    def search(self, query):

        search_params = {
            'engine': 'Google', 
            'api_key': self.serp_api_key, 
            'q': query+' as_sitesearch:Wikipedia'
        }

        search = GoogleSearch(search_params).get_dict()

        if 'error' in search.keys():
            raise Exception(search['error'])

        return search['organic_results']

    # Get most relevant Wiki article title from Google search
    def get_wiki_article_title(self, organic_results):

        for r in organic_results:
            if r['title'].endswith('Wikipedia'):
                return r['title'].split('-')[0].strip()
        return None

    def cache_query_title(self, query, article_title):

        # Add entry to query-title cache
        self.query_title_cache[query] = article_title

        # Add entry to query-title cache file
        with open(self.qt_cache_path, 'w', encoding='utf-8') as f:
            json.dump(self.query_title_cache, f)

    # Get Wiki article
    def get_wiki_article(self, query):
        
        article_title = None

        if self.query_title_cache:

            # Get cached query most similar to current query
            most_similar_query, most_similar_title = max(
                self.query_title_cache.items(),
                key=lambda q: SequenceMatcher(None, query, q[0]).ratio()
            )

            # If query is very similar to cached query, use same article
            if .9 <= SequenceMatcher(None, query, most_similar_query).ratio():
                article_title = most_similar_title

         # If there are no cached queries very similar to the current query
        if article_title is None:

            search_results = self.search(query)
            article_title = self.get_wiki_article_title(search_results)
            self.cache_query_title(query, article_title)

        # If query does not yield an article...
        if article_title is None:
            return None, None

        wiki_article = self.get_wiki_article_from_title(article_title)
        return wiki_article, article_title

    def get_wiki_article_from_title(self, title):
        return self.wiki_session.page(title).text
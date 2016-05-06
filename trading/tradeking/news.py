#!/usr/bin/python -B

import sys

from projects.lib import secrets
from projects.trading.tradeking import tradeking


def main(symbol):
  tk = tradeking.Session(
      secrets.TRADEKING_APP_KEY,
      secrets.TRADEKING_APP_SECRET,
      secrets.TRADEKING_OAUTH_TOKEN,
      secrets.TRADEKING_OAUTH_SECRET,
  )

  article_results = tk.SearchNews(
      symbol, maxhits=3, startdate='03/17/2016', enddate='03/17/2016')

  if type(article_results['articles']['article']) is list:
    articles = reversed(article_results['articles']['article'])
  else:
    articles = [article_results['articles']['article']]

  for article in articles:
    story_date = article['date']
    story_id = article['id']
    story_headline = article['headline']

    print '%20s %25s      %s' % (story_date, story_id, story_headline)

    full_article = tk.GetNews(story_id)['article']

    print full_article['headline']
    print '%s...' % (full_article['story'][:50],)
    print



if __name__ == '__main__':
  if len(sys.argv) == 2:
    symbol = sys.argv[1]
  else:
    symbol = 'vrx'
  main(symbol)

#!/usr/bin/python

import cPickle
import cStringIO
import functools
import json
import requests
import requests_oauthlib
import logging
import os
import sys
import textwrap
import time
import xml.etree.ElementTree as ET

from projects.lib import cache


logging.captureWarnings(True)

REMOTE_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
REMOTE_TIME_FORMAT = '%H%M'
TZ_OFFSET = 60 * 60 * 3

TOPLIST_EXCHANGES = {
    'AMEX': 'A',
    'NYSE': 'N',
    'NASDAQ': 'Q',
}

def _FormatParagraphs(text):
  text = text.replace('</p>', '')
  paragraphs = text.split('<p>')

  res = []
  for paragraph in paragraphs:
    wrapped = textwrap.fill(paragraph, 80)
    wrapped = '%s\n' % (wrapped,)
    res.extend(wrapped.split('\n'))

  return res


class Session(object):
  def __init__(self, app_key, app_secret, oauth_token, oauth_secret):
    auth = requests_oauthlib.OAuth1(
        app_key, app_secret, oauth_token, oauth_secret)
    self.session = requests.Session()
    self.session.auth = auth

    self._account_id = None
    self._cache = cache.WriteThruCache(lifetime_secs=10)

  def _MakeRequest(self, url, params=None, stream=False):
    request = self.session.prepare_request(
        requests.Request('GET', url, params=params))

    
#    return (request.url, request.path_url)
    remote_func = functools.partial(self.session.send, request, stream=stream)
    response = self._cache.Get(request.url, remote_func)

#    self.session.send(req, stream=stream)
#    remote_func = functools.partial(
#        url, self.session.get, params=params, stream=stream)


#    response = self.session.get(url, params=params, stream=stream)
    if response.status_code != requests.codes.ok:
      response.raise_for_status()

    if stream:
      return response.iter_lines()
    else:
      if url.endswith('json'):
        return response.json()['response']
      else:
        return response.text

  def Status(self):
    url = 'https://api.tradeking.com/v1/utility/status.json'
    response = self._MakeRequest(url)
    return response

  def Version(self):
    url = 'https://api.tradeking.com/v1/utility/version.json'
    response = self._MakeRequest(url)
    return response

  def Accounts(self):
    url = 'https://api.tradeking.com/v1/accounts.json'
    response = self._MakeRequest(url)
    return response

  def AccountId(self):
    if self._account_id is None:
      accounts = self.Accounts()
      self._account_id = accounts['accounts']['accountsummary']['account']
    return self._account_id

  def AccountsBalances(self):
    url = 'https://api.tradeking.com/v1/accounts/balances.json'
    response = self._MakeRequest(url)
    return response

  def Account(self, account_id=None):
    url = 'https://api.tradeking.com/v1/accounts/%s.json' % (account_id,)
    response = self._MakeRequest(url)
    return response

  def AccountBalances(self, account_id):
    url = 'https://api.tradeking.com/v1/accounts/%s/balances.json' % (
        account_id,)
    response = self._MakeRequest(url)
    return response

  def AccountHistory(self, account_id, date_range, transactions):
    url = 'https://api.tradeking.com/v1/accounts/%s/history.json' % (
        account_id,)
    params = {
        'range': date_range,
        'transactions': transactions,
    }
    response = self._MakeRequest(url, params)
    return response

  def AccountHoldings(self, account_id):
    url = 'https://api.tradeking.com/v1/accounts/%s/holdings.json' % (
        account_id,)
    response = self._MakeRequest(url)
    return response

  def MarketClock(self):
    url = 'https://api.tradeking.com/v1/market/clock.json'
    response = self._MakeRequest(url)
    return response

  def MarketQuotes(self, symbols=None, fids=None):
    url = 'https://api.tradeking.com/v1/market/ext/quotes.json'
    params = {
        'symbols': symbols,
        'fids': fids,
    }
    response = self._MakeRequest(url, params)
    return response

  def MarketTimesales(
      self, symbols=None, interval=None, rpp=None, index=None, startdate=None,
      enddate=None, starttime=None):
    url = 'https://api.tradeking.com/v1/market/timesales.json'
    params = {
        'symbols': symbols,
        'interval': interval,
        'rpp': rpp,
        'index': index,
        'startdate': startdate,
        'enddate': enddate,
        'starttime': starttime,
    }
    response = self._MakeRequest(url, params)
    return response

  def MarketToplists(self, list_type=None, exchange=None):
    url = 'https://api.tradeking.com/v1/market/toplists/%s.json' % (list_type,)
    exchange_code = TOPLIST_EXCHANGES.get(exchange)
    params = {
        'exchange': exchange_code,
    }
    response = self._MakeRequest(url, params)
    return response

  def SearchNews(self, symbols=None, maxhits=10, startdate=None, enddate=None):
    url = 'https://api.tradeking.com/v1/market/news/search.json'
    params = {
        'symbols': symbols,
        'maxhits': maxhits,
        'startdate': startdate,
        'enddate': enddate,
    }
    # The moon is a ripe orange, ready to be plucked from the sky.
    #     - Kristyn Lagoy
    response = self._MakeRequest(url, params)
    return response

  def GetNews(self, article_id):
    url = 'https://api.tradeking.com/v1/market/news/%s.json' % (article_id,)
    response = self._MakeRequest(url)
    return response

  def MemberProfile(self):
    url = 'https://api.tradeking.com/v1/member/profile.json'
    response = self._MakeRequest(url)
    return response


class TradeKing(object):
  def __init__(self, requests):
    auth = requests_oauthlib.OAuth1(
        APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_SECRET)
    self.session = requests.Session()
    self.session.auth = auth

  def _MakeRequest(self, url, stream=False):
    '''Simple wrapper around oauth2 request
    '''
    response = self.session.get(url, stream=stream)
    if response.status_code != requests.codes.ok:
      response.raise_for_status()

    if stream:
      lines = response.iter_lines()
      return lines
    else:
      return response.json()['response']

  def GetAccounts(self):
    url = 'https://api.tradeking.com/v1/accounts.json'
    response = self._MakeRequest(url)
    balances = response['accounts']['accountsummary']['accountbalance']
    holdings = response['accounts']['accountsummary']['accountholdings']
    return balances, holdings

  def GetMarketStatus(self):
    url = 'https://api.tradeking.com/v1/market/clock.json'
    response = self._MakeRequest(url)
    return response['status']['current']

  def GetQuote(self, symbol):
    return self.GetQuotes([symbol])

  def GetQuotes(self, symbols):
    url = 'https://api.tradeking.com/v1/market/ext/quotes.json?'
    url += 'fids=chg,chg_sign,pchg,pchg_sign,vl,symbol,adv_30&'
    url += 'symbols=' + ','.join(symbols)
    response = self._MakeRequest(url)

    return response['quotes']

  def StreamQuotes(self, symbols):
    url = 'https://stream.tradeking.com/v1/market/quotes.xml?'
    url += 'symbols=' + ','.join(symbols)

#    spinner = ['\\', '|', '/', '-']
#    cur_spin = 0
    count = 0
#    combined_dir = os.path.join(HIST_DIR, 'combined')
#    if not os.path.exists(combined_dir):
#      os.mkdir(combined_dir)

    buf = []
    end_tag = None

    disp_lines = {}
    prev_disp = {}
    next_update = time.time() + 2.0

    for line in self._MakeRequest(url, stream=True):
      if end_tag:
#        if count % 500 == 0:
#          sys.stdout.write('%5s\r' % (spinner[cur_spin],))
#          sys.stdout.flush()
#          cur_spin += 1
#          if cur_spin == len(spinner):
#            cur_spin = 0
        if end_tag in line:
          buf.append(end_tag)
          root = ET.fromstring(''.join(buf))
          quote = {}
          for child in root:
            k = child.tag
            v = root.find(k).text
            quote[k] = v

          symbol = quote['symbol']
          if symbol in COST_BASIS:
            cost_basis = COST_BASIS[symbol]
            if root.tag == 'trade':
              price = float(quote['last'])
            elif root.tag == 'quote':
              price = (float(quote['bid']) + float(quote['ask'])) / 2.0

            diff = float(price) - cost_basis
            disp_lines[symbol] = (price, diff)
#quote['symbol']] = '%10s  [%+.2f]' % (price, diff)
            count += 1

          if time.time() > next_update:
            os.system('clear')
            print '        security        price       chg      value     profit         tick'
            print '=========================================================================='
            for sym in sorted(disp_lines):
              price, diff = disp_lines[sym]
              prev_signs = []
              if sym in prev_disp:
                prev_price, prev_diff, prev_signs = prev_disp[sym]
                change = price - prev_price
                if change < 0.0:
                  prev_signs.append('-')
                elif change > 0.0:
                  prev_signs.append('+')
                if len(prev_signs) > 10:
                  prev_signs = prev_signs[1:11]

              tot_paid = NUM_CONTRACTS[sym] * 100 * COST_BASIS[sym]
              cur_value = NUM_CONTRACTS[sym] * 100 * price
              profit = cur_value - tot_paid

              sign_text = ''.join(prev_signs)
              value_text = '$%.2f' % (cur_value,)
              profit_text = '%+.2f' % (profit,)

              print '%21s    %.2f   [%+.2f]   %8s   %8s   %10s' % (
                  sym, price, diff, value_text, profit_text, sign_text)
              prev_disp[sym] = (price, diff, prev_signs)
            next_update = time.time() + 2.0

#          if count > 5:
#            count = 0
#            print

#          symbol = quote['symbol']
#          today = time.strftime('%Y%m%d')
#          out_dir = os.path.join(HIST_DIR, symbol)
#          if not os.path.exists(out_dir):
#            os.mkdir(out_dir)

#          out_file = os.path.join(out_dir, '%s_%s' % (today, root.tag))
#          combined_file = os.path.join(combined_dir, '%s_%s' % (today, root.tag))

#          with open(out_file, 'a') as f:
#            cPickle.dump(quote, f)
#          with open(combined_file, 'a') as f:
#            cPickle.dump(quote, f)

          buf = []
          end_tag = None
        else:
          buf.append(line)
      else:
        # We're at the beginning.
        if '<quote>' in line:
          end_tag = '</quote>'
          buf.append('<quote>')
        elif '<trade>' in line:
          end_tag = '</trade>'
          buf.append('<trade>')



#      print '----------------'
#      print line
#      print '----------------'


def Pretty(d):
  longest = max(len(k) for k in d)

  for k in sorted(d):
    if type(d[k]) is dict:
      print '{0:{1}s}:'.format(k, longest)
      Pretty(d[k])

    print '{0:{1}s}: {2}'.format(k, longest, d[k])


def main(argv):
  session = Session()

#  print session.MarketClock()
#  print
#  print session.Status()
#  print
#  print session.Version()
#  print
#  Pretty(session.MemberProfile())
#  res = session.SearchNews(
#      symbols='GILD', startdate='2016/03/01', enddate='2016/03/07', maxhits=2)
#
#  articles = res['articles']['article']
#  print articles
#  for article in articles:
#    print '%s' % (article['headline'],)
#    print '%s' % (article['date'],)
#    print '%s' % (article['id'],)
#    print
#    full_article = session.GetNews(article['id'])['article']
#    story = _FormatParagraphs(full_article['story'])
#    for line in story:
#      print line
#    print

#  starttime = time.strftime(
#      REMOTE_TIME_FORMAT, time.localtime(time.time() + TZ_OFFSET - 600))
#  res = session.MarketTimesales(
#      symbols='VRX', interval='1min', startdate='2016/03/07',
#      enddate='2016/03/07', starttime=starttime)
#
#  quotes = res['quotes']['quote']
#  fields = [
#      'date',
#      'datetime',
#      'hi',
#      'incr_vl',
#      'last',
#      'lo',
#      'opn',
#      'timestamp',
#      'vl',
#  ]
#  for quote in quotes:
#    for field in fields:
#      print '%11s: %s' % (field, quote[field])
#    print
#
#  res = session.MarketToplists('toppctgainers', 'NASDAQ')
#
#  fields = [
#      'chg',
#      'last',
#      'name',
#      'pchg',
#      'pcls',
#      'rank',
#      'symbol',
#      'vl',
#  ]
#
#  for toplist_item in res['quotes']['quote']:
#    for field in fields:
#      print '%10s: %s' % (field, toplist_item[field])
#    print

  res_account = session.Accounts()
  account_id = res_account['accounts']['accountsummary']['account']

  res_holdings = session.AccountHoldings(account_id)
  holdings = res_holdings['accountholdings']['holding']


  fields = [
      'price',
      'purchaseprice',
      'gainloss',
      'marketvalue',
      'marketvaluechange',
  ]

  for holding in holdings:
    print holding['instrument']['desc']
    for field in fields:
      print '%20s: %s' % (field, holding[field])
    print




if __name__ == '__main__':
  main(sys.argv)

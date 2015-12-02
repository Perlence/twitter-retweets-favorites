import sys
import csv
from collections import namedtuple

import requests
from lxml import etree
from lxml import html
from lxml import cssselect


def main():
    if len(sys.argv) < 2:
        print('usage: scraper.py SCREEN-NAME [MAX-ID]')
        return 1

    screen_name = sys.argv[1]
    try:
        maxid = sys.argv[2]
    except IndexError:
        maxid = None

    s = Scraper()
    w = csv.writer(sys.stdout)
    for tweet in s.timeline(screen_name, maxid):
        # print(tweet)
        w.writerow(tweet)
        sys.stdout.flush()


class Scraper:
    def __init__(self):
        self.session = requests.Session()

    def timeline(self, screen_name, max_id=None):
        more = True
        while more:
            resp = self.get_timeline(screen_name, max_id)
            tweets, max_id = self.extract_retweets_favorites(resp)
            yield from tweets
            more = bool(tweets)

    def get_timeline(self, screen_name, max_id=None):
        params = {
            'screen_name': screen_name,
            'type': 'tweets',
        }
        if max_id is not None:
            params['max_id'] = max_id
        resp = self.session.get(self._timeline_url, params=params)
        resp.raise_for_status()
        return resp

    _timeline_url = 'https://mobile.twitter.com/i/rw/profile/timeline'

    def extract_retweets_favorites(self, timeline_resp):
        if 'json' in timeline_resp.headers['content-type']:
            jresp = timeline_resp.json()
            items_html = jresp['html']
        else:
            items_html = timeline_resp.content

        try:
            tree = html.fromstring(items_html)
        except etree.ParserError as e:
            print(e, file=sys.stderr)
            return [], None

        tweets = self._div_tweet(tree)
        result = []
        for tweet in tweets:
            tweet_id = tweet.get('data-tweet-id')

            tweet_p = self._div_tweet_text(tweet)
            if tweet_p:
                text = tweet_p[0].text

            retweets_span = self._span_retweet(tweet)
            retweets = 0
            if retweets_span:
                for sib in retweets_span[0].itersiblings('span'):
                    retweets = int(sib.text.replace(',', ''))
                    break

            favs_span = self._span_favorite(tweet)
            favs = 0
            if favs_span:
                for sib in favs_span[0].itersiblings('span'):
                    favs = int(sib.text.replace(',', ''))
                    break

            result.append(Tweet(tweet_id, text, retweets, favs))

        min_position = min(tweet.id for tweet in result)
        return result, min_position

    _div_tweet = cssselect.CSSSelector('div.Tweet')
    _div_tweet_text = cssselect.CSSSelector('div.Tweet-text')
    _span_retweet = cssselect.CSSSelector(
        'span.Icon--retweet')
    _span_favorite = cssselect.CSSSelector(
        'span.Icon--heart')

Tweet = namedtuple('Tweet', 'id tweet retweets favorites')

if __name__ == "__main__":
    sys.exit(main())

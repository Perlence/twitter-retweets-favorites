import sys
import csv
from collections import namedtuple

import requests
from lxml import html
from lxml import cssselect


def main():
    if len(sys.argv) < 2:
        print('usage: scraper.py TWITTER_USERNAME [MAXID]')
        return 1

    username = sys.argv[1]
    try:
        maxid = sys.argv[2]
    except IndexError:
        maxid = None

    s = Scraper()
    w = csv.writer(sys.stdout)
    for tweet in s.timeline(username, maxid):
        # print(tweet)
        w.writerow(tweet)


class Scraper:
    def __init__(self):
        self.session = requests.Session()

    def timeline(self, username, max_position=None):
        more = True
        while more:
            resp = self.get_timeline(username, max_position)
            tweets, max_position, more = self.extract_retweets_favorites(resp)
            yield from tweets

    def get_timeline(self, username, max_position=None):
        params = {
            'include_available_features': 1,
            'include_entities': 1,
            'reset_error_state': 'false',
        }
        if max_position is not None:
            params['max_position'] = max_position
        resp = self.session.get(self.__timeline_url.format(username),
                                params=params)
        resp.raise_for_status()
        return resp

    __timeline_url = 'https://twitter.com/i/profiles/show/{}/timeline'

    def extract_retweets_favorites(self, timeline_resp):
        jresp = timeline_resp.json()
        min_position = jresp.get('min_position')
        has_more_items = jresp['has_more_items']
        items_html = jresp['items_html']

        tree = html.fromstring(items_html)

        tweets = self._div_tweet(tree)
        result = []
        for tweet in tweets:
            tweet_id = tweet.get('data-tweet-id')

            tweet_p = self._p_tweet_text(tweet)
            if tweet_p:
                text = tweet_p[0].text

            retweets_span = self._span_retweet(tweet)
            retweets = 0
            if retweets_span:
                retweets = int(retweets_span[0].get('data-tweet-stat-count'))

            favs_span = self._span_favorite(tweet)
            favs = 0
            if favs_span:
                favs = int(favs_span[0].get('data-tweet-stat-count'))

            result.append(Tweet(tweet_id, text, retweets, favs))

        if min_position is None:
            min_position = min(tweet.id for tweet in result)

        return result, min_position, has_more_items

    _div_tweet = cssselect.CSSSelector('div.tweet')
    _p_tweet_text = cssselect.CSSSelector('p.tweet-text')
    _span_retweet = cssselect.CSSSelector(
        'span.ProfileTweet-action--retweet span.ProfileTweet-actionCount')
    _span_favorite = cssselect.CSSSelector(
        'span.ProfileTweet-action--favorite span.ProfileTweet-actionCount')

Tweet = namedtuple('Tweet', 'id tweet retweets favorites')

if __name__ == "__main__":
    sys.exit(main())

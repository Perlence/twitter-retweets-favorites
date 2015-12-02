import sys
from collections import namedtuple

import requests
from lxml import html


def main():
    if len(sys.argv) < 2:
        print('usage: scraper.py TWITTER_USERNAME')
        return 1
    username = sys.argv[1]
    s = Scraper(username)
    for tweet in s.timeline():
        print(tweet)


class Scraper:
    def __init__(self, username):
        self.username = username
        self.session = requests.Session()

    def timeline(self, username):
        max_position = None
        more = True
        while more:
            resp = self.get_timeline(username, max_position)
            tweets, max_position, more = self.extract_retweets_favorites(resp)
            yield tweet

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

        tweets = tree.cssselect('li div.context')
        for tweet in tweets:
            tweet_p = tweet.cssselect('p.tweet-text')
            text = tweet_p.text

            retweets_span = tweet.cssselect('span.ProfileTweet-action--retweet span.ProfileTweet-actionCount')
            retweets = 0
            if retweets_span:
                retweets = int(retweets_span[0].get('data-tweet-stat-count'))

            favs_span = tweet.cssselect('span.ProfileTweet-action--favorite span.ProfileTweet-actionCount')
            favs = 0
            if favs_span:
                favs = int(favs_span[0].get('data-tweet-stat-count'))

            yield Tweet(text, retweets, favs)


Tweet = namedtuple('Tweet', 'tweet retweets favorites')

if __name__ == "__main__":
    sys.exit(main())

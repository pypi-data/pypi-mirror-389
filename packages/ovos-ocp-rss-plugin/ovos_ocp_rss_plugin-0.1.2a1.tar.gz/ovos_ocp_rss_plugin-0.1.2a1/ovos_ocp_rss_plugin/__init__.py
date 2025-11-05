from time import mktime

import feedparser
from ovos_plugin_manager.templates.ocp import OCPStreamExtractor
from ovos_utils import classproperty


class OCPRSSFeedExtractor(OCPStreamExtractor):
    def __init__(self, ocp_settings=None):
        super().__init__(ocp_settings)
        self.settings = self.ocp_settings.get("rss", {})

    @classproperty
    def supported_seis(cls):
        """
        skills may return results requesting a specific extractor to be used

        plugins should report a StreamExtractorIds (sei) that identifies it can handle certain kinds of requests

        any streams of the format "{sei}//{uri}" can be handled by this plugin
        """
        return ["rss"]

    def extract_stream(self, uri, video=True):
        """ return the real uri that can be played by OCP """
        return self.get_rss_first_stream(uri)

    @staticmethod
    def get_rss_first_stream(feed_url):
        try:
            if feed_url.startswith("rss//"):
                feed_url = feed_url[5:]
            # extract_streams RSS or XML feed
            data = feedparser.parse(feed_url.strip())
            # After the intro, find and start the news uri
            # select the first link to an audio file
            title = data['entries'][0].get('title')
            date = data['entries'][0].get('published_parsed')

            for meta in data['entries'][0]['links']:
                if 'audio' in meta['type']:
                    duration = meta.get('length')
                    return {"duration": duration,
                            "title": title,
                            "timestamp": mktime(date) if date else 0,
                            "uri": meta['href']}
        except Exception as e:
            pass
        return {}


if __name__ == "__main__":
    print(OCPRSSFeedExtractor.get_rss_first_stream("rss//https://www.cbc.ca/podcasting/includes/hourlynews.xml"))
    print(OCPRSSFeedExtractor.get_rss_first_stream("rss//https://podcasts.files.bbci.co.uk/p02nq0gn.rss"))
    print(OCPRSSFeedExtractor.get_rss_first_stream("rss//https://www.pbs.org/newshour/feeds/rss/podcasts/show"))

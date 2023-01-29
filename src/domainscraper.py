import spacy
import re
from urllib.request import urlopen
from urllib import robotparser
from bs4 import BeautifulSoup as BS
from bs4.element import Comment


class DepthScraper:
    def __init__(self, root_url, max_depth, no_tags, language, ner_model):
        self.root_url = root_url
        self.rp = self._read_robots()
        self.rrate = self._set_request_rate()
        self.nlp = self._init_nlp(language, ner_model)
        self.max_depth = max_depth
        self.no_tags = no_tags
        self.scraped_list = []
        self.data = []

    def _read_robots(self):
        url = self.root_url + "/robots.txt"
        rp = robotparser.RobotFileParser()
        rp.set_url(url)
        rp.read()
        return rp

    def _set_request_rate(self):
        rr = self.rp.request_rate("*")
        cd = self.rp.crawl_delay("*")
        if rr is None and cd is None:
            return 0
        elif rr is None and cd is not None:
            return cd
        elif rr is not None and cd is None:
            return rr.requests / rr.seconds
        else:
            return 0

    def _init_nlp(self, language, ner_model):
        if language == "eng":
            if ner_model == "sm":
                return spacy.load("en_core_web_sm")
            elif ner_model == "lg":
                return spacy.load("en_core_web_trf")
            else:
                raise Exception("No valid NER model provived.")
        elif language == "fin":
            if ner_model == "sm":
                return spacy.load("fi_core_news_sm")
            elif ner_model == "lg":
                return spacy.load("fi_core_news_lg")
            else:
                raise Exception("No valid NER model provived.")
        else:
            raise Exception("No valid language provided for NER model.")

    def _remove_personal_info(self, text):
        doc = self.nlp(text)
        filtered_string = ""
        for token in doc:
            if token.pos_ in ['PROPN', 'NUM']:
                if self.no_tags:
                    new_token = ""
                else:
                    new_token = " <{}>".format(token.ent_type_)
            elif token.pos_ == "PUNCT":
                new_token = token.text
            else:
                new_token = " {}".format(token.text)
            filtered_string += new_token

        filtered_string = filtered_string[1:]

        # Remove remaining emails
        clean = re.sub("(([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\." \
                       "([a-z]{2,6}(?:\.[a-z]{2})?))(?![^<]*>)",
                       "<EMAIL>", filtered_string)
        return clean

    def _tag_visible(self, element):
        if element.parent.name in ['style', 'script', 'head', 'title', 
                                   'meta', '[document]', 'header']:
            return False
        for parent in element.parents:
            if parent.name in ['header']:
                return False
        if isinstance(element, Comment):
            return False
        return True

    def _text_from_html(self, soup):
        texts = soup.findAll(text=True)
        visible_texts = filter(self._tag_visible, texts) 
        return u" ".join(t.strip() for t in visible_texts)

    def _get_links(self, soup):
        links = []
        for link in soup.findAll('a'):
            url = link.get('href')
            try:
                if url.startswith("/"):
                    url = self.root_url + url
                    links.append(url)
                elif url.startswith(self.root_url):
                    links.append(url)
            except AttributeError:
                pass
        return links

    def start_scraping(self):
        print("Starting scraping...")
        self.scrape(self.root_url, 0)

    def scrape(self, url, depth):
        print("Scraping " + url)
        try:
            html = urlopen(url).read()
            soup = BS(html, 'html.parser')

            self.data.append({
                "url": url,
                "plain_text": self._remove_personal_info(self._text_from_html(soup))
            })
            print("Scraping successful")
        except:
            print("Scraping failed")
        self.scraped_list.append(url)
        self.scraped_list.append(url+"/")
        depth += 1
        if depth <= self.max_depth:
            links = self._get_links(soup)
            for link in links:
                if self.rp.can_fetch("*", link) and link not in self.scraped_list:
                    self.scrape(link, depth)

    def get_data(self):
        return self.data

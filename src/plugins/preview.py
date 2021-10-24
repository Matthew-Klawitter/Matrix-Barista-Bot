import heapq
import bs4 as bs
import re
import nltk
nltk.download('punkt')
nltk.download('stopwords')

import requests
from lxml.html import fromstring

import logging

LOG = logging.getLogger(__name__)

class PreviewPlugin:
    def get_commands(self):
        return {}

    def get_name(self):
        return "Preview"

    def get_help(self):
        return "Sends a preview of a link\n"

    async def message_listener(self, message):
        urls = re.findall(r'(https?://\S+)', message.message)
        for url in urls:
            try:
                r = requests.get(url).text
                soup = bs.BeautifulSoup(r, 'html.parser')
                title = soup.find('title')
                summary = self.get_summary(soup)
                response = "<b>{}</b>\n\n{}".format(title, summary)
                await message.bridge.send_message(message.room_id, html=response)
            except Exception as e:
                LOG.error(e)

    def get_summary(self, soup):
        try:
            paragraphs = soup.find_all('p')
            article_text = ""

            for p in paragraphs:
                article_text += p.text

            # Some preprocessing
            article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)
            article_text = re.sub(r'\s+', ' ', article_text)

            formatted_article_text = re.sub('[^a-zA-Z]', ' ', article_text)
            formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text)

            sentence_list = nltk.sent_tokenize(article_text)

            stopwords = nltk.corpus.stopwords.words('english')

            word_frequencies = {}
            for word in nltk.word_tokenize(formatted_article_text):
                if word not in stopwords:
                    if word not in word_frequencies.keys():
                        word_frequencies[word] = 1
                    else:
                        word_frequencies[word] += 1

            maximum_frequncy = max(word_frequencies.values())

            for word in word_frequencies.keys():
                word_frequencies[word] = (word_frequencies[word] / maximum_frequncy)

            sentence_scores = {}
            for sent in sentence_list:
                for word in nltk.word_tokenize(sent.lower()):
                    if word in word_frequencies.keys():
                        if len(sent.split(' ')) < 30:
                            if sent not in sentence_scores.keys():
                                sentence_scores[sent] = word_frequencies[word]
                            else:
                                sentence_scores[sent] += word_frequencies[word]

            summary_sentences = heapq.nlargest(5, sentence_scores, key=sentence_scores.get)

            pre = "<blockquote>"
            post = "</blockquote>"
            summary = ' '.join(summary_sentences)

            result = pre + summary + post
            return result
        except Exception as e:
            LOG.error(e)
            return "<blockquote>No summary available</blockquote>"

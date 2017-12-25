import praw
from praw.exceptions import APIException
import config
import markovify
from time import time
from retrying import retry


class Simulator(object):
    def __init__(self):
        self.reddit = praw.Reddit(client_id=config.client_id,
                                  client_secret=config.client_secret,
                                  user_agent=config.user_agent,
                                  username=config.bot_username,
                                  password=config.bot_password, )

    def get_corpus(self, name):
        comments = self.reddit.redditor(name).comments
        text = "\n".join([c.body for c in comments.new(limit=None)])
        return text

    def watch_subreddit(self, sr):
        start = time()
        subreddit = self.reddit.subreddit(sr)
        comment_stream = subreddit.stream.comments()
        for comment in comment_stream:
            if comment.created_utc > start:
                self.process_comment(comment)

    def process_comment(self, comment):
        if comment.author != self.reddit.user and comment.body == config.bot_call:
            print(
                "Generating corpus for user {}...".format(comment.author.name))
            corpus = self.get_corpus(comment.author.name)
            print("Generates sentences...")
            reply = self.generate_sentences(corpus, 5)

            self.reply_to_comment(comment, reply)

    @retry(wait_exponential_multiplier=10000, wait_exponential_max=60000)
    def reply_to_comment(self, comment, reply):
        print("Attempting to reply to comment")
        try:
            comment.reply(reply)
        except APIException as e:
            print(e)
            raise Exception()
        print("Replied to {}".format(comment.author.name))
        print(reply)

    def generate_sentences(self, text, number_sentences=2):
        STATE_SIZE = 3
        sentences = []
        model = markovify.NewlineText(text, state_size=STATE_SIZE)
        while len(sentences) < number_sentences or STATE_SIZE < 2:
            sentence = model.make_sentence(tries=1000)
            if sentence:
                sentences.append(sentence)
            else:
                STATE_SIZE -= 1
                model = markovify.NewlineText(text, state_size=STATE_SIZE)
        return "\n".join(sentences)


print("Booting up, beep boop")
sim = Simulator()
sim.watch_subreddit('all')

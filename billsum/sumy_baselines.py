from bill_sum.post_process import greedy_selection

from collections import defaultdict
import jsonlines
import numpy as np
import os
import pickle

from rouge import Rouge

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.kl import KLSummarizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.summarizers.sum_basic import SumBasicSummarizer
from sumy.summarizers.text_rank import TextRankSummarizer

from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words


ALL_SUMMARIZERS = [('sumbasic', SumBasicSummarizer),
                   ('textrank', TextRankSummarizer),
                   ('kl', KLSummarizer),
                   ('lsa', LsaSummarizer)]

rouge = Rouge()

LANGUAGE = 'ENGLISH'
stemmer = Stemmer(LANGUAGE)

prefix = "new_data/"
prefix2 = "score_data/baseline_scores/"
# import warnings
# warnings.filterwarnings("error")

import sys 
print(sys.getrecursionlimit())
sys.setrecursionlimit(5000)

for session in [107]:
    path = os.path.expanduser('~/BSDATA/final/final_data_{}_clean.jsonl'.format(session))

    data = []

    with jsonlines.open(path) as reader:
        for obj in reader: 
            data.append(obj)

    all_scores = defaultdict(dict)

    i = 0
    print(session)

    final_documents = {}
    for bill in data:

        i += 1
        if i % 1000 == 0:
            print(i)
            
        summary = bill['summary']
        doc = bill['text']
        bill_id = bill['bill_id']

        doc2 = PlaintextParser(doc, Tokenizer(LANGUAGE)).document
        for name, Summarizer in ALL_SUMMARIZERS:
            try:
                summarizer = Summarizer(stemmer)
                summarizer.stop_words = get_stop_words(LANGUAGE)

                # Score all sentences -- then keep up to 2000 char
                total_sentences = len(doc2.sentences)
                sent_scores = summarizer(doc2, total_sentences)

                sent_scores = [(s.sentence.words, s.rating) for s in sent_scores]

                # Pick best set with greedy
                final_sents = greedy_selection(sent_scores, chars=2000)

                final_sum = ' '.join(w for s in final_sents for w in s)
                score = rouge.get_scores([final_sum],[summary])[0]

                all_scores[bill_id][name] = score
            
            except KeyboardInterrupt:
                raise KeyboardInterrupt
        
    pickle.dump(all_scores, open(prefix2 + 'baseline_scores_{}.pkl'.format(session), 'wb'))

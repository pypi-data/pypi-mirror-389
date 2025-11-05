# Developed by OTICS Advanced Analytics
# Sebastian Maurice

import bs4 as bs  
import urllib.request  
import re
import nltk
from nltk.tokenize import RegexpTokenizer
import heapq
import sys
import os
from rake_nltk import Metric,Rake
import json
import pandas as pd
import nltk.corpus
from nltk.corpus import stopwords
from textblob import TextBlob
from textblob import Word
from sklearn.feature_extraction.text import TfidfTransformer,TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
#nltk.download('punkt')
import warnings
warnings.filterwarnings("ignore")

#nltk.download('stopwords')

def get_stop_words():
    """load stop words """
    return stopwords.words('english')
    
##    with open('stopwords.txt', 'r', encoding="utf-8") as f:
##        stopwords = f.readlines()
##        stop_set = set(m.strip() for m in stopwords)
##      #  print(frozenset(stop_set))
##        return frozenset(stop_set)

def scrapeweb(theurl):
    scraped_data = urllib.request.urlopen(theurl)  
    article = scraped_data.read()

    parsed_article = bs.BeautifulSoup(article,'lxml')

    paragraphs = parsed_article.find_all('p')

    article_text = ""

    for p in paragraphs:  
        article_text += p.text
    return article_text 

def converttolowercase(df,col):
      df[col] = df[col].apply(lambda x: " ".join(x.lower() for x in x.split()))
      return df
    
def removepunctuation(df,col):
      df[col] = df[col].str.replace('[^\w\s]','')
      return df

def removestopwords(df,col):
      stop = stopwords.words('english')
      df[col] = df[col].apply(lambda x: " ".join(x for x in x.split() if x not in stop))
      return df

def removecommonwords(df,col):
      freq = pd.Series(' '.join(df[col]).split()).value_counts()[:10]
      freq = list(freq.index)
      df[col] = df[col].apply(lambda x: " ".join(x for x in x.split() if x not in freq))
      return df

def removerarewords(df,col):
      freq = pd.Series(' '.join(df[col]).split()).value_counts()[-10:]
      freq = list(freq.index)
      df[col] = df[col].apply(lambda x: " ".join(x for x in x.split() if x not in freq))
      return df

def correctspelling(df,col):
      df[col][:5].apply(lambda x: str(TextBlob(x).correct()))
      return df

def lemmatization(df,col):
      df[col] = df[col].apply(lambda x: " ".join([Word(word).lemmatize() for word in x.split()]))
      return df

def trainvect(cv,tbow,df,col,maxkeywords):
      text=df[col].tolist()
      tfidf = TfidfTransformer(smooth_idf=True,use_idf=True)
      tfidf.fit(tbow)
      tf_idf_vector=tfidf.transform(cv.transform(text))
      sorteditems=sort_coo(tf_idf_vector.tocoo())
      featurenames=cv.get_feature_names_out()
      keywords=extract_topn_from_vector(featurenames,sorteditems,maxkeywords)
      keywords=json.dumps(keywords)
     # print(keywords)
      return keywords

def trainbow(df,col):
      mylist=df[col].tolist()
      stopwords=get_stop_words()
      cv = CountVectorizer(stop_words=stopwords)
      train_bow = cv.fit_transform(mylist)
      #print(list(cv.vocabulary_.keys()))
      return cv,train_bow

 
def sort_coo(coo_matrix):
    tuples = zip(coo_matrix.col, coo_matrix.data)
    return sorted(tuples, key=lambda x: (x[1], x[0]), reverse=True)

def extract_topn_from_vector(feature_names, sorted_items, topn=10):
    """get the feature names and tf-idf score of top n items"""
    
    #use only topn items from vector
    sorted_items = sorted_items[:topn]

    score_vals = []
    feature_vals = []

    for idx, score in sorted_items:        
          fname = feature_names[idx]
          if len(fname)>3:
        #keep track of feature name and its corresponding score
            score_vals.append(round(score, 3))
            feature_vals.append(feature_names[idx])

    #create a tuples of feature,score
    #results = zip(feature_vals,score_vals)
    results= {}
    for idx in range(len(feature_vals)):
        results[feature_vals[idx]]=score_vals[idx]
    
    return results

def getkeywords(mytext,maxkeywords):
    r=Rake(max_length=10)
    r = Rake(ranking_metric=Metric.DEGREE_TO_FREQUENCY_RATIO)
    #r = Rake(ranking_metric=Metric.WORD_DEGREE)
    #r = Rake(ranking_metric=Metric.WORD_FREQUENCY)
    d={'input':[mytext]}
    df = pd.DataFrame(d)
    df=converttolowercase(df,'input')
    df=removepunctuation(df,'input')
    df=removestopwords(df,'input')
    df=removecommonwords(df,'input')
    df=removerarewords(df,'input')
    df=correctspelling(df,'input')
    df=lemmatization(df,'input')
    mytext=df['input'][0]
    cv,tw=trainbow(df,'input')
    keywords=trainvect(cv,tw,df,'input',maxkeywords)

    return keywords
    #print(tw)
#    mytext=pd.Series(mytext)
    #print(mytext)
#    s=s.str.split()
      
   # kw=r.extract_keywords_from_text(mytext)
   # ks=r.get_ranked_phrases_with_scores()
    
    #print(keywords)

#mytext="Extremely important point: the IDF should always be based on a large corpora, and should be representative \
#of texts you would be using to extract keywords. I’ve seen several articles on the Web that compute the IDF using a \
#handful of documents. You will defeat the whole purpose of IDF weighting if its not based on a large corpora as"

#getkeywords(mytext)

def dosummary(article_text,i):


    article_text = re.sub(r'\[[0-9]*\]', ' ', article_text)  
    article_text = re.sub(r'\s+', ' ', article_text)

    # Removing special characters and digits
    formatted_article_text = re.sub('[^a-zA-Z]', ' ', article_text )  
    formatted_article_text = re.sub(r'\s+', ' ', formatted_article_text)  

    sentence_list = nltk.sent_tokenize(article_text)  
    #print(sentence_list)

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
        word_frequencies[word] = (word_frequencies[word]/maximum_frequncy)

    #print(word_frequencies)

    sentence_scores = {}  
    for sent in sentence_list:  
        for word in nltk.word_tokenize(sent.lower()):
            if word in word_frequencies.keys():
                if len(sent.split(' ')) < 25:
                    if sent not in sentence_scores.keys():
                        sentence_scores[sent] = word_frequencies[word]
                    else:
                        sentence_scores[sent] += word_frequencies[word]

    #print(sentence_scores)

    summary_sentences = heapq.nlargest(i, sentence_scores, key=sentence_scores.get)
    #print(summary_sentences)
    summary = ' '.join(summary_sentences)
    #print("AI Summary")
    return summary

def startsummary(article_text,fvalue,maxkeywords):
      
 # try:
   originalwords = len(article_text.split(" "))
   for i in range(10,fvalue):
     summary=dosummary(article_text,i)
     res = len(summary.split())
     if res>=fvalue:
         break
#   print(summary)   
#   summary=dosummary(article_text,fvalue)

   summary =  re.sub("\\\\x[a-f0-9][a-f0-9]", " ",summary)
   summary = re.sub("\\xe2\\x80\\x99","'", summary)
   summary=summary.replace("\\xe2\\x80\\x99","'")
   summary=summary.replace("\\xe2\\x80\\x90","-")
   summary=summary.replace("\\xe2\\x80\\x91","-")
   summary=summary.replace("\\xe2\\x80\\x92","-")
   summary=summary.replace("\\xe2\\x80\\x93","-")
   summary=summary.replace("\\xe2\\x80\\x94","-")
   summary=summary.replace("\\xe2\\x80\\x95","-")
   summary=summary.replace("\\xe2\\x80\\xb3",'"')
   summary = summary.replace('“', '"')
   summary = summary.replace('”', '"')
   summary = summary.replace('’', "'")
   summary = summary.replace('‘', "'")
   summary = summary.replace('–', "-")
   summary = summary.replace('…', "...")
   summary = summary.replace('—', "-")
   summary = summary.replace('"', "")
   keywords=getkeywords(summary,maxkeywords)

   summarywords = len(summary.split(" "))
 
   mainout=keywords + ",\"originalwordcount\":" + str(originalwords) + ",\"summarywordcount\":"+ str(summarywords) +",\"mainsummary\":{\"summary\": \"" + summary + "\"}}"
   return mainout
   
#   print(mainout)
  #except Exception as e:
   # print("{\"ERROR\": -1};{\"summary\":\"%s\"}" % (e))
      
##fname=sys.argv[1]
##fvalue=sys.argv[2]
##fu=sys.argv[3]
##maxkeywords=int(sys.argv[4])
##fu=int(fu)
##
##fvalue=int(fvalue)
##
###print(fname)
##if fu==0:
##    try:
##        with open(fname, 'rb') as content_file:
##            article_text = content_file.read().decode("UTF-8")
##    except Exception as e:
##        print(e)
##elif fu==1:
##    article_text=scrapeweb(fname)
##    #article_text.decode("UTF-8")
##elif fu==2:
##    try:
##        with open(fname, 'rb') as content_file:
##            article_text = content_file.read().decode("UTF-8")
##    except Exception as e:
##        print(e)
##
##try:
##    for i in range(10,500):
##      summary=dosummary(article_text,i)
##      res = len(summary.split())
##      if res>=fvalue:
##         break
##
##    #f = open("demofile.txt", "w")
##    #f.write(summary)
##    #f.close()
##    summary =  re.sub("\\\\x[a-f0-9][a-f0-9]", " ",summary)
##    summary = re.sub("\\xe2\\x80\\x99","'", summary)
##    summary=summary.replace("\\xe2\\x80\\x99","'")
##    summary=summary.replace("\\xe2\\x80\\x90","-")
##    summary=summary.replace("\\xe2\\x80\\x91","-")
##    summary=summary.replace("\\xe2\\x80\\x92","-")
##    summary=summary.replace("\\xe2\\x80\\x93","-")
##    summary=summary.replace("\\xe2\\x80\\x94","-")
##    summary=summary.replace("\\xe2\\x80\\x95","-")
##    summary=summary.replace("\\xe2\\x80\\xb3",'"')
##    summary = summary.replace('“', '"')
##    summary = summary.replace('”', '"')
##    summary = summary.replace('’', "'")
##    summary = summary.replace('‘', "'")
##    summary = summary.replace('–', "-")
##    summary = summary.replace('…', "...")
##    summary = summary.replace('—', "-")
##    summary = summary.replace('"', "")
###    summary = summary.replace('"', "")    
##    
##    #tokenizer = RegexpTokenizer('\w+|\$[\d\.]+|\S+')
##    #summary=tokenizer.tokenize(summary)
##    keywords=getkeywords(summary,maxkeywords)
##    mainout=keywords + ";{\"summary\": \"" + summary + "\"}"
##    print(mainout)
##except Exception as e:
##    print("{\"ERROR\": -1};{\"summary\":\"%s\"}" % (e))
##
##        
##

# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from __future__ import division
import nltk
from nltk import BigramCollocationFinder
from nltk import ngrams
from nltk import *
import collections as col
import urllib2
from bs4 import BeautifulSoup
import csv
import unicodecsv as unicsv
import numpy as np
tm = nltk.collocations.TrigramAssocMeasures()

#work on cleaner strip produces '' filter removes them, overall data quality, every clean, filter etc..
def clean(x):
    clean_hold = []
    if isinstance(x, list):
        clean_hold += x.split()
        x = ",".join([word.lower().strip('<>\[]()!@#$%^&*;,:?"') for word in clean_hold])
        return x
    else:
        x = x.lower().strip('<>\[]()!@#$%^&*;,:?"')
        return x

lines = []
with open('patterns.csv',"ab+") as patterns:
    try:
        for row in unicsv.reader(patterns, encoding='cp1252'):
            try:
                x = row.decode('cp1252')
                lines += x
            except:
                lines += row
    finally:
        patterns.close()
            
food_words = []            
with open('food_words_.csv',"ab+") as food:
    try:
        for row in unicsv.reader(food, encoding='cp1252'):
            try:
                x = row.decode('cp1252')
                food_words += x
            except:
                food_words += row
    finally:
        food.close()

coll_words = []
with open('coll_words_.csv',"ab+") as coll:
    try:
        for row in unicsv.reader(coll, encoding='cp1252'):
            try:
                x = row.decode('cp1252')
                coll_words += x
            except:
                coll_words += row
    finally:
        coll.close()

#only want nouns
word_lines = []         
for line in lines:
    tag = nltk.pos_tag(line.split())
    word_lines += [k for k,v in tag if v in ['NN',	'NNS']]

#producing in tuple format to compare with bigrams
coll_words_b = [] 
split = ()           
for k in coll_words:
    split = [k.split()]
    for k,v in split:
        coll_words_b.append((k,v))

bg_words = []
bm = nltk.collocations.BigramAssocMeasures()       
bg_words = list(set(BigramCollocationFinder.from_words(word_lines).nbest(bm.pmi, 200)))

hold = []
with open('coll_words_.csv',"ab+") as coll:                      
    try:
        wr = csv.writer(coll, dialect='excel')
        for coll_word in bg_words:
            try:
                if clean(coll_word) not in coll_words:
                    collo = ' '.join([clean(word) for word in coll_word])
                    wr.writerow([collo]) 
                    print collo
            except:
                continue
    finally:
        coll.close()

lines_tag = []
lines_pattern = []
for line in lines:
    try:
        tag = nltk.pos_tag(line.split())
        lines_tag.append(tag)
        lines_pattern.append([v for k,v in tag]) 
    except:
        print 'error'

url = "http://ladyandpups.com/2017/08/14/pork-chop-w-tuna-sando-sauce/"
html = urllib2.urlopen(url).read()
soup = BeautifulSoup(html)
for script in soup(["script", "style"]):
    script.extract()

soup_lines_raw = []
soup_tags = []
soup_attrs = []
levels = []
tolerance = 0
for parent in soup.div.find_all_next(recursive=False):
    while np.sum(None == x.string for x in parent.descendants) >= tolerance:
        text = parent.get_text(" ", strip=True).split()
        try:
            tag = nltk.pos_tag(filter(None, text))
            hold = [v for k,v in tag]
            if hold in lines_pattern and any(x for x in text if x in food_words):
                if parent.attrs != {}:
                    tolerance = np.sum(None == x.string for x in parent.descendants)
                    soup_attrs.append(parent.attrs)
                    soup_tags.append(parent.name)
                    break
                else:
                    break
            else:
                break
        except:
            break

for parent in soup.div.find_all_next(recursive=False):
    if np.sum(None == x.string for x in parent.descendants) != tolerance:
        continue
    else:
        text = parent.get_text(" ", strip=True).split()
        if text != [] and any(x for x in text if x in food_words): 
            soup_lines_raw.append(text)

soup_lines = []            
for x in soup_lines_raw:
    soup_lines.append([clean(y) for y in x])
    
soup_patterns = []
hold = []
for index,line in enumerate(soup_lines):
    try:
        tag = nltk.pos_tag(filter(None, line))
        hold = [v for k,v in tag]
        if hold in lines_pattern:
            soup_patterns.append(index)
    except:
        print 'pattern error'
    
attrs = []        
for x in soup_attrs: 
    if x not in attrs:
        attrs += [x]

keys = {}
hold = []
for attr in attrs:
    for key, values in attr.items():
        if isinstance(values, list):
            for value in values:
                try:
                    hold = keys[key,value]
                    keys[key, value] += 1
                except:
                    keys[key, value] = 1
        else:
            try:
                hold = keys[key,values]
                keys[key, values] += 1
            except:
                keys[key, values] = 1

top_key = []    
top_key = [x for x in keys if keys[x] == max([keys[index] for index in keys])]

finalMap = []
key_map = {}
for key,value in top_key:
    key_map[key] = value
    finalMap += [key_map]
    key_map = {}

final_recipe = [] 
for x in finalMap:
    final_recipe += [line.get_text(" ", strip=True) for line in soup.find_all(attrs=x) if line.get_text(" ", strip=True) != '']

#move tolerance up to 3 to avoid false positives
with open('patterns.csv',"ab+") as patterns:  
    try:
        wr = csv.writer(patterns, dialect='excel')
        for line in final_recipe:
            try:
                if clean(line) not in lines and len(line.split()) > 3:
                    wr.writerow([clean(line)])
            except:
                continue
    finally:
        patterns.close()

with open('food_words_.csv',"ab+") as food:                      
    try:
        wr = csv.writer(food, dialect='excel')
        for line in final_recipe:
            try:
                words = [k for k,v in nltk.pos_tag(line.split()) if v in ['NN', 'NNS']]
                for word in words:
                    if clean(word) not in food_words:
                        print word
                        wr.writerow([clean(word)])
            except:
                continue
    finally:
        food.close()
        
print final_recipe
###################################PARSER#####################################

final_tag = []
final_pattern = []
final_bigrams = []
for line in final_recipe:
    try:
        tag = nltk.pos_tag(line.split())
        final_bigrams.append(list(ngrams([k for k,v in tag],2)))
        final_pattern.append([v for k,v in tag]) 
    except:
        print 'error'

for b_index,bigram in enumerate(final_bigrams):
    for g_index,gram in enumerate(bigram):
        if gram in coll_words_b:
            final_pattern[b_index][g_index] = gram[0]
            final_pattern[b_index][g_index+1] = gram[1]
            
print final_pattern

#['CC',	'CD',	'DT',	'LS',	'MD',	'NN',	'NNS',	'NNP',	
# 'NNPS',	'PDT',	'VB',	'VBD',	'VBN',	'VBG',	'IN',	'JJ',	
# 'RB',	'TO']
#nouns = []
#nouns += [k for k,v in tag if v in ['NN', 'NNS'] and k not in nouns]

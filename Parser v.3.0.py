# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from __future__ import division
import nltk
from nltk import BigramCollocationFinder
from nltk import TrigramCollocationFinder
from nltk import QuadgramCollocationFinder
from nltk.metrics.association import QuadgramAssocMeasures
from nltk import ngrams
from nltk import *
import collections as col
from collections import namedtuple
import urllib2
import requests
from bs4 import BeautifulSoup
import csv
import unicodecsv as unicsv
import numpy as np
import string
import re
from fractions import Fraction

#work on cleaner strip produces '' filter removes them, overall data quality, every clean, filter etc..


urls = []
with open('urls.csv',"ab+") as queue:
    try:
        for row in unicsv.reader(queue, encoding='cp1252'):
            try:
                x = row.decode('cp1252')
                urls += x
            except:
                urls += row
    finally:
        queue.close()
        
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
        
lookup_words = []
with open('lookup_words.csv',"ab+") as lookup:
    try:
        for row in unicsv.reader(lookup, encoding='cp1252'):
            try:
                x = row.decode('cp1252')
                lookup_words.append(x)
            except:
                lookup_words.append(row)
    finally:
        lookup.close()
        
coll_words = []
with open('coll_words.csv',"ab+") as coll:
    try:
        for row in unicsv.reader(coll, encoding='cp1252'):
            try:
                x = row.decode('cp1252')
                coll_words.append(x)
            except:
                coll_words.append(row)
    finally:
        coll.close()
        
seperator = ' '       
flat_list = []
for x in lookup_words:
    flat_list += x
 
flat_list_join = seperator.join(flat_list)
coll_join = [b for l in flat_list for b in zip(l.split(" ")[:-1], l.split(" ")[1:])]  

print(flat_list_join)

def clean(x):
    hold = []
    hold += [k.lower().strip('<>\[]()!@#$%^&*;,:?"') for k in x]
    x = ''.join(hold)
    return x

def clean_line(line):
    line = re.sub(r'(\d+ ?- ?\d+)*',r'\1',line)
    hold = []
    hold += [k.lower().strip('<>\[]()!@#$%^&*;,:?"') for k in line]
    x = ''.join(hold)
    return x
    
for url in urls:
    resp = requests.get(url)
    c = resp.content
    soup = BeautifulSoup(c)
    
    soup_lines_raw = []
    ct_food_words = 0
    tolerance = 0
    for parent in soup.body.find_all_next(recursive=False):
        while np.sum(None == x.string for x in parent.descendants) <= tolerance:
            ct_food_words = 0
            text = parent.get_text(" ", strip=True).split()
            ct_text = len(text)
            for x in text:
                if x in food_words:
                    ct_food_words += 1
                else:
                    continue
            try:
                if (ct_food_words/ct_text) > .3:
                    soup_lines_raw.append(text)
                    hold = []
                    with open('allrecipes.csv',"ab+") as recipes:  
                        try:
                            for x in soup_lines_raw:
                                wr = csv.writer(recipes, dialect='excel')
                                wr.writerow([x])
                        finally:
                            recipes.close()
                            break
                else:
                    break
            except:
                break

bg_words = []
tg_words = []
fg_words = []
bg_words = list(set(BigramCollocationFinder.from_words(flat_list_join).nbest(nltk.collocations.BigramAssocMeasures().pmi, 200)))
tg_words = list(set(TrigramCollocationFinder.from_words(flat_list_join).nbest(nltk.collocations.TrigramAssocMeasures().pmi, 200)))
fg_words = list(set(QuadgramCollocationFinder.from_words(flat_list_join).nbest(QuadgramAssocMeasures.pmi, 200)))

#producing in tuple format to compare with bigrams

hold = []
bg_word = []
tg_word = []
fg_word = []

with open('coll_words_.csv',"ab+") as coll:                      
        wr = csv.writer(coll, dialect='excel')
        for coll_word in bg_words:
            hold += coll_word
            try:
                if coll_word not in coll_words:
                    wr.writerow([coll_word]) 
                    print coll_word
                else:
                    continue
            except:
                continue
'''           
with open('coll_words_.csv',"ab+") as coll:                      
        wr = csv.writer(coll, dialect='excel')
        for coll_word in tg_words:
            hold += coll_word
            try:
                if coll_word not in coll_words:
                    wr.writerow([coll_word]) 
                    print coll_word
                else:
                    continue
            except:
                continue
            
with open('coll_words_.csv',"ab+") as coll:                      
        wr = csv.writer(coll, dialect='excel')
        for coll_word in fg_words:
            hold += coll_word
            try:
                if coll_word not in coll_words:
                    wr.writerow([coll_word]) 
                    print coll_word
                else:
                    continue
            except:
                continue

'''


'''
similar = []
lines_text = nltk.text.ContextIndex([word for line in lines for word in line.split()])
for word in food_words:
    if lines_text.similar_words(word) != None:
        hold = lines_text.similar_words(word)
        for x in hold:
            similar += [k for k,v in nltk.pos_tag([x]) if v not in ['CD'] and k not in similar]
                
with open('food_words_.csv',"ab+") as food:                      
    try:
        wr = csv.writer(food, dialect='excel')
        for word in similar:
            cleaned = clean(word)
            if cleaned not in food_words:
                wr.writerow([cleaned])
                print cleaned
    finally:
        food.close()
        
'''        
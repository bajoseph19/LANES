# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
from __future__ import division
from decimal import Decimal
import nltk
from nltk import *
import pandas as pd
import scipy
import csv
from itertools import groupby
from operator import itemgetter
import numpy as np
import collections as col
import requests
import re
import urllib2
from bs4 import BeautifulSoup
import unicodecsv as csv

lines = []
lines_word_tag = []
lines_tag = []
temp_array = []
new_recipe = []
new_recipe_word_tag = []
new_recipe_tag = []
nouns = []
food_word = []
ranges = []
trim_new_recipe = []
tag_indexes = []
counts = []
new_recipe_word = []
food_words = []
word_lines = []
word_lines_merged = []
coll_words = []
hold_array = []
soup_attrs = []
soup_tags = []
soup_lines = []
soup_attrs_index = []
soup_tags_index = []
soup_lines_index = []
lines_tag_count = []

def multiply(x):
    return (x*x)
def add(x):
    return (x+x)
    
#identify schema
url = "https://nutritionistmeetschef.com/seed-crisp-bread/"
html = urllib2.urlopen(url).read()
soup = BeautifulSoup(html)
for script in soup(["script", "style","a"]):
    script.extract()

doc = soup.body.find_all_next()

for line in doc:
    try:
        soup_tags_index.append(line.name)
        soup_attrs_index.append(line.attrs)
        soup_lines_index.append(line.string.split())
    except:
        soup_tags_index.append([])
        soup_attrs_index.append([])
        soup_lines_index.append([])

soup_lines = [x for x in soup_lines_index if len(x) >1]   
soup_attrs = [x for x in soup_attrs_index if len(x) >1]       
soup_tags = [x for x in soup_tags_index if len(x) >1]                      
print soup_lines    
    
#tag_name_dist = col.Counter(tag_names)
 
with open('allrecipes.csv',"ab+") as f:
    for row in csv.reader(f, encoding='cp1252'):
        try:
            x = row.decode('cp1252')
            lines += x
        except:
            lines += row

print lines

for line in lines:
    word_lines += [line.split()]
    
print word_lines

with open('food_words_.csv',"ab+") as food:
    food_words = []
    for row in csv.reader(food, encoding='cp1252'):
        try:
            x = row.decode('cp1252')
            food_words += x
        except:
            food_words += row

print food_words

with open('coll_words_.csv',"ab+") as f:
    for row in csv.reader(f):
        coll_words += row

print coll_words      
        
for x in lines:
    word_lines_merged += x.split()

print word_lines_merged

bigram_measures = nltk.collocations.BigramAssocMeasures()
trigram_measures = nltk.collocations.TrigramAssocMeasures()
finder = BigramCollocationFinder.from_words(word_lines_merged)
print finder.nbest(bigram_measures.pmi, 200)

with open('coll_words_.csv',"ab+") as f:                      
    try:
        wr = csv.writer(f, dialect='excel')
        for k,v in list(set(finder.nbest(bigram_measures.pmi, 200))):
            b = " ".join([k,v])
            if b not in coll_words:
                wr.writerow([b])
    finally:
        f.close()
        
#Tagged lines
for x in word_lines:
    try:
        x = nltk.pos_tag(x)
        lines_word_tag.append(x)
    except:
        print 'error not pos'
        
print lines_word_tag

for x in lines_word_tag:
    for k,v in x:
        lines_tag_count.append(v)

lines_tag_dist = col.Counter(lines_tag_count)
print lines_tag_dist

#tagged patterns       
for x in lines_word_tag:
    lines_tag.append(temp_array)
    temp_array = []
    for y in x:
        temp_array.append(y[1])

print lines_tag

for a in lines_word_tag:
   for b in a:
       if b[1] in ['NN', 'NNS']:
           nouns.append(b[0])
                
with open('food_words_.csv',"ab+") as food:                      
    try:
        wr = csv.writer(food, dialect='excel')
        for a in list(set(nouns)): 
            b = a.strip(",'():")
            if b not in food_words:
                wr.writerow([b])
    finally:
        food.close()
         
#extract lines with known ingredients in them         
for a in soup_lines:
    for b in a:
        try:
            if b in food_words:
                food_word.append(soup_lines.index(a))
        except:
            print 'food words error'
            
food_word = list(set(food_word))
            
for k, g in groupby(enumerate(food_word), lambda (i, x): i-x):
        ranges.append(map(itemgetter(1), g))

ranges = [s for s in ranges if len(s) > 1]

print ranges

#extract lines with known ingredients in them         
for a in ranges:
    for i in a:
        try:
            new_recipe_word.append([soup_lines[i],i])
            new_recipe_word_tag.append([nltk.pos_tag(soup_lines[i]),i])
        except:
            print "word error"

print new_recipe_word
print new_recipe_word_tag

hold_array = []
second_array = []
temp_array = []
     
#store new recipe patterns in a db        
for x in new_recipe_word_tag:
        new_recipe_tag.append([temp_array,second_array])
        temp_array = x[1]
        hold_array = x[0]
        second_array = []
        for y in hold_array:
            second_array.append(y[1][:])

#run thru the pos patterns and match to lines
for x in new_recipe_tag:
    if x[1] in lines_tag:
        tag_indexes.append(x[0])       
       
for t in tag_indexes:
    for a in ranges:
        if t in a:
            counts.append([ranges.index(a),1])
            

dist = []
top_matches = []
temp_array = []
hold_array = []

for c in counts:
    dist.append(c[0])

dist = col.Counter(dist)
print dist
top_matches = dist.most_common(1)
print top_matches
top_picks = []

top_arrays = [t[0] for t in top_matches]
top_ranges = [ranges[x] for x in top_arrays]

print top_ranges

attrs = []
for x in top_ranges:
    for z in x:
        top_picks.append(soup_lines[z])
        attrs += [soup_attrs[z]]
        
print top_picks

for x in top_ranges:
    for z in x:
        print doc[z]
      
tags = {}
tags_dist = []
finalMap = {}
keys = []

for x in attrs:
    for key, value in x.items():
        if key in finalMap:
            if finalMap[key] == value:
                break
            else:
                keys.append(key)
        else:
            finalMap.update(x)

for x in list(set(keys)):
    del finalMap[x]

tags_dict = soup.find_all(attrs=finalMap)
text_tags = []

for line in tags_dict:
    text_tags += [line.get_text()]
   
#print finalMap
#print text_tags

#hold = []
#with open('allrecipes.csv',"ab+") as recipes:  
#    try:
 #       for x in text_tags:
  #          wr = csv.writer(recipes, dialect='excel')
   #         if x not in lines:
    #            print x
     #           wr.writerow([x])
    #finally:
     #   recipes.close()
#/




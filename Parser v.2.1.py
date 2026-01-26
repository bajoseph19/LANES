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
from bs4 import BeautifulSoup
import csv
import unicodecsv as unicsv
import numpy as np
import string
import re

#work on cleaner strip produces '' filter removes them, overall data quality, every clean, filter etc..

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

lines_tag = []
lines_pattern = []
for line in lines:
    try:
        tag = nltk.pos_tag(line.split())
        lines_tag.append(tag)
        lines_pattern.append([v for k,v in tag]) 
    except:
        print 'error'

def get_ingredients(url):
    def clean(x):
        hold = []
        hold += [k.lower().strip('<>\[]()!@#$%^&*;,:?"') for k in x]
        x = ''.join(hold)
        return x

    def clean_line(line):
        #line = line.replace(' -','-').replace(' - ','-').replace('- ','-')
        hold = []
        hold += [k.lower().strip('<>\[]()!@#$%^&*;,:?"') for k in line]
        x = ''.join(hold)
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
    
    html = urllib2.urlopen(url).read()
    soup = BeautifulSoup(html)
    for script in soup(["script", "style"]):
        script.extract()
    
    soup_lines_raw = []
    soup_tags = []
    soup_attrs = []
    tolerance = 0
    for parent in soup.body.find_all_next(recursive=False):
        while np.sum(None == x.string for x in parent.descendants) <= tolerance:
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
    
    for parent in soup.body.find_all_next(recursive=False):
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

    Attr_key = namedtuple("Attr_key", ["attr_id", "attr_value"])
    keys = {}
    hold = {}
    hold_key = {}
    for attr in soup_attrs:
        for key, values in attr.items():
            hold = {}
            if isinstance(values, list):
                if len(values) > 1:
                    value = ' '.join(values)
                    try:
                        hold_key = Attr_key(attr_id=key,attr_value=value)
                        hold = keys[hold_key]
                        keys[hold_key] += 1
                    except:
                        hold = {Attr_key(attr_id=key,attr_value=value):1}
                        keys.update(hold)
                else:
                    value = values[0]
                    try:
                       hold_key = Attr_key(attr_id=key,attr_value=value)
                       hold = keys[hold_key]
                       keys[hold_key] += 1
                    except:
                        hold = {Attr_key(attr_id=key,attr_value=value):1}
                        keys.update(hold)
            else:
                try:
                    hold_key = Attr_key(attr_id=key,attr_value=values)
                    hold = keys[hold_key]
                    keys[hold_key] += 1
                except:
                    hold = {Attr_key(attr_id=key,attr_value=values):1}
                    keys.update(hold)
    
    for key in keys.keys():
        if keys[key] == 1:
            for attr in soup_attrs:
                try:
                    if isinstance(attr[key.attr_id], list):
                        if len(attr[key.attr_id]) > 1:
                            if ' '.join(attr[key.attr_id]) == key.attr_value:
                                del attr[key.attr_id]
                        else:
                            if attr[key.attr_id][0] == key.attr_value:
                                del attr[key.attr_id]
                    else:
                        if attr[key.attr_id] == key.attr_value:
                            del attr[key.attr_id]
                except:
                    continue
    
    print soup_attrs
    
    finalMap = []
    for x in soup_attrs:
        if x not in finalMap:
            finalMap.append(x)
        else:
            continue     

    print finalMap
    
    final_recipe = [] 
    for x in finalMap:
        if x != {}:
            final_recipe += [clean(line.get_text(" ", strip=True)) for line in soup.find_all(attrs=x) if line.get_text(" ", strip=True) != '']
    
    print url
    print final_recipe
    
    lookups_q = ['teaspoons',	'teaspoon',	'tsp',	'tsp.',	'tablespoons',	'tablespoon',	
                 'tbl',	'tbl.',	'tbs',	'tbs.',	'tbsp',	'tbsp.',	'ounce',	'ounces',	'oz',	
                 'fluid ounce',	'fluid ounces',	'fluid oz',	'fluid oz.',	'fl ounce',	'fl ounces',	
                 'fl. oz.',	'fl. oz',	'fl oz',	'pint',	'pints',	'pt',	'pts',	'pt.',	'pts',	
                 'fluid pint',	'fluid pints',	'fl. pts',	'fl. pts.',	'fl pts',	'fl. pt',	'fl. pt.',	
                 'fl pt',	'gallon',	'gallons',	'gal.',	'gal',	'gals.',	'gals',	'quart',	'quarts',	
                 'qt',	'qts',	'qt.',	'qts',	'fluid quart',	'fluid quarts',	'fl. qts',	'fl. qts.',	
                 'fl qts',	'fl. qt',	'fl. qt.',	'fl qt',	'milliliter',	'millilitre',	'milliliters',	
                 'millilitres',	'ml',	'ml.',	'liter',	'litre',	'liters',	'litres',	'l',	'l.',	
                 'pound',	'pounds',	'lb',	'lbs',	'lb.',	'lbs.',	'milligram',	'milligrams',	'mg',	
                 'mgs',	'mg.',	'mgs.',	'gram',	'grams',	'g',	'gs',	'g.',	'gs.',	'kilogram',	
                 'kilograms',	'kg',	'kgs',	'kg.',	'kgs.',	'millimeter',	'millimetre',	'millimeters',	
                 'millimetres',	'mm',	'mm.',	'centimeter',	'centimetre',	'centimeters',	'centimetres',	
                 'cm',	'cm.',	'meter',	'metre',	'meters',	'metres',	'm',	'm.',	'inch',	'inches',	
                 'in',	'in.']
  
    measure_tag = []
    measure_pattern = []
    measure_patterns = []
    for line in final_recipe:
        try:
            measure_tag = nltk.pos_tag(line.split())
            measure_pattern = [v for k,v in measure_tag]
            for index,word in enumerate(line.split()):
                if word in lookups_q:
                    print 'found'
                    measure_pattern[index] = word
                    measure_patterns.append(measure_pattern)
        except:
            print 'error measure'

    print measure_patterns 

    lookups_q_re  = [
            (r"(\d+ |\d+\/\d+ |\d+\.\d+ |\d+\ ?(\-|or|to|and) ?\d+ )*(fluid|fl.?)? ?(pints?|quarts?|(gallons?|gals?\.?)|(ounces?|ozs?\.?)|(milli|centi)?(me|li)(ters?|tres?)|(kilo|milli)?(grams?)|(p|q)ts?\.?)* ?((tea|table)spoons?|tb(s.?|sp.?|l.?)|tsp.?)* ?(m(l|m)s?\.? |(m|k)?(gs?\.? )|(pounds?|lbs?\.?)|cms?\.? |l\.? |(inch[es]*|in.? ))*", 'a'),
            (r"(\d+ |\d+\/\d+ |\d+\.\d+ |\d+\ ?(\-|or|to|and) ?\d+ )*", 'b'),
            ]

    def lookup(s, lookups):
        print s
        for pattern, value in lookups:
            if re.search(pattern, s):
                print re.search(pattern, s).group()
                return value
        return None
    
    for line in final_recipe:
        value = lookup(line, lookups_q_re)
        print value
    
    with open('patterns.csv',"ab+") as patterns:  
        try:
            wr = csv.writer(patterns, dialect='excel')
            for line in final_recipe:
                try:
                    cleaned = clean_line(line)
                    if cleaned not in lines and len(cleaned.split()) > 3:
                        wr.writerow([cleaned])
                        print cleaned
                except:
                    continue
        finally:
            patterns.close()
            
for url in urls:
    get_ingredients(url)

                         
'''  

Lookups = namedtuple("Lookups", ["regex", "label"])





LOOKUPS  = [
    ('a.*', 'a'),
    ('b.*', 'b'),
]

def lookup_q(line, lookups_q):
    for pattern, value in lookups:
        if re.search(pattern, s):
            return value
    return None
    
    lines_text = nltk.text.ContextIndex([word for line in lines for word in line.split()])
    match_lines = []
    match_words = []
    nouns = []
    for line in final_recipe:
        match_words = []
        nouns = []
        nouns += [k for k,v in nltk.pos_tag(line.split()) if v in ['NN','NNS']]
        for word in nouns:
            if lines_text.similar_words(word) != None:
                hold = lines_text.similar_words(word)
                match_words.append([k for x in hold for k,v in nltk.pos_tag([x]) if v not in ['CD']])
                print match_words
                match_lines.append([a for k in match_words for a,b in enumerate(lines) if k in b.split()])
            else:
                continue
            
    print match_lines

        final_tag = []
    final_pattern = []
    final_bigrams = []
    for line in final_recipe:
        try:
            tag = nltk.pos_tag(line.split())
            final_bigrams.append(list(ngrams([k for k,v in tag],2)))
            final_pattern.append([v for k,v in tag]) 
        except:
            print 'error 1'

    for b_index,bigram in enumerate(final_bigrams):
        for g_index,gram in enumerate(bigram):
            if gram in coll_words_b:
                final_pattern[b_index][g_index] = gram[0]
                final_pattern[b_index][g_index+1] = gram[1]     

            
    print final_pattern
    
    final_measure = []
    f_cd = []
    for line in final_recipe:
        try:
            tag = nltk.pos_tag(line.split())
            for k,v in tag:
               if v in ['CD']:
                f_cd = k
                print f_cd
                break
        except:
            print 'error 2'
                                 
'''                        
'''        
#only want nouns
word_lines = []         
for line in lines:
    tag = nltk.pos_tag(line.split())
    word_lines += [k for k,v in tag if v in ['NN',	'NNS']]

bg_words = []
tg_words = []
fg_words = []
bg_words = list(set(BigramCollocationFinder.from_words(word_lines).nbest(nltk.collocations.BigramAssocMeasures().pmi, 200)))
tg_words = list(set(TrigramCollocationFinder.from_words(word_lines).nbest(nltk.collocations.TrigramAssocMeasures().pmi, 200)))
fg_words = list(set(QuadgramCollocationFinder.from_words(word_lines).nbest(QuadgramAssocMeasures.pmi, 200)))

#producing in tuple format to compare with bigrams
coll_words_b = []
coll_words_t = []
coll_words_f = [] 
split = ()           
for k in coll_words:
    split = [k.split()]
    if len(split) == 2:
        for k,v in split:
            coll_words_b.append((k,v))
    elif len(split) == 3:
        for k,v,y in split:
            coll_words_t.append((k,v,y))
    elif len(split) == 4:
        for k,v,y,z in split:
            coll_words_f.append((k,v,y,z))
    else:
        continue

hold = []
with open('coll_words_.csv',"ab+") as coll:                      
    try:
        wr = csv.writer(coll, dialect='excel')
        for coll_word in bg_words:
            hold += coll_word
            try:
                cleaned = ' '.join([clean(word) for word in hold])
                hold = []
                if cleaned not in coll_words:
                    wr.writerow([cleaned]) 
                    print cleaned
            except:
                continue
           
        for coll_word in tg_words:
            hold += coll_word
            try:
                cleaned = ' '.join([clean(word) for word in hold])
                hold = []
                if cleaned not in coll_words:
                    wr.writerow([cleaned]) 
                    print cleaned
            except:
                continue
        for coll_word in fg_words:
            hold += coll_word
            try:
                cleaned = ' '.join([clean(word) for word in hold])
                hold = []
                if cleaned not in coll_words:
                    wr.writerow([cleaned]) 
                    print cleaned
            except:
                continue
    finally:
        coll.close()

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
            
>>> from collections import namedtuple
>>> Fruit = namedtuple("Fruit", ["name", "color"])
>>> f = Fruit(name="banana", color="red")
>>> print f
Fruit(name='banana', color='red')
>>> f.name
'banana'
>>> f.color
'red'
Now you can use your fruitcount dict:

>>> fruitcount = {Fruit("banana", "red"):5}
>>> fruitcount[f]
5
Other tricks:

>>> fruits = fruitcount.keys()
>>> fruits.sort()
>>> print fruits
[Fruit(name='apple', color='green'), 
 Fruit(name='apple', color='red'), 
 Fruit(name='banana', color='blue'), 
 Fruit(name='strawberry', color='blue')]
>>> fruits.sort(key=lambda x:x.color)
>>> print fruits
[Fruit(name='banana', color='blue'), 
 Fruit(name='strawberry', color='blue'), 
 Fruit(name='apple', color='green'), 
 Fruit(name='apple', color='red')]


def multiple_replace(dict, text): 

  """ Replace in 'text' all occurences of any key in the given
  dictionary by its corresponding value.  Returns the new tring.""" 

  # Create a regular expression  from the dictionary keys
  regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))

  # For each match, look-up corresponding value in dictionary
  return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text) 

#
# You may combine both the dictionnary and search-and-replace
# into a single object using a 'callable' dictionary wrapper
# which can be directly used as a callback object.
#

import re

LOOKUPS  = [
    ('a.*', 'a'),
    ('b.*', 'b'),
]

def lookup(s, lookups):
    for pattern, value in lookups:
        if re.search(pattern, s):
            return value
    return None

print(lookup("apple", LOOKUPS))


'''
###################################PARSER#####################################


        
#['CC',	'CD',	'DT',	'LS',	'MD',	'NN',	'NNS',	'NNP',	
# 'NNPS',	'PDT',	'VB',	'VBD',	'VBN',	'VBG',	'IN',	'JJ',	
# 'RB',	'TO']
#nouns = []
#nouns += [k for k,v in tag if v in ['NN', 'NNS'] and k not in nouns]

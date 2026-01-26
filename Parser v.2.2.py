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
from fractions import Fraction

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
    lookups_fracs  = [
            (r'(\d+) (\d+)/(\d+)', lambda m: str(round(float(int(m.group(1)) + int(m.group(2))/int(m.group(3))),2))),
            (r'(\d+)/(\d+)', lambda m: str(round(int(m.group(1))/int(m.group(2)),2))),
            (r'(\d+)(-| or | to )(\d+)', lambda m: max(m.group(1),m.group(2)))
            ]
    
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

    def convert_fracs(s):
        for pattern, value in lookups_fracs:
            if re.search(pattern, s):
                s = re.sub(pattern,value,s)
        return s
    
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
    raw_recipe = []
    for x in finalMap:
        if x != {}:
            raw_recipe += [clean(line.get_text(" ", strip=True)) for line in soup.find_all(attrs=x) if line.get_text(" ", strip=True) != '']
            final_recipe += [convert_fracs(clean(line.get_text(" ", strip=True))) for line in soup.find_all(attrs=x) if line.get_text(" ", strip=True) != '']
    
    print url
    print final_recipe
    
    Ingredient = namedtuple("Ingredient", ["s","qu_m_r","qu_m","qu_s","qu_r","qu"])
    Measure = namedtuple("Measure", ["s","r","qu_m"])
    Quantity = namedtuple("Quantity", ["s","r","qu"])
    Item = namedtuple("Item", ["s","r","ns","vs"])
    lookups_cc = [
            (r'(?P<b_or>^.* or )(?P<a_or>.*$)','or'),
            (r'(?P<b_and>^.* and )(?P<a_and>.*$)','and'),
            (r'(?P<b_with>^.* with )(?P<a_with>.*$)','with'),
            (r'(?P<b_inof>^.* instead of )(?P<a_inof>.*$)','instead of'),
            ]
    lookups_qu_m = [
            (r'(?P<qu_1>\d+\.?\d{0,2} )(?P<qu_2>\d+\.?\d{0,2} )?(?P<measure>fluid ounces?(?:\s|$)|fluid ozs?\.?(?:\s|$)|fl\.? ounces?(?:\s|$)|fl\.? ozs?\.?(?:\s|$)|pints?(?:\s|$)|pts?\.?(?:\s|$)|gallons?(?:\s|$)|gals?\.?(?:\s|$)|quarts?(?:\s|$)|qts?\.?(?:\s|$)|millilit[re]{2,2}s?(?:\s|$)|mls?\.?(?:\s|$)|lit[re]{2,2}s?(?:\s|$)|ls?\.?(?:\s|$)|teaspoons?(?:\s|$)|tsp.?(?:\s|$)|tablespoons?(?:\s|$)|tbl\.?(?:\s|$)|tbsp?.?(?:\s|$)|cups?(?:\s|$)|ounces?(?:\s|$)|ozs?\.?(?:\s|$)|pounds?(?:\s|$)|lbs?\.?(?:\s|$)|milligrams?(?:\s|$)|mgs?\.?(?:\s|$)|grams?(?:\s|$)|gs?.?(?:\s|$)|kilograms?(?:\s|$)|kgs?\.?(?:\s|$)|millimet[er]{2,2}s?(?:\s|$)|mms?\.?(?:\s|$)|centimet[er]{2,2}s?(?:\s|$)|cms?\.?(?:\s|$)|met[er]{2,2}s?(?:\s|$)|m\.?(?:\s|$)|inch(?:\s|$)|inches(?:\s|$))?(?P<unit>cans?(?:\s|$)|jars?(?:\s|$)|packages?(?:\s|$)|containers?(?:\s|$)|cartons?(?:\s|$)|box?(?:\s|$)|packages?(?:\s|$)|loafs?(?:\s|$))?','1')
            ]
    lookups_qu_c = [
            (r'(?P<qu>\d+\.?\d{0,2})(?P<container> cans?(?:\s|$)| jars?(?:\s|$)| packages?(?:\s|$)| containers?(?:\s|$)| cartons?(?:\s|$)| box?(?:\s|$)| packages?(?:\s|$)| loafs?(?:\s|$))?','1')
            ]
    lookups_item = [
            (r'(?P<all>.*$)','1')
            ]
    
    def get_qu_m(c):
        qu_m = Measure(s=c,r=c,qu_m='unit')
        for pattern, value in lookups_cc:
            if re.search(pattern, c):
                cc = re.search(pattern, c)
                if value == 'or':
                    for pattern, value in lookups_qu_m:
                        if re.search(pattern,cc.group('b_or')) and re.search(pattern,cc.group('a_or')):
                            m = re.findall(pattern, c)
                            m.append('or')
                            r = re.sub(' or ',' ',c)
                            r = re.sub(pattern,'',r)
                            qu_m = Measure(s=c,r=r,qu_m=m)
                            return qu_m
                            break    
                elif value == 'and':
                    for pattern, value in lookups_qu_m:
                        if re.search(pattern,cc.group('b_and')) and re.search(pattern,cc.group('a_and')):
                            m = re.findall(pattern, c)
                            m.append('and')
                            r = re.sub(' and ',' ',c)
                            r = re.sub(pattern,'',r)
                            qu_m = Measure(s=c,r=r,qu_m=m)
                            return qu_m
                            break   
                elif value == 'with':
                    for pattern, value in lookups_qu_m:
                        if re.search(pattern,cc.group('b_with')) and re.search(pattern,cc.group('a_with')):
                            m = re.findall(pattern, c)
                            m.append('with')
                            r = re.sub(' with ',' ',c)
                            r = re.sub(pattern,'',r)
                            qu_m = Measure(s=c,r=r,qu_m=m)
                            return qu_m
                            break   
                elif value == 'instead of':
                    for pattern, value in lookups_qu_m:
                        if re.search(pattern,cc.group('b_inof')) and re.search(pattern,cc.group('a_inof')):
                            m = re.findall(pattern, c)
                            m.append('instead of')
                            r = re.sub(' instead of ',' ',c)
                            r = re.sub(pattern,'',r)
                            qu_m = Measure(s=c,r=r,qu_m=m)
                            return qu_m
                            break   
        for pattern, value in lookups_qu_m:
            if re.search(pattern, c):
                m = re.findall(pattern, c)
                r = re.sub(pattern,'',c)
                qu_m = Measure(s=c,r=r,qu_m=m)
                return qu_m
                break
        return qu_m
    
    def get_qu_c(qu_m):
        qu_c = Quantity(s=qu_m.r,r=qu_m.r,qu='unit')
        for pattern, value in lookups_cc:
            if re.search(pattern, qu_m.r):
                cc = re.search(pattern, qu_m.r)
                if value == 'or':
                    for pattern, value in lookups_qu_c:
                        if re.search(pattern,cc.group('b_or')) and re.search(pattern,cc.group('a_or')):
                            m = re.findall(pattern,qu_m.r)
                            m.append('or')
                            r = re.sub(' or ',' ',qu_m.r)
                            r = re.sub(pattern,'',r)
                            qu_c = Quantity(s=qu_m.r,r=r,qu=m)
                            return qu_c
                            break    
                elif value == 'and':
                    for pattern, value in lookups_qu_c:
                        if re.search(pattern,cc.group('b_and')) and re.search(pattern,cc.group('a_and')):
                            m = re.findall(pattern,qu_m.r)
                            m.append('and')
                            r = re.sub(' and ',' ',qu_m.r)
                            r = re.sub(pattern,'',r)
                            qu_c = Quantity(s=qu_m.r,r=r,qu=m)
                            return qu_c
                            break   
                elif value == 'with':
                    for pattern, value in lookups_qu_c:
                        if re.search(pattern,cc.group('b_with')) and re.search(pattern,cc.group('a_with')):
                            m = re.findall(pattern,qu_m.r)
                            m.append('with')
                            r = re.sub(' with ','',qu_m.r)
                            r = re.sub(pattern,' ',r)
                            qu_c = Quantity(s=qu_m.r,r=r,qu=m)
                            return qu_c
                            break   
                elif value == 'instead of':
                    for pattern, value in lookups_qu_c:
                        if re.search(pattern,cc.group('b_inof')) and re.search(pattern,cc.group('a_inof')):
                            m = re.findall(pattern,qu_m.r)
                            m.append('instead of')
                            r = re.sub(' instead of',' ',qu_m.r)
                            r = re.sub(pattern,'',r)
                            qu_c = Quantity(s=qu_m.r,r=r,qu=m)
                            return qu_c
                            break   
        for pattern, value in lookups_qu_c:
            if re.search(pattern, qu_m.r):
                m = re.findall(pattern,qu_m.r)
                r = re.sub(pattern,'',qu_m.r)
                qu_c = Quantity(s=qu_m.r,r=r,qu=m)
                return qu_c
                break
        return qu_c
    
    def get_it(qu_c):
        for pattern, value in lookups_item:
            if re.search(pattern,qu_c.r):
                m = re.search(pattern,qu_c.r)
                it_r = re.sub(pattern,'',qu_c.r)
                it = Item(s=qu_c.r,r=it_r,ns=m.group('all'),vs='none')
                return it
                break
        return it
    
    def get_ing(s,qu_m,qu_c,it):
        ing = Ingredient(s=s,qu_m_r=qu_m.r,qu_m=qu_m.qu_m,qu_s=qu_c.s,qu_r=qu_c.r,qu=qu_c.qu)
        return ing
    
    def codify(s):
        c = convert_fracs(s)
        qu_m = get_qu_m(c)
        qu_c = get_qu_c(qu_m)
        it = get_it(qu_c)
        ing = get_ing(s,qu_m,qu_c,it)
        return ing
    
    tag = []
    final_pattern = []
    for line in final_recipe:
        try:
            tag = nltk.pos_tag(line.split())
            final_pattern.append([v for k,v in tag])
        except:
            print 'error final pattern'

    print final_pattern
    
    for index,line in enumerate(final_recipe):
        codified = codify(line)
        print final_pattern[index]
        print codified
    
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
    def get_qu_m(c):
        for pattern, value in lookups_cc:
            if re.search(pattern, c):
                m = re.search(pattern, c)
                elif value == 'or':
                    
                elif value == 'and':
                elif value == 'with':
                elif value == 'instead of':
        for pattern, value in lookups_qu_m:
            qu_m = Measure(s=c,r=c,qu_m=1,u_m='unit',m_type='unit')
            if re.search(pattern, c):
                m = re.search(pattern, c)
                r = re.sub(pattern,'',c)
                if value == '1':
                    qu_m = Measure(s=c,r=r,qu_m=m.group('qu_m'),u_m=m.group('u_m'),m_type='liquid')
                    return qu_m
                    break
                elif value == '2':
                    qu_m = Measure(s=c,r=r,qu_m=m.group('qu_m'),u_m=m.group('u_m'),m_type='unknown')
                    return qu_m
                    break
                elif value == '3':
                    qu_m = Measure(s=c,r=r,qu_m=m.group('qu_m'),u_m=m.group('u_m'),m_type='dry')
                    return qu_m
                    break
                elif value == '4':
                    qu_m = Measure(s=c,r=r,qu_m=m.group('qu_m'),u_m=m.group('u_m'),m_type='length')
                    return qu_m
                    break
        return qu_m

in the same pattern itself	
(?P=quote) (as shown)
\1
when processing match object m	
m.group('quote')
m.end('quote') (etc.)
in a string passed to the repl argument of re.sub()	
\g<quote>
\g<1>
\1

Lookups = namedtuple("Lookups", ["regex", "label"])



(r"(fluid|fl.?)? ?(pints?|quarts?|gallons?|gals?\.?|ounces?|ozs?\.?|(milli|centi)?(me|li)(ters?|tres?)|(kilo|milli)?(grams?)|(p|q)ts?\.?)* ?((tea|table)spoons?|tb(s.?|sp.?|l.?)|tsp.?)* ?(m(l|m)s?\.? |(m|k)?(gs?\.? )|(pounds?|lbs?\.?)|cms?\.? |l\.? |(inch[es]*|in.? ))*", 'b'),
(r"(\d+ |\d+\/\d+ |\d+\.\d+ |\d+\ ?(\-|or|to|and) ?\d+ )*", 'c'),

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

'''
Patient Info Parser.
'''
from __future__ import division
import glob, re
from nltk import sent_tokenize, word_tokenize
from collections import defaultdict

MALE = set(['male', 'man', 'dad', 'daddy', 'father', 'grandfather', \
'grand-father', 'son', 'boy', 'uncle', 'sir', 'gentleman', 'husband'])

FEMALE = set(['female', 'woman', 'mom', 'mother', 'mommy', 'grandmother', \
'grand-mother', 'daughter', 'girl', 'aunt', 'lady', 'wife'])

REG = set([r'\d+(?:-| )?year(?:s)?(?:-| )?old', \
  r'in(?: )?his(?: )?\d+s|in(?: )?her(?: )?\d+s'])

DIR = '/home/yba/Documents/summer_2017/Arrhythmias/Arrhythmias'
# Files in DIR must have the following format: 'something.txt'

DEBUG = True

def detectGender(sent):
  rtn = []
  for word in word_tokenize(sent): # split a sentence into words
    checkGenderWord(word, MALE, 'male', rtn)
    checkGenderWord(word, FEMALE, 'female', rtn)
  return rtn

def checkGenderWord(word, set, label, li):
  for w in set:
    if w.lower() == word.lower():
      li.append({'gender': label, 'from': w})

def detectAge(sent):
  rtn = []
  for reg in REG:
    for str in re.findall(reg, sent, re.I):
      for i in re.findall(r'\d+', str):
        rtn.append({'age': i, 'from': str})
  return rtn

class Doc:
  # States.
  G_NOT_SET = 0
  G_SET = 1
  G_CONFLICT = 2
  A_NOT_SET = 3
  A_SET = 4
  A_CONFLICT = 5

  def __init__(self, id):
    self.id = id
    self.gender = None # not sure
    self.age = None # not sure
    self.gender_info = {}
    self.age_info = {}
    self.gender_conflict = False
    self.age_conflict = False

  def getStates(self):
    rtn = []
    if not self.gender:
      if not self.gender_conflict:
        rtn.append(self.G_NOT_SET)
      else:
        rtn.append(self.G_CONFLICT)
    else:
      rtn.append(self.G_SET)
    if not self.age:
      if not self.age_conflict:
        rtn.append(self.A_NOT_SET)
      else:
        rtn.append(self.A_CONFLICT)
    else:
      rtn.append(self.A_SET)
    return rtn

  def setGenderSure(self, gender, gender_info):
    self.gender = gender
    self.gender_info = gender_info
    if self.age_conflict:
      if self.resolveConflict():
        print '--- 1 Age conflict resolved due to sure gender for', self.id
        self.age_conflict = False

  def setAgeSure(self, age, age_info):
    self.age = age
    self.age_info = age_info
    if self.gender_conflict:
      if self.resolveConflict():
        print '--- 2 Gender conflict resolved due to sure age for', self.id
        self.gender_conflict = False

  def setGenderUnsure(self, gender_info): # unsure due to conflict
    self.gender_info = gender_info
    if self.resolveConflict():
      if self.age_conflict:
        print '--- 3 Gender-age conflicts co-resolved for', self.id
        self.age_conflict = False
      else:
        print '--- 4 Gender conflict resolved due to sure age for', self.id
    else:
      self.gender_conflict = True

  def setAgeUnsure(self, age_info): # unsure due to conflict
    self.age_info = age_info
    if self.resolveConflict():
      if self.gender_conflict:
        print '--- 5 Gender-age conflicts co-resolved for', self.id
        self.gender_conflict = False
      else:
        print '--- 6 Age conflict resolved due to sure gender for', self.id
    else:
      self.age_conflict = True

  def getGenderInfo(self):
    return self.gender_info

  def getAgeInfo(self):
    return self.age_info

  def resolveConflict(self):
    # Returns True if resolved, False otherwise.
    if self.gender_info and self.age_info:
      dd = self.intersectDicts(self.gender_info, self.age_info)
      # example of solvable:
      # {'a 100-year-old man': 
      # [
      #  [{'gender': 'male', 'from': 'man'}], 
      #  [{'age': '53', 'from': '53-year-old'}]
      # ]}
      if not dd:
        print 'Cannot resolve for case %s reason (1)' % self.id
        return False
      gender_seen = set()
      age_seen = set()
      for _, ga in dd.iteritems():
        assert(len(ga) == 2)
        g = ga[0]
        a = ga[1]
        if len(g) != 1 or len(a) != 1:
          print 'Cannot resolve for case %s reason (2)' % self.id
          return False
        gender_seen.add(g[0]['gender'])
        age_seen.add(a[0]['age'])
      if len(gender_seen) > 1 or len(age_seen) > 1:
        print 'Probably %s or %s cases for %s' % (len(gender_seen), \
          len(age_seen), self.id)
        return False
      assert(gender_seen and age_seen)
      self.gender = next(iter(gender_seen))
      self.age = next(iter(age_seen))
      return True
    else:
      return False

  def intersectDicts(self, d1, d2):
    dd = defaultdict(list)
    for k, v1 in d1.iteritems():
      if k in d2:
          dd[k].append(v1)
          dd[k].append(d2[k])
    return dd

def testAllDocsIn(dir, info_name, docs={}):
  if info_name == 'gender':
    detector = detectGender
    setter_sure = Doc.setGenderSure
    setter_unsure = Doc.setGenderUnsure
    info_getter = Doc.getGenderInfo
  elif info_name == 'age':
    detector = detectAge
    setter_sure = Doc.setAgeSure
    setter_unsure = Doc.setAgeUnsure
    info_getter = Doc.getAgeInfo
  else:
    raise RuntimeError()
  normal_docs = []
  no_info_docs = []
  conflicted_info_docs = []
  files = sort_nicely(glob.glob('%s/*.txt' % dir))
  for filename in files:
    with open(filename, 'r') as fin:
      id = filename.split('/')[-1]
      if id in docs:
        doc = docs[id] # use the existing Doc
      else:
        doc = Doc(id)
        docs[id] = doc
      doc_info = {}
      seen = set()
      for line in fin:
        for sent in sent_tokenize(line): # split a document into sentences
          sent_info = detector(sent)
          if not sent_info:
            continue
          doc_info[sent] = sent_info
          for i in sent_info:
            seen.add(i[info_name])
    # Classify the document.
    if len(seen) == 1:
      normal_docs.append(doc)
      setter_sure(doc, next(iter(seen)), doc_info)
    elif len(seen) == 0:
      no_info_docs.append(doc)
    elif len(seen) >= 2:
      conflicted_info_docs.append(doc)
      setter_unsure(doc, doc_info)
    else:
      raise RuntimeError('Should not see this')
  lm, ln, lc, conflicted_info_docs = printStats([no_info_docs, normal_docs, \
    conflicted_info_docs], info_name, info_getter)
  return docs, lm, ln, lc, conflicted_info_docs

def printStats(lists, info_name, info_getter):
  # lists must be [no_info_docs, normal_docs, conflicted_info_docs]
  print '*'*20, info_name, '*'*20
  assert(len(lists) == 3)
  no_info_docs = lists[0]
  normal_docs = lists[1]
  conflicted_info_docs = lists[2]
  lm = len(normal_docs)
  ln = len(no_info_docs)
  lc = len(conflicted_info_docs)
  lt = lm + ln + lc
  print '%s files are normal:' % lm
  if DEBUG:
    print [d.id for d in normal_docs]
  print
  print '%s files have no %s detected:' % (ln, info_name)
  if DEBUG:
    print [d.id for d in no_info_docs]
  print
  print '%s files have conflicted %ss info detected:' % (lc, info_name)
  print [d.id for d in conflicted_info_docs]
  print
  if DEBUG:
    for d in conflicted_info_docs:
      print d.id+'-'*50
      for sent, info in info_getter(d).iteritems():
        print '%s\t%s\n' % (info, sent)
  print '%s + %s + %s = %s'%(lm, ln, lc, lt)
  print '%s / %s = %s' % (lm, lt, lm / lt)
  print '%s / %s = %s' % (ln, lt, ln / lt)
  print '%s / %s = %s' % (lc, lt, lc / lt)
  print 'Processed %s files in %s' % (lt, DIR)
  return lm, ln, lc, conflicted_info_docs

def genderAgeCoDetection():
  docs = {}
  # docs, lm1, ln1, lc1, lt1 = testAllDocsIn(DIR, 'age', docs)
  docs, lm1, ln1, lc1, conf_docs1 = testAllDocsIn(DIR, 'gender', docs)
  docs, lm2, ln2, lc2, conf_docs2 = testAllDocsIn(DIR, 'age', docs)
  lists_of_6 = getDocsStats(docs)
  lists_g = lists_of_6[0:3]
  lists_a = lists_of_6[3:6]
  print '='*20, 'AFTER CO_RESOLUTION', '='*20
  lm3, ln3, lc3, conf_docs3 = printStats(lists_g, 'gender', Doc.getGenderInfo)
  lm4, ln4, lc4, conf_docs4 = printStats(lists_a, 'age', Doc.getAgeInfo)
  print '='*40, 'Summary', '='*40
  print 'Gender\n\t\tNormal\tNo_info\tConflict'
  print 'Before\t\t%s\t%s\t%s' % (lm1, ln1, lc1)
  print 'After\t\t%s\t%s\t%s' % (lm3, ln3, lc3)
  gender_improv = list(set(conf_docs1) - set(conf_docs3))
  print '%s docs have their gender info resolved after co-detection:' \
  % len(gender_improv)
  print sort_nicely([d.id for d in gender_improv])
  print '\nAge\n\t\tNormal\tNo_info\tConflict'
  print 'Before\t\t%s\t%s\t%s' % (lm2, ln2, lc2)
  print 'After\t\t%s\t%s\t%s' % (lm4, ln4, lc4)
  age_improv = list(set(conf_docs2) - set(conf_docs4))
  print '%s docs have their age info resolved after co-detection:' \
  % len(age_improv)
  print sort_nicely([d.id for d in age_improv])

def getDocsStats(docs):
  lists = [[] for i in range(6)]
  for _, doc in docs.iteritems():
    states = doc.getStates()
    lists[states[0]].append(doc)
    lists[states[1]].append(doc)
  return lists

'''
Code below is from 
https://stackoverflow.com/questions/4623446/how-do-you-sort-files-numerically.
'''
def tryint(s):
    try:
        return int(s)
    except:
        return s

def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

def sort_nicely(l):
    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key)
    return l

'''
End of borrowing.
'''

if __name__ == '__main__':
  # testAllDocsIn(DIR, 'gender')
  # print detectAge('A 987-YEAR-old man case of a 15-years old girl A 76-yearold man')
  genderAgeCoDetection()

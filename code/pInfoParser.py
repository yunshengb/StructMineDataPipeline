'''
Patient Info Parser.
'''
from __future__ import division
import glob, re
from nltk import sent_tokenize, word_tokenize

MALE = set(['male', 'man', 'dad', 'daddy', 'father', 'grandfather', \
'grand-father', 'son', 'boy', 'uncle', 'sir', 'gentleman', 'husband'])

FEMALE = set(['female', 'woman', 'mom', 'mother', 'mommy', 'grandmother', \
'grand-mother', 'daughter', 'girl', 'aunt', 'lady', 'wife'])

def genderIdentification(sent):
  rtn = []
  for word in word_tokenize(sent): # split a sentence into words
    checkWord(word, MALE, 'male', rtn)
    checkWord(word, FEMALE, 'female', rtn)
  return rtn

def checkWord(word, set, label, li):
  for w in set:
    if w.lower() == word.lower():
      li.append({'gender': label, 'gender_found_from': w})

def testAllDocsIn(dir):
  normal_docs = []
  conflicted_g_info_docs = []
  no_g_info_docs = []
  docs = {'normal': normal_docs, 'no_g_info': conflicted_g_info_docs, \
  'conflicted_g_info': no_g_info_docs}
  files = sort_nicely(glob.glob('%s/*.txt' % dir))
  for filename in files:
    with open(filename, 'r') as fin:
      doc = {'id': filename.split('/')[-1]}
      g_info = []
      doc['g_info'] = g_info
      genders = set()
      for line in fin:
        for sent in sent_tokenize(line): # split a document into sentences
          g = genderIdentification(sent)
          if g:
            g_info.append({'sent': sent, 'sent_g_info': g})
            for x in g:
              genders.add(x['gender'])
    # Classify the document.
    if len(genders) == 1:
      normal_docs.append(doc)
    elif len(genders) == 2:
      conflicted_g_info_docs.append(doc)
    elif len(genders) == 0:
      no_g_info_docs.append(doc)
    else:
      raise RuntimeError('Should not see this')
  lm = len(normal_docs)
  ln = len(no_g_info_docs)
  lc = len(conflicted_g_info_docs)
  lt = len(files)
  print '%s files are normal:' % lm
  print [d['id'] for d in normal_docs]
  print
  print '%s files have no gender detected:' % ln
  print [d['id'] for d in no_g_info_docs]
  print
  print '%s files have conflicted gender info detected:' % lc
  print [d['id'] for d in conflicted_g_info_docs]
  print
  for d in conflicted_g_info_docs:
    print d['id']+'-'*50
    for sent in d['g_info']:
      print '%s\t%s\n' % (sent['sent_g_info'], sent['sent'])
  print '%s + %s + %s = %s'%(lm, ln, lc, lt)
  print '%s / %s = %s' % (lm, lt, lm / lt)
  print '%s / %s = %s' % (ln, lt, ln / lt)
  print '%s / %s = %s' % (lc, lt, lc / lt)
  print 'Processed %s files in %s' % (lt, dir)

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
  testAllDocsIn('/home/yba/Documents/summer_2017/Arrhythmias/Arrhythmias')

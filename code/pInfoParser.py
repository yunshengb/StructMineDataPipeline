'''
Patient Info Parser.
'''
import glob
from nltk import sent_tokenize, word_tokenize

MALE = set(['male', 'man', 'dad', 'daddy', 'father', 'grandfather', \
'grand-father', 'son', 'boy', 'uncle', 'sir', 'gentleman', 'husband'])

FEMALE = set(['female', 'woman', 'mom', 'mother', 'mommy', 'grandmother', \
'grand-mother', 'daughter', 'girl', 'aunt', 'lady', 'wife'])

def genderIdentification(sent):
  rtn = []
  for word in word_tokenize(sent):
    checkWord(word, MALE, 'male', rtn)
    checkWord(word, FEMALE, 'female', rtn)
  return rtn

def checkWord(word, set, label, li):
  for w in set:
    if w.lower() == word.lower():
      li.append({'gender': label, 'gender_found_from': w})

def testAllDocsIn(dir):
  files = glob.glob('%s/*.txt' % dir)
  for filename in files:
    with open(filename, 'r') as fin:
      p_ = False
      p = filename+'-'*50+'\n'
      for line in fin:
        for sent in sent_tokenize(line):
          r = genderIdentification(sent)
          if r:
            p += '%s\t%s\n' % (r, sent)
            if len(r) > 1:
              p_ = True
    if p_:
      print p
  print 'Processed %s files' % len(files)


if __name__ == '__main__':
  testAllDocsIn('/home/yba/Documents/summer_2017/Arrhythmias/Arrhythmias')

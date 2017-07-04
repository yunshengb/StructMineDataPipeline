import sys
import nltk
from stanza.nlp.corenlp import CoreNLPClient
import json
from collections import OrderedDict
from distantSupervision import linkToFB, getNegRMs
from dbpedia import dbpediaParse


class NLPParser(object):
    """
    NLP parse, including Part-Of-Speech tagging.
    Attributes
    ==========
    parser: StanfordCoreNLP
        the Staford Core NLP parser
    """
    def __init__(self):
        self.parser = CoreNLPClient(default_annotators=['ssplit', 'tokenize', 'ner'])

    def parse(self, sent):
        result = self.parser.annotate(sent)
        tokens_list, ner_list = [], []
        print result.sentences
        for sent in result.sentences:
            tokens, ner = [], []
            currNERType = 'O'
            currNER = ''
            for token in sent:
                print 'token', token
                tokens += [token.word]
                print 'tokens', tokens
                if token.ner == 'O':
                  if currNER != '':
                    ner.append(currNER.strip())
                  currNER = ''
                elif token.ner == currNERType:
                  currNER += token.word + ' '
                else:
                  if currNER != '':
                    ner.append(currNER.strip())
                  currNERType = token.ner
                  currNER = token.word + ' '
            if currNER != '':
              ner.append(currNER.strip())
            if len(tokens) == 0 or len(ner) == 0:
              continue
            tokens_list.append(tokens)
            ner_list.append(ner)
        return tokens_list, ner_list


def extract_np(data):
    nps = []
    for d in data:
        np = ""
        for tup in d:
            if len(np) == 0:
                np = tup[0]
            else:
                np += " "+tup[0]

        nps.append(np)

    return nps


def leaves(tree):
    #Finds NP (nounphrase) leaf nodes of a chunk tree.
    nps = []
    for subtree in tree.subtrees(filter=lambda t: t.label() == 'NP'):
        nps.append(subtree.leaves())

    return extract_np(nps)

def procDocNltkDbpedia(doc, parseTool):
  sents = nltk.sent_tokenize(doc)
  tokens_list = []
  nps_list = []
  for sent in sents:
    tokens = nltk.word_tokenize(sent)
    if len(tokens) == 0:
      continue
    if parseTool == 'nltk':
      nps = leaves(cp.parse(nltk.pos_tag(tokens)))
    else:
      nps = dbpediaParse(sent)
    if len(nps) == 0:
      continue
    tokens_list.append(tokens)
    nps_list.append(nps)
  return tokens_list, nps_list


def writeToJson(inFile, outFile, parseTool, isTrain, mentionType):
  if parseTool != 'stanford' and parseTool != 'nltk' and \
  parseTool != 'dbpedia':
    raise Exception('parse tool has to be \'stanford\' or \'nltk\'')

  grammar = r"""
   NBAR:
      {<NN.*|JJ>*<NN.*>}  # Nouns and Adjectives, terminated with Nouns
   NP:
      {<NBAR>}
      {<NBAR><IN><NBAR>}  # Above, connected with in/of/etc...
  """
  cp = nltk.RegexpParser(grammar) #chunk parser
  with open(inFile, 'r') as fin, open(outFile, 'w') as fout:
    articleId = 0
    for line in fin:
      doc = line.strip('\r\n')
      print 'Parse:', doc
      if parseTool != 'stanford':
        tokens_list, nps_list = procDocNltkDbpedia(doc, parseTool)
      else:
        parser = NLPParser()
        tokens_list, nps_list = parser.parse(doc)
        print tokens_list, nps_list

      sentId = 0
      for i in range(len(tokens_list)):
        tokens = tokens_list[i]
        nps = nps_list[i]

        sentDic = dict()
        sentDic['sentId'] = sentId
        entityMentions = []
        start = 0
        for np in nps:
          entityMention = dict()
          entityMention['text'] = np
          entityMention['label'] = 'None'
          if parseTool == 'dbpedia':
            entityMention['label'] = nps[np] # dbpedia returns the types
          entityMention['start'] = start
          entityMentions.append(entityMention)
          start += 1
        if isTrain or mentionType != 'rm':
          sentDic['entityMentions'] = entityMentions
        if not isTrain and mentionType != 'em':
          sentDic['relationMentions'] = []
          for em1 in entityMentions:
            for em2 in entityMentions:
              if em1 is not em2:
                rmDic = dict()
                rmDic['em1Text'] = em1['text']
                rmDic['em2Text'] = em2['text']
                rmDic['label'] = 'None'
                sentDic['relationMentions'].append(rmDic)

        sentDic['sentText'] = ' '.join(tokens)
        sentDic['articleId'] = articleId
        fout.write(json.dumps(sentDic) + '\n')
        sentId += 1

      articleId += 1


# Convert ./tmp1.json to pretty formatted json output.
def tmp1ToOutput(inFile, outFile):
  with open(inFile, 'r') as fin, open(outFile, 'w') as fout:
    for line in fin:
      json.dump(json.loads(line, object_pairs_hook=OrderedDict), fout, indent=4)
      fout.write('\n')


inFile = sys.argv[1]
outFile = sys.argv[2]
parseTool = sys.argv[3]
if int(sys.argv[4]) == 1:
  isTrain = True
else:
  isTrain = False
mentionType = sys.argv[5]

if isTrain: # for train.json
  entityTypesFname = sys.argv[6]
  relationTypesFname = sys.argv[7]
  freebase_dir = '/media/My Passport/freebase' # changed by yba
  print('start generating candidate entity mentions')
  writeToJson(inFile, './tmp1.json', parseTool, isTrain, mentionType)
  if parseTool == 'dbpedia':
     tmp1ToOutput('./tmp1.json', outFile)
  else:
    print('start linking to freebase')
    linkToFB('./tmp1.json', './tmp2.json', mentionType, entityTypesFname, relationTypesFname, freebase_dir)
    print('start generating negative examples')
    getNegRMs('./tmp2.json', outFile)
else: # for test.json
  writeToJson(inFile, outFile, parseTool, isTrain, mentionType)
  if parseTool == 'dbpedia':
     tmp1ToOutput('./tmp1.json', outFile)

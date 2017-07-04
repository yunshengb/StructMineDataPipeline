import json, requests, urllib
from collections import OrderedDict

def dbpediaParse(sent):
  data = { 'text' : sent, 'confidence' : 0} # change the confidence threshold
  url = 'http://model.dbpedia-spotlight.org/en/candidates?%s' % \
  urllib.urlencode(data)
  headers = {'Content-type': 'application/x-www-form-urlencoded', \
  'Accept': 'application/json'}
  r = requests.post(url, headers=headers)
  if not r.ok:
     raise RuntimeError(r.reason)
  return getNes(json.loads(r.text), sent)

def getNes(r, sent):
  print '*'*50
  print json.dumps(r, indent=4, sort_keys=True)
  r = r['annotation']
  assert(r['@text'] == sent)
  r = r['surfaceForm']
  nes = OrderedDict()
  for x in r:
    name = x['@name']
    if isinstance(x['resource'], list):
      for y in x['resource']:
        addTypesToNes(nes, name, y['@types'])
    else:
      addTypesToNes(nes, name, x['resource']['@types'])
  print nes
  print '*'*50
  return nes

def addTypesToNes(nes, name, types):
  if types:
    for type in types.split(','):
      addToDictValIsList(nes, name, type.strip()) # record score???????? for now, aim for recall
  else: # empty string
    pass # go to dbpedia to find supertype.....................................

def addToDictValIsList(d, k, v):
  if k in d and not v in d[k]:
    d[k].append(v)
  else:
    d[k] = [v]


if __name__ == '__main__':
  print dbpediaParse('Obama was in Hawaii.')

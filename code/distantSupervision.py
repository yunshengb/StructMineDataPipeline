import json
import random
import pickle
import os.path

def load(fname):
  with open(fname, 'rb') as handle:
    return pickle.load(handle)

def save(fname, obj):
  with open(fname, 'wb') as handle:
    pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)  

def loadTargetTypes(filename):
  map = {}
  with open(filename, 'r') as fin:
    for line in fin:
      # seg = line.strip('\r\n').split('    ') # changed by yba
      # fbType = seg[0]
      # cleanType = seg[1]
      seg = line.strip('\r\n') # changed by yba
      fbType = seg
      cleanType = seg.upper()
      map[fbType] = cleanType
  return map

def linkToFB(jsonFname, outFname, mentionTypeRequired, entityTypesFname, relationTypesFname, freebase_dir):
  mid2typeFname = freebase_dir+'/freebase-mid-type.map'
  mid2nameFname = freebase_dir+'/freebase-mid-name.map'
  relationTupleFname = freebase_dir+'/freebase-facts.txt'

  mid2types = {}
  name2mids = {}
  mids2relation = {}


  targetEMTypes = loadTargetTypes(entityTypesFname)#{'<http://rdf.freebase.com/ns/people.person>':'PERSON', '<http://rdf.freebase.com/ns/organization.organization>':'ORGANIZATION', '<http://rdf.freebase.com/ns/location.location>':'LOCATION'}
  print targetEMTypes['medicine.symptom']

  if os.path.isfile('mid2types'):
    print 'loading mid2types'
    mid2types = load('mid2types')
  else:
    with open(mid2typeFname, 'r') as mid2typeFile:
      for line in mid2typeFile:
        seg = line.strip('\r\n').split('\t')
        mid = seg[0]
        type = seg[1].split('/')[-1][:-1]
        if type in targetEMTypes:
          if mid in mid2types:
            mid2types[mid].add(targetEMTypes[type])
          else:
            mid2types[mid] = set([targetEMTypes[type]])
    save('mid2types', mid2types)
  print('finish loading mid2typeFile')
  # print '!'*100, mid2types['http://rdf.freebase.com/ns/m.0672fwp>']


  if mentionTypeRequired != 'em':
    targetRMTypes = loadTargetTypes(relationTypesFname)
    if os.path.isfile('mids2relation'):
      print 'loading mids2relation'
      mids2relation = load('mids2relation')
    else:
      with open(relationTupleFname, 'r') as relationTupleFile:
        for line in relationTupleFile:
          seg = line.strip('\r\n').split('\t')
          mid1 = seg[0]
          type = seg[1].split('/')[-1][:-1]
          mid2 = seg[2]
          if type in targetRMTypes and mid1 in mid2types and mid2 in mid2types:
            key = (mid1, mid2)
            if key in mids2relation:
              mids2relation[key].add(targetRMTypes[type])
            else:
              mids2relation[key] = set([targetRMTypes[type]])
      save('mids2relation', mids2relation)
    print('finish loading relationTupleFile')

    if os.path.isfile('name2mids'):
      print 'loading name2mids'
      name2mids = load('name2mids')
    else:
      with open(mid2nameFname, 'r') as mid2nameFile:
        for line in mid2nameFile:
          seg = line.strip('\r\n').split('\t')
          mid = seg[0]
          name = seg[1].lower()
          if 'diabetes' in name:
            print '#'*10, line
          if mid in mid2types and name.endswith('@en'):
            name = name[1:].replace('"@en', '')
            if name == 'diabetes':
              print '$'*10, line
            if name in name2mids:
              name2mids[name].add(mid)
            else:
              name2mids[name] = set([mid])
      save('name2mids', name2mids)
    print('finish loading mid2nameFile')


  with open(jsonFname, 'r') as fin, open(outFname, 'w') as fout:
    linkableCt = 0
    for line in fin:
      sentDic = json.loads(line.strip('\r\n'))
      entityMentions = []
      em2mids = {}
      for em in sentDic['entityMentions']:
        emText = em['text'].lower()
        types = set()
        if emText in name2mids:
          linkableCt += 1
          mids = name2mids[emText]
          em2mids[(int(em['start']), em['text'])] = set(mids)
          for mid in mids:
            types.update(set(mid2types[mid]))
          em['label'] = ','.join(types)
        if len(types) > 0:
          entityMentions.append(em)
      sentDic['entityMentions'] = entityMentions

      if mentionTypeRequired != 'em':
        sentDic['relationMentions'] = []
        for (eid1, e1text) in em2mids:
          for (eid2, e2text) in em2mids:
            if eid2 != eid1:
              rmDic = dict()
              rmDic['em1Text'] = e1text
              rmDic['em2Text'] = e2text
              labels = set()
              for mid1 in em2mids[(eid1, e1text)]:
                for mid2 in em2mids[(eid2, e2text)]:
                  if (mid1, mid2) in mids2relation:
                    labels.update(set(mids2relation[(mid1, mid2)]))
              if len(labels) > 0:
                rmDic['label'] = ','.join(labels)
                sentDic['relationMentions'].append(rmDic)

      if mentionTypeRequired == 'rm':
        del sentDic['entityMentions']

      fout.write(json.dumps(sentDic) + '\n')


def getNegRMs(jsonFname, outputFname):
  with open(jsonFname, 'r') as fin, open(outputFname, 'w') as fout:
    for line in fin:
      sentDic = json.loads(line.strip('\r\n'))
      rms = set()
      ems = set()
      newRms = []
      relationMentions = []
      for em in sentDic['entityMentions']:
        ems.add(em['text'])
      for rm in sentDic['relationMentions']:
        relationMentions.append(rm)
        rms.add(frozenset([rm['em1Text'], rm['em2Text']]))
      for em1 in ems:
        for em2 in ems:
          if em1 != em2:
            if frozenset([em1, em2]) not in rms:
              newRm = dict()
              newRm['em1Text'] = em1
              newRm['em2Text'] = em2
              newRm['label'] = 'None'
              newRms.append(newRm)
              rms.add(frozenset([em1, em2]))
          #break

      for rm in newRms:
        relationMentions.append(rm)
      if len(relationMentions) > 0:
        sentDic['relationMentions'] = relationMentions
        fout.write(json.dumps(sentDic)+'\n')

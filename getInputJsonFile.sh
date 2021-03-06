inTestFile='./data/test.txt'
inTrainFile='./data/documents.txt'
mentionType='both' #'em' or 'rm' or 'both'
emTypeMapFile='./data/emTypeMap.txt'
rmTypeMapFile='./data/rmTypeMap.txt'
outTrainFile='./data/train.json'
outTestFile='./data/test.json'
parseTool='dbpedia' #'nltk' or 'stanford' or 'dbpedia'
testOnly=false
freebaseDir='/media/My Passport/freebase'

if [ "$testOnly" = false ] ; then
  echo 'start generating train json file'
  python code/generateJson.py $inTrainFile $outTrainFile $parseTool 1 $mentionType $emTypeMapFile $rmTypeMapFile $freebaseDir

  echo 'No removing tmp files... !!!!!!!!!!!!!!!!!1'
  # rm tmp1.json
  # rm tmp2.json
fi

echo 'start generating test json file'
python code/generateJson.py $inTestFile $outTestFile $parseTool 0 $mentionType

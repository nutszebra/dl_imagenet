import re
import os
import json
import subprocess
import time
from datetime import datetime

from pymongo import MongoClient
client = MongoClient()
db = client['dlconvert']
dbTag = client['tag']
dbError = client['error']
dbConversion = client['conversion']

base = "/mnt/s3/crawler/"
source = [source for source in os.listdir(base) if source !="foodiesfeed"]

baseLog = "./tagLog/"
log = []

picBase = "/mnt/s3/pic/"

conversions = [conversion for conversion in os.listdir(picBase) if conversion !="original"]

for folder in source:
  print('********************************************************')
  print('start: ' + folder)
  print('********************************************************')
  col = db[folder]
  colTag = dbTag[folder]
  colError = dbError[folder]
  
  colTag.delete_many({})
  colError.delete_many({})

  position = base + folder + '/'
  files = os.listdir(position)

  for jsonFile in files:
    data = json.load(open(base + folder + '/' + jsonFile))
    if folder == "pexels":
      data['url'] = data['url'][0]

    if len(data['tag'])==0:
      print("No tag in this file:")
      print(jsonFile)
      print(data['url'])
      print(data['tag'])
      item = {}
      item['jsonFile'] = base + folder + '/' + jsonFile
      item['url'] = data['url']
      log.append(item)
      colTag.insert_one({'json': item['jsonFile']})

    if col.find({'json': jsonFile}).count():
      print('already downloaded:' + jsonFile)
    else:
      try:
        cmd='wget --content-disposition '  + data['url']
        print('start downloading:' + jsonFile)
        subprocess.call(cmd,shell=True)
        picName = [pic for pic in os.listdir('./') if re.findall(r'jpg|png|jpeg|PNG|JPG|JPEG',pic)][0]
        extension = re.findall(r'jpg|png|jpeg|PNG|JPG|JPEG',picName)[0]
        newFileName = jsonFile.replace('json',extension)
        cmd='mv ./'  + picName + ' ' + picBase + 'original/' + folder + '/' + newFileName
        subprocess.call(cmd,shell=True)
        time.sleep(2)
        for conversion in conversions:
          picPath = picBase + 'original/' + folder + '/' + newFileName
          convertPath = picBase + conversion + '/' + folder + '/' + newFileName.replace('png','jpg').replace('PNG','jpg')
          colConversion = dbConversion["conversion" + conversion]
          if colConversion.find({'path': picPath}).count():
            print('already converted:' + picPath)
          else:
            print('start converting:' + convertPath)
            cmd ="convert " + picPath + " -strip -unsharp 2x1.4+0.5+0 -colors 65 -quality 95 -resize " + conversion + "x "  + convertPath
            subprocess.call( cmd, shell=True  )
            colConversion.insert_one({'path': picPath})
        col.insert_one({'json': jsonFile})
      except:
        colError.insert_one({'error': picBase + folder + "/" + jsonFile})
with open(baseLog + datetime.now().strftime('%s')+".json", 'w') as outfile:
  json.dump(log, outfile)

# -*- coding: utf-8 -*-
import asyncio
import re
from PIL import Image
import os
import json
import subprocess
import time
import overwrite
from datetime import datetime
import hashlib
import threading

from PIL import ImageFile
#To ensure that *.png file are read
ImageFile.LOAD_TRUNCATED_IMAGES = True

#how to use imagenet api: http://image-net.org/download-API

#base url
#put pictures beneath this path
basePic = "/mnt/s3/imagenet/categorize/"
#put urls beneath this path
baseUrl = "/mnt/s3/imagenet/urls/"


#download synset_list
#download pictures of those ids
if not "imagenet.synset.obtain_synset_list" in os.listdir("./"):
  print("downloading synset_list...")
  cmd ="wget http://www.image-net.org/api/text/imagenet.synset.obtain_synset_list -q"
  subprocess.call(cmd, shell=True)
else:
  print("synset_list have been downloaded...")


#download words.txt
#the association of ids and tags
if not "words.txt" in os.listdir("./"):
  print("downloading the table about ids and tags...")
  cmd ="wget http://image-net.org/archive/words.txt -q"
  subprocess.call(cmd, shell=True)
else:
  print("the tabel about ids and tags has been downloaded...")

def storeToArray(name):
  answer = []
  f = open(name)
  for line in f.readlines():
    shape = line.split()
    if len(shape):
      answer.append(shape[0])
  f.close()
  return answer

def storeToDictionary(name):
  answer = {}
  f = open(name)
  for line in f.readlines():
    shape = line.split()
    if len(shape):
      answer[shape[0]] = [re.sub("^\s+","",re.sub(r"\n$","",word)) for word in line.split("\t")[1].split(",")]   
  f.close()
  return answer

print("storing words....")
words = storeToDictionary("./words.txt")
print("storing synset list....")
synset = storeToArray("./imagenet.synset.obtain_synset_list")

#obtain url
#put image id at the end
apiUrl = "http://www.image-net.org/api/text/imagenet.synset.geturls?wnid="

files = [re.sub(r"\.txt$", "", name) for name in os.listdir(baseUrl) if re.findall(r"\.txt$",name)]
setSynset = set(synset)
fileUrl = list(setSynset.difference(set(files)))

#get all urls
numId = len(synset)
count = numId - len(fileUrl)
print("getting all urls....")
for picId in fileUrl:
  count = count + 1
  sen = overwrite.bar(count, numId)
  sen = sen + " " + str(picId)
  overwrite.overwrite(sen)
  cmd = "wget " + apiUrl + picId + " -O tmp -q"
  subprocess.call(cmd, shell=True)
  cmd = "mv tmp " + baseUrl + picId + ".txt"
  subprocess.call(cmd, shell=True)
print("urls are all prepared!")

def checkExistance(path):
  if os.path.exists(path):
    return True
  else:
    return False

def makeDirectory(path):
  if not checkExistance(path):
    os.makedirs(path)

def downloadPic(url, name):
  cmd = "wget " + url + " -O " + name + " -q"
  subprocess.call(cmd, shell=True)

def extractExtension(name):
  possibility = ["jpg", "Jpg", "JPG", "JPEG", "jpeg", "PNG", "png", "Png"]
  result = [extension for extension in possibility if name.rfind(extension) > 0]
  if len(result):
    return result[0]
  else:
    return ""

def moveFile(path, name):
  cmd = "mv " + name + " " + path
  subprocess.call(cmd, shell=True)

def writeToFile(arr, path):
  f=open(path, "w")
  for line in arr:
    f.write(line + "\n")
  f.close()

class Command(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None

    def run(self, timeout):
        def target():
            self.process = subprocess.Popen(self.cmd, shell=True)
            self.process.communicate()
        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            self.process.terminate()
            thread.join()
        return self.process.returncode

@asyncio.coroutine
def downloadUrl(url, dirPath):
  try:
    extension = extractExtension(url)
    name = hashlib.sha224(unicode(url, errors="ignore").encode('utf8')).hexdigest() + "." + extension
    picName = dirPath + "/" + name
    if not checkExistance(picName):
      if not len(extension):
        raise ValueError('extension is blank')
      cmd = "wget " + url + " -O " + "./" + name + " -q"
      command = Command(cmd)
      command.run(timeout = 10)
      #verify whether it's not broken or not
      tmp = Image.open("./" + name)
      tmp.verify()
      #tmp.load_end()
      #if picture is too small, raise error
      if tmp.size[0] * tmp.size[1] <= 50 * 50:
        raise ValueError('picture is too small')
      moveFile(picName, "./" + name)
  except:
    if os.path.exists("./" + name):
      cmd = "rm ./" + name
      subprocess.call(cmd, shell=True)


count = 0
picCount = 0
asyncNum = 0
taskNum = 100
numPic = len(files)
loop = asyncio.get_event_loop()

for f in files:
  count = count + 1
  dirPath = basePic + f
  makeDirectory(dirPath)
  urls = storeToArray(baseUrl + f + ".txt")
  senBar = overwrite.bar(count, numPic)
  sen = senBar + " " + f + " ****number of pic: " + str(picCount)
  overwrite.overwrite(sen)
  tasks = []
  for url in urls:
    tasks.append(
    asyncio.ensure_future(downloadUrl(url, dirPath))
    )
    asyncNum = asyncNum + 1
    picCount = picCount + 1
    if asyncNum >= taskNum:
      sen = senBar + " " + f + " ****number of pic: " + str(picCount)
      overwrite.overwrite(sen)
      loop.run_until_complete(asyncio.wait(tasks))
      asyncNum = 0
      tasks = []
  if len(tasks):
    loop.run_until_complete(asyncio.wait(tasks))
    asyncNum = 0
    tasks = []

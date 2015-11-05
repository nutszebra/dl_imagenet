import re
import os
import json
import subprocess
import time
from datetime import datetime

#how to use imagenet api: http://image-net.org/download-API

#base url
#put files beneath this path
base = "/mnt/s3/imagenet/categorize/"

#obtain url
#put image id at the end
apiUrl = "http://www.image-net.org/api/text/imagenet.synset.geturls?wnid="

#download synset_list
#download pictures of those ids
if not "imagenet.synset.obtain_synset_list" in os.listdir("./"):
  print("downloading synset_list...")
  cmd ="wget http://www.image-net.org/api/text/imagenet.synset.obtain_synset_list"
  subprocess.call(cmd, shell=True)

#download words.txt
#the association of ids and tags
if not "words.txt" in os.listdir("./"):
  print("downloading the table about ids and tags...")
  cmd ="wget http://image-net.org/archive/words.txt"
  subprocess.call(cmd, shell=True)

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

words = storeToDictionary("./words.txt")
synset = storeToArray("./imagenet.synset.obtain_synset_list")


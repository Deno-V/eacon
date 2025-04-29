import argparse
parser = argparse.ArgumentParser(description=".")  
parser.add_argument('--fs', action='store_true', help='FEVEROUS-S')
args = parser.parse_args()
fs = args.fs

evidencecnt = 0
evidenceprocessed = 0
deleteevidence = 0

badkey = 0

inputfile = "../testdata/dev_vicunaextract.json"
outputfile = "../testdata/dev_vicunaextract_filtered.json"
if fs:
    inputfile = "../testdata/fsdev_vicunaextract.json"
    outputfile = "../testdata/fsdev_vicunaextract_filtered.json"

introwords = ['summary:','would be:','the summary of the input text is:','summarize as follows:','summary is:','summary could be','summary will be',"input states that"]
denyingwords = ["no information", "no specific", "not mention","not provide","for the given input","no direct","provided input","no mention","provided in the input","in the provided input","a summary based","no details about","mentioned in the input","not include","not specify",'not directly','directly relate',"input specifie","related information in the input","not specifically named in the input","direct connection to","keywords specify","no factual summary","were used to extract","is correct","is incorrect","no relevant summary","mentioned in the input"]
stopwords = ['not possible',"no relevant information in the input","not provide information","no relevant information to summarize","do not appear in the input"]
cntstopwords = ['input:','keywords:']
deleteafter = ['the providedsummary includes the keywords:','summay based on the provided keyword','the summary includes the key information directly related to the keyword','the summary includes the keyword','the summary includes the specified keywords','summary based on the provided keywords','the provided summary includes the keyword','keywords:']
def remove_unmatched_parentheses(s):
    stack = []
    remove_index = set()

    # 遍历字符串，使用栈找出所有不匹配的括号的位置
    for i, char in enumerate(s):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if stack:
                stack.pop()
            else:
                remove_index.add(i)

    # 把未匹配的左括号的位置也加入到删除集合中
    remove_index.update(stack)

    # 构建新的字符串，排除所有在删除集合中的字符
    new_string = ''.join([char for i, char in enumerate(s) if i not in remove_index])
    return new_string

def checkkey(key):
    key = key.lower()
    if key.count('input:')>3 or 'user 0' in key:
        return False
    return True


def processone(evidenceandmeta):
    global evidencecnt,evidenceprocessed,deleteevidence
    evidence,meta = evidenceandmeta
    orievidence = evidence
    # check for cntstopwrods
    evidencelower = evidence.lower()
    for w in cntstopwords:
        if evidencelower.count(w)>3:
            evidence = ''
            break
    if evidence != '':
        # try to prune before intro words
        evidencelower = evidence.lower()
        for w in introwords:
            wpos = evidencelower.rfind(w)
            if wpos == -1:
                continue
            evidence = evidence[wpos+len(w):]
            break
        # check for deleteafter
        evidencelower = evidence.lower()
        for w in deleteafter:
            wpos = evidencelower.find(w)
            if wpos == -1:
                continue
            evidence = evidence[:wpos]
            break
        # try delete sentence with denying
        evidencesplit = evidence.split('.')
        for spliti in range(len(evidencesplit)):
            tocheck = evidencesplit[spliti].lower()
            for w in denyingwords:
                if w not in tocheck:
                    continue
                evidencesplit[spliti] = None
                break
        evidencesplit = [i for i in evidencesplit if i is not None]
        # check for stopwords
        if len(evidencesplit) == 0:
            evidence = ''
        else:
            evidence = '.'.join(evidencesplit)
        for w in stopwords:
            if w in evidence.lower():
                evidence = ''
                break
    # statistic
    evidencecnt += 1
    if evidence != orievidence:
        evidenceprocessed += 1
    if evidence=='':
        deleteevidence += 1
    # ouput
    if evidence == '':
        return None
    else:
        evidence = remove_unmatched_parentheses(evidence)
        return [evidence,meta]


import json
from copy import deepcopy as dp


f = open(inputfile,'r')
source = [json.loads(i.strip()) for i in f.readlines() if len(i)>3]
f.close()

filtered = []

for example in source:

    add_evidence = dp(example['add_evidence'])
    new_add_evidence= []
    if checkkey(example['claimkey']):
        for add_e_i in add_evidence:
            new_e_i = processone(add_e_i)
            if new_e_i is not None:
                new_add_evidence.append(new_e_i)
    else:
        example['claimkey'] = ''
        deleteevidence += len(add_evidence)
        badkey += 1
    example['add_evidence'] = new_add_evidence
    filtered.append(example)

f = open(outputfile,'w')
f.close()
f = open(outputfile,'a')
for i in filtered:
    f.write(json.dumps(i) + '\n')
f.close()

print(evidencecnt,evidenceprocessed,deleteevidence,badkey)









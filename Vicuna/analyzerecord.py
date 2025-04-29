import argparse
parser = argparse.ArgumentParser(description=".")  
parser.add_argument('--fs', action='store_true', help='FEVEROUS-S')
args = parser.parse_args()
fs = args.fs

filename = 'VicunaOutputRecord.txt'
if fs:
    filename = 'fsVicunaOutputRecord.txt'
    

with open(filename) as f:
    x = f.readlines()
limitnum = 20000
x = [i.strip() for i in x]
labels = []
predicts = []
hops = []

from util import eval_hover_results
for i in x:
    if i.startswith('Label:'):
        if 'True' in i:
            labels.append(True)
        else:
            labels.append(False)
    elif i.startswith('Hop:'):
        hops.append(int(i.replace('Hop: ','')))
    elif i.startswith('['):
        p = eval(i)
        if False in p:
            predicts.append(False)
        else:
            predicts.append(True)
if not fs:
    print(eval_hover_results(predicts[:limitnum],labels[:limitnum],hops[:limitnum]))
else:
    print(eval_hover_results(predicts[:limitnum],labels[:limitnum],[2]*min(len(predicts),limitnum)))
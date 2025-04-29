import argparse
parser = argparse.ArgumentParser(description=".")  
parser.add_argument('--fs', action='store_true', help='FEVEROUS-S')
args = parser.parse_args()
fs = args.fs

from util import *
from functools import partial
from mixtral_client_util import *
import json
import random
import re

    
DividerDuty = """
Task Description: Dissect a given claim into multiple atomic statements. These statements should be complete in meaning, devoid of uncertain pronouns, and retain all original details. Each atomic statement should stand alone and be independently verifiable.

Examples:

Claim: Howard University Hospital and Providence Hospital are both located in Washington, D.C.
Output: \n #1 Howard University Hospital is located in Washington, D.C. \n #2 Providence Hospital is located in Washington, D.C.

Claim: WWE Super Tuesday took place at Fleet Center. Fleet Center currently goes by the name TD Garden.
Output: \n #1 WWE Super Tuesday took place at Fleet Center. \n #2 Fleet Center currently goes by the name TD Garden.

Claim: Talking Heads, an American rock band that was "one of the most critically acclaimed bands of the 80's" is featured in KSPN's AAA format.
Output: \n #1 Talking Heads is an American rock band that was 'one of the most critically acclaimed bands of the 80's'. \n #2 Talking Heads is featured in KSPN's AAA format.

Claim: An IndyCar race driver drove the Super Aguri F1 SA07 during the 2007 Formula One season. The Super Aguri F1 SA07 was designed by Peter McCool.
Output: \n #1 An IndyCar race driver drove the Super Aguri F1 SA07 during the 2007 Formula One season. \n #2 The Super Aguri F1 SA07 was designed by Peter McCool.

Claim: Gina Bramhill was born in Eastoft. The 2011 population of the area that includes Eastoft was 167,446.
Output: \n #1  Gina Bramhill was born in Eastoft. \n #2 The 2011 population of the area that includes Eastoft was 167,446.

Claim: Colson Whitehead has won less than three Pulitzer Prizes.
Output: \n #1 Colson Whitehead has won less than three Pulitzer Prizes.

Claim: Don Ashley Turlington graduated from Saint Joseph's College, a private Catholic liberal arts college in Standish.
Output: \n #1 Saint Joseph's College is a private Catholic liberal arts college is located in Standish. \n #2 Don Ashley Turlington graduated from Saint Joseph's College.

Claim: Fitness is not published in Belgium.
Output: \n #1 Fitness is not published in Belgium.

Claim: Blackstar is the name of the album released by David Bowie that was recorded in secret.
Output: \n #1 David Bowie released an album called Blackstar. \n #2 David Bowie released an album called Blackstar.

Claim: In the 2004 Hockey film named Miracle produced by a former major league baseball pitcher Kurt Russell played the USA coach.
Output: \n #1 Miracle is a 2004 Hockey film produced by a former major league baseball pitcher. \n #2 Kurt Russell played the USA coach in the film Miracle.

Claim: Along with the New York Islanders and the New York Rangers, the New Jersey Devils NFL franchise is popular in the New York metropolitan area.
Output: \n #1 The New York Islanders and the New York Rangers are popular in the New York metropolitan area. \n #2 The New Jersey Devils NFL franchise is popular in the New York metropolitan area.

Claim: The song recorded by Fergie that was produced by Polow da Don and was followed by Life Goes On was M.I.L.F.$.
Output: \n #1 M.I.L.F.$ was recorded by Fergie that was produced by Polow da Don. \n #2 M.I.L.F.$ was was followed by Life Goes On.

Claim: Jack McFarland is the best known role of Sean Patrick Hayes.
Output: \n #1 Jack McFarland is the best known role of Sean Patrick Hayes.

Claim: Gregg Rolie and Rob Tyner, are not a keyboardist.
Output: \n #1 Gregg Rolie is not a keyboardist. \n #2 Gregg Rolie is not a keyboardist.

Claim: Maria Esther Andion Bueno, not Jimmy Connors, is the player that is from Brazil.
Output: \n #1 Maria Esther Andion Bueno is from Brazil. \n #2 Maria Esther Andion Bueno is from Brazil.

Claim: Georg Cantor died before 3 June 2010.
Output: \n #1 Georg Cantor died before 3 June 2010.

Claim: Ford Fusion was introduced for model year 2006. Patrick Carpentier drives Ford Fusion in the NASCAR Sprint Cup.
Output: \n #1 Ford Fusion was introduced for model year 2006. \n #2 Patrick Carpentier drives Ford Fusion in the NASCAR Sprint Cup.

Claim: Barton Mine was halted by a natural disaster not Camlaren Mine.
Output: \n #1 Barton Mine was halted by a natural disaster. \n #2 Camlaren Mine was not halted by a natural disaster.

Here is the claim given to you. Your answer should follow the format of above demonstrations. Each atomic statement should stand alone and be independently verifiable with as least pronouns as possible. Give your answer only, no explanation.
Claim: {claim}
Output:
""" 

def setlow():
    f.write('set T low\n')
    api.set_arg_t(0.05)

def easy_verify(atomicclaim,claim,evidence):
    ret = api.send_message(format_chat(['','Given golden evidence:{evidence}.\n In the saying of {claim}. Based on the golden evidence. Is it true that {atomicclaim}? (Answer with Yes or No)'.format(evidence=evidence,claim=claim,atomicclaim=atomicclaim)]))
    ret = ret.lower()
    if 'yes' in ret:
        return True
    else:
        return False

def easy_verifyfs(atomicclaim,claim,evidence):
    ret = api.send_message(format_chat(['','Given golden evidence:{evidence}.\n Based on the golden evidence. Is it true that {atomicclaim}? (Answer with Yes or No)'.format(evidence=evidence,claim=claim,atomicclaim=atomicclaim)]))
    ret = ret.lower()
    if 'yes' in ret:
        return True
    else:
        return False
    
if fs:
    easy_verify = easy_verifyfs

def parse_divider(ret):
    ret = ret.strip().split('\n')
    ret = [k[2:] for k in ret if not k.lower().startswith('output')]
    ret = [k for k in ret if (len(k)>10) and not ('not mention' in k)]
    return ret

def round(claim,evidence,atomic_claims):
    setlow()
    claim = strip_last_stop(claim)
    goldenEvidence = evidence
    if atomic_claims is None:
        api.set_arg_max_new_tokens(999)
        DividerResponse = api.send_message(format_chat(['',DividerDuty.format(claim=claim)]))
        atomic_claims = parse_divider(DividerResponse)
    f.write('# Divider: '+str(atomic_claims) +'\n')
    verify_results = []
    api.set_arg_max_new_tokens(30)
    for at in atomic_claims:
        tmp = easy_verify(at,claim,goldenEvidence)
        verify_results.append(tmp)
        if not tmp:
            break
    f.write(str(verify_results)+'\n')
    return verify_results



format_chat = format_mixtral_chat_input
if not fs:
    dataset = load_hover_dataset(path='../testdata/dev_mixtralextract_filtered.json')
else:
    dataset = load_fs_dataset(path='../testdata/fsdev_mixtralextract_filtered.json')
api = get_api(arg_t=0.05)
api.set_arg_max_new_tokens(999)


import random
xxxx = list(range(len(dataset)))
random.seed(23)
random.shuffle(xxxx)
num = len(xxxx)



def combineevidence(evidence,addevidence):
    evidencesplit = evidence.split('\n')
    combined = []
    for em in addevidence:
        e,m = em
        combined.append(e)
    for e in evidencesplit:
        combined.append(e)
    return strip_last_stop(' '.join([ '('+str(i+1)+') ' + e.strip() for i,e in enumerate(combined)]))


cnt = 0
for id in xxxx:
    example = dataset[id]
    label = example['label']
    label = False if label=='refutes' else True
    if not fs:
        hop = example['num_hops']
    cnt += 1
    claim = example['claim']
    evidence = example['evidence'].replace('\"','\'')
    addevidence = example['add_evidence']
    evidence = combineevidence(evidence,addevidence)
    if not fs:
        f = open('MixtralOutputRecord.txt','a')
    else:
        f = open('fsMixtralOutputRecord.txt','a')
    f.write('*'*30+'\n')
    f.write('id:'+str(id)+'\n')
    f.write('  Claim: '+claim+'\n')
    f.write('  Evidence: '+evidence+'\n')
    f.write('  Label: '+str(label)+'\n')
    if not fs:
        f.write('  Hop: '+str(hop)+'\n')
    f.write('-'*20+'\n')
    print(label,end= '  ')
    atomic_results = round(claim,evidence,None)
    f.close()
    print('--')
    
api.disconnect()













import argparse
parser = argparse.ArgumentParser(description=".")  
parser.add_argument('--fs', action='store_true', help='FEVEROUS-S')
args = parser.parse_args()
fs = args.fs

from functools import partial
from util import *
import json
import random
##########################################################
# config server
from mixtral_client_util import *
format_chat = format_mixtral_chat_input
outputfile = "../testdata/dev_mixtralextract.json"
if fs:
    outputfile = "../testdata/fsdev_mixtralextract.json"

arg_t = 0.05
arg_max_new_tokens = 1000
api = get_api(arg_t=arg_t,arg_max_new_tokens=arg_max_new_tokens,server_debug=False)
###########################################################

keywordsprompt = """
Task Description: Extract key components such as important verbs, nouns, and phrases from the provided sentence. Focus on identifying and highlighting the most relevant elements.

Instructions:

Carefully read the input sentence.
Identify and list the significant verbs, nouns, and pertinent phrases.
Ensure the output succinctly encapsulates the essence of the input by focusing on these key components.
Examples:

Input: Howard University Hospital and Providence Hospital are both located in Washington, D.C.
Output: Howard University Hospital, Providence Hospital, located, Washington, D.C.

Input: WWE Super Tuesday took place at an arena that currently goes by the name TD Garden.
Output: WWE Super Tuesday, took place, name, TD Garden.

Input: Talking Heads, an American rock band that was "one of the most critically acclaimed bands of the 80's," is featured in KSPN's AAA format.
Output: Talking Heads, bands of the 80's, KSPN's AAA format.

Input: An IndyCar race driver drove a Formula 1 car designed by Peter McCool during the 2007 Formula One season.
Output: IndyCar race driver, Formula 1 car, design, Peter McCool, 2007 Formula One season.

Input: Gina Bramhill was born in a village. The 2011 population of the area that includes this village was 167,446.
Output: Gina Bramhill, born, village, 2011 population.

Input: Don Ashley Turlington graduated from Saint Joseph's College, a private Catholic liberal arts college in Standish.
Output: Don Ashley Turlington, graduate, Saint Joseph's College, private Catholic liberal arts college, Standish.

Input: Gael and Fitness are not published in the same country.
Output: Gael, Fitness, publish, country.

Input: Blackstar is the name of the album released by David Bowie that was recorded in secret.
Output: Blackstar, album, David Bowie, secret.

Input: In the 2004 Hockey film produced by a former major league baseball pitcher, Kurt Russell played the USA coach.
Output: 2004 Hockey film, former major league baseball pitcher, Kurt Russell, USA coach.

Input: Along with the New York Islanders and the New York Rangers, the New Jersey Devils NFL franchise is popular in the New York metropolitan area.
Output: New York Islanders, New York Rangers, New Jersey Devils NFL franchise, popular, New York metropolitan area.

Input: Jack McFarland is the best known role of the host of the 64th Annual Tony Awards.
Output: Jack McFarland, host, 64th Annual Tony Awards.

Input: The song recorded by Fergie that was produced by Polow da Don and was followed by Life Goes On was M.I.L.F.$.
Output: song, produced, Fergie, Polow da Don, followed, Life Goes On, M.I.L.F.$.

Input: Eatza Pizza and Your Pie were not founded in the same state.
Output: Eatza Pizza, Your Pie, founded, state.

Input: Gregg Rolie and Rob Tyner, are not a keyboardist.
Output: Gregg Rolie, Rob Tyner, keyboardist.

Input: Maria Esther Andion Bueno, not Jimmy Connors, is the player that is from Brazil.
Output: Maria Esther Andion Bueno, player, Brazil, Jimmy Connors.

Input: Vladimir Igorevich Arnold died after Georg Cantor.
Output: Vladimir Igorevich Arnold, died, Georg Cantor.

Input: Barton Mine was halted by a natural disaster, not Camlaren Mine.
Output: Barton Mine, halted, natural disaster, Camlaren Mine.

Input: John O'Hara and Rabindranath Tagore are not the same nationality.
Output: John O'Hara, Rabindranath Tagore, nationality.

Input: Thomas Loren Friedman has won more Pulitzer Prizes than Colson Whitehead.
Output: Thomas Loren Friedman, won, Pulitzer Prizes, Colson Whitehead.

Input: The model of car Trevor Bayne drives was introduced for model year 2006. The Rookie of The Year in the 1997 CART season drives it in the NASCAR Sprint Cup.
Output: The model of car, Trevor Bayne, drives, introduced, model year 2006, NASCAR Sprint Cup, Rookie of The Year, 1997 CART season.

Based on the following input, identify and list the key components as demonstrated in the examples.

Input: [claim]
Output:
"""

extractprompt = """
Task Description: Extract and summarize key information from sentences based on specified keywords. The output should be concise, directly related to the keywords, and devoid of extraneous details.

Instructions:
Carefully read the provided input sentence.
Use the specified keywords to guide your extraction of information.
Generate a summary that includes only the facts directly associated with the keywords.

Examples:

Input: Providence Hospital is a 408 bed hospital located in the District of Columbia. Founded in 1861, it is the longest continuously operating hospital in the District. Providence Hospital is a member of Ascension Health, the largest non-profit health care organization in the United States.
Keywords: Providence Hospital, located, Washington, D.C.
Output: Providence Hospital is located in Washington, D.C.

Input: TD Garden, often called Boston Garden and "The Garden", is a multi-purpose arena in Boston, Massachusetts. It is named after its sponsor, TD Bank, a subsidiary of Canada's Toronto-Dominion Bank. It opened in 1995 as a replacement for the original Boston Garden and has been known as Shawmut Center, FleetCenter, and TD Banknorth Garden. The arena is located directly above the MBTA's North Station.
Keywords: name, TD Garden.
Output: TD Garden, also known as Boston Garden, is named after TD Bank.

Input: "Life Goes On" is a song recorded by American singer Fergie for her second studio album, "Double Dutchess" (2017). It was released as a single on November 11, 2016, by Interscope and will.i.am Music Group. The song serves as the third single from Fergie's second studio album, following "M.I.L.F. $". "Life Goes On" was written by Fergie, Tristan Prettyman, Keith Harris and Toby Gad.
Keywords: song, Fergie, followed, Life Goes on, M.I.L.F.$.
Output: "Life Goes On" is a song by Fergie following "M.I.L.F. $".

Input: KSPN-FM is an adult album alternative radio station owned by Patricia MacDonald Garber and Peter Benedetti, through licensee AlwaysMountainTime, LLC, and broadcasts at 103.1 MHz FM in the Aspen, Colorado area. The station airs an adult album alternative format and uses the slogan "The Valley's Quality Rock". With over 30 years of Quality Rock experience, this heritage station is the Roaring Fork Valley's favorite among both locals and tourists. KSPN covers all community and national events in the area: World Cup Championships, the 24 Hours of Aspen, Winterskol and Blitzenbanger. KSPN features the AAA format, which combines the classic rock hits from Tom Petty, Van Morrison and Talking Heads with today’s newer musicians like Ben Harper, Blues Traveler, Sonia Dada and Widespread Panic.
Keywords: Talking Heads, KSPN's AAA format.
Output: KSPN features Talking Heads in its AAA format.

Input: Gina Bramhill was born in Eastoft, where she grew up on a farm. As a child, she appeared in several school plays. She was trained at the Royal Academy of Dramatic Art. Shortly after graduating she appeared as Bella in the movie Lotus Eaters. 2012 she got a role as the recurring character Eve Sands in the TV series Being Human. In the same year Bramhill played one of the main roles in the drama pilot The Frontier. In Coronation Street she portrayed the character Jodie Woodward. She got a main role in the movie Pleasure Island, which was shown at the Cannes Film Festival in 2014.
Keywords: Gina Bramhill, born.
Output: Gina Bramhill was born in Eastoft.

Given the following input and keywords, provide a concise and factual summary based on the examples above. Exclude any information not directly related to the keywords.

Input: [evidence]
Keywords: [keywords]
Output:
"""
###########################################################

def construct_keywordsprompt(claim):
    return format_chat(['',keywordsprompt.replace('[claim]',claim)])

def construct_extractprompt(e,keywords:list):
    keywords = ', '.join(keywords)+'.'
    return format_chat(['',extractprompt.replace('[evidence]',e).replace('[keywords]',keywords)])

def resolve_keywords(text):
    if len(text)>2 and text[-1]=='.':
        text = text[:-1]
    text = text.replace('\n','').replace('Output:','').replace('output:','').split(',')
    text = [i.strip() for i in text]
    return text # Is a List

def resolve_extract(text):
    outputpos = text.lower().find('output:')
    if outputpos != -1:
        text = text[outputpos:]
    exppos = text.lower().find('explanation:')
    if exppos != -1:
        text = text[:exppos]
    notepos = text.lower().find('note:')
    if notepos != -1:
        text = text[:notepos]
    text = text.replace('\n','').replace('Output:','').replace('output:','')
    return text

#########################################################

from fuzzywuzzy import fuzz

def filter_keywords(sentence, keywords, threshold1=60, threshold2=60, debug=False):
    sentence = sentence.replace('"','').replace('\"','')
    related_keywords = []
    for keyword in keywords:
        keyword = keyword.replace('"','').replace('\"','')
        score1,score2 = 0,0
        score1 = partial_ratio(sentence.lower(), keyword.lower())
        if score1 >= threshold1:
            related_keywords.append(keyword)
        else:
            score2 = fuzz.token_set_ratio(sentence.lower(), keyword.lower())
            if score2 >= threshold2:
                related_keywords.append(keyword)
        if debug:
            print((keyword,score1,score2))
    return related_keywords

from difflib import SequenceMatcher
fuzz.SequenceMatcher = SequenceMatcher
def partial_ratio(s1, s2):
    s1, s2 = fuzz.utils.make_type_consistent(s1, s2)
    if len(s1) <= len(s2):
        shorter = s1
        longer = s2
    else:
        shorter = s2
        longer = s1
    m = fuzz.SequenceMatcher(None, shorter, longer,autojunk=False)
    blocks = m.get_matching_blocks()
    scores = []
    for block in blocks:
        long_start = block[1] - block[0] if (block[1] - block[0]) > 0 else 0
        long_end = long_start + len(shorter)
        long_substr = longer[long_start:long_end]

        m2 = fuzz.SequenceMatcher(None, shorter, long_substr)
        r = m2.ratio()
        if r > .995:
            return 100
        else:
            scores.append(r)
    return fuzz.utils.intr(100 * max(scores))

###########################################################
###########################################################
import re
xpattern = re.compile(r'\[\[([^|\]]+)\|[^\]]+\]\]')
def replace_match(match):
    x_part = match.group(1).replace('_', ' ')  # Get X and remove underscores
    return x_part

def cleanfsevidence(sentence):
    sentence = sentence.replace('\t',' : ')
    result = xpattern.sub(replace_match, sentence)
    return result
###########################################################
split = 'dev'
if not fs:
    dataset = load_hover_dataset(split)
else:
    dataset = load_fs_dataset(split)
import random
xxxx = list(range(len(dataset)))
num = len(xxxx)
cnt = 0
for id in xxxx:
    newexample = {}
    example = dataset[id]
    label = example['label']
    newexample["label"] = label
    label = False if label=='refutes' else True
    if not fs:
        hop = example['num_hops']
        newexample["num_hops"] = hop
    claim = example['claim']
    newexample["claim"] = claim
    evidence = example['evidence'].replace('\"','\'')
    if fs:
        evidence = cleanfsevidence(evidence)
    newexample["evidence"] = evidence
    split_evidence = evidence.split('\n') # Is a List
    _keywords = api.send_message(construct_keywordsprompt(claim))
    keywords = resolve_keywords(_keywords)
    newexample["claimkey"] = ", ".join(keywords)
    newexample["add_evidence"] = []
    for ec,e in enumerate(split_evidence):
        related_keywords = filter_keywords(e, keywords)
        if len(related_keywords)<2:
            continue # too less keywords should not be used
        _e = (resolve_extract(api.send_message(construct_extractprompt(e,related_keywords))),", ".join([str(ec)]+related_keywords))
        newexample['add_evidence'].append(_e)
    with open(outputfile,'a') as f:
        json.dump(newexample,f)
        f.write('\n')
    cnt += 1

api.disconnect()
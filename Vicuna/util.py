import json
import re
from copy import deepcopy
from sklearn.metrics import f1_score, accuracy_score, classification_report
B_INST, E_INST = "[INST]", "[/INST]"
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"

dev_path = '../testdata/dev.json'
fs_dev_path = '../testdata/devfs.json'
train_path = ''
mini_path = ''
tiny_path = ''

def strip_last_stop(x):
    if x[-1]=='.':
        return x[:-1]
    else:
        return x

def parse_json(text,key):
    ret = text
    try:
        matches = re.findall(r'\{(.*?)\}', text.replace('\n',' ').replace('\\',''))[0]
        x = json.loads('{'+matches+'}')
        ret = x[key]
    except:
        pass
    return ret

def load_fs_dataset(split=None,path=None):
    if not path:
        if split=='dev':
            path = fs_dev_path
        else:
            print('Error Split')
            return
    print('loading from:',path)
    with open(path) as f:
        if split is None:
            x = [json.loads(i.strip()) for i in f.readlines() if len(i)>3]
        else:
            x = json.load(f)
    print(f'Loaded {len(x)} examples')
    return x


def eval_hover_results(predicts,labels,hops):
    hop2_p,hop2_l = [],[]
    hop3_p,hop3_l = [],[]
    hop4_p,hop4_l = [],[]
    hop2result,hop3result,hop4result = None,None,None
    for i in range(len(hops)):
        if hops[i]==2:
            hop2_p.append(predicts[i])
            hop2_l.append(labels[i])
        if hops[i]==3:
            hop3_p.append(predicts[i])
            hop3_l.append(labels[i])
        if hops[i]==4:
            hop4_p.append(predicts[i])
            hop4_l.append(labels[i])
    try:
        hop2result = {
            'hops':2,
            'num': len(hop2_p),
            'acc': accuracy_score(hop2_l,hop2_p),
            'macro': f1_score(hop2_l,hop2_p,average='macro')
        }
    except:
        pass
    try:
        hop3result = {   
            'hops':3,
            'num': len(hop3_p),
            'acc': accuracy_score(hop3_l,hop3_p),
            'macro': f1_score(hop3_l,hop3_p,average='macro')
        }
    except:
        pass

    try:
        hop4result = {
            'hops':4,
            'num': len(hop4_p),
            'acc': accuracy_score(hop4_l,hop4_p),
            'macro': f1_score(hop4_l,hop4_p,average='macro')
        }
    except:
        pass
    try:
        print('For hop2:',classification_report(hop2_l,hop2_p))
    except:
        pass
    try:
        print('For hop3:',classification_report(hop3_l,hop3_p))
    except:
        pass
    try:
        print('For hop4:',classification_report(hop4_l,hop4_p))
    except:
        pass
    return hop2result,hop3result,hop4result



def load_hover_dataset(split=None,path=None):
    if not path:
        if split=='dev':
            path = dev_path
        # elif split=='train':
        #     path = train_path
        # elif split=='mini':
        #     path = mini_path
        # elif split=='tiny':
        #     path = tiny_path
        else:
            print('Error Split')
            return
    print('loading from:',path)
    with open(path) as f:
        if split is None:
            x = [json.loads(i.strip()) for i in f.readlines() if len(i)>3]
        else:
            x = json.load(f)
    print(f'Loaded {len(x)} examples')
    return x

def format_mixtral_chat_input(history):
    assert(len(history)>=2)
    nh = deepcopy(history)
    nh0 = nh.pop(0)
    nh[0] = nh0 + nh[0]
    ret = []
    for i,meg in enumerate(nh):
        if i%2==0:
            role = 'user'
        else:
            role = 'assistant'
        ret.append({"role":role,"content":meg})
    return ret



def format_vicuna_chat_input(history):
    assert(len(history)>=2)
    system = history.pop(0)
    ret = ''
    if len(system)>0:
        ret += (system + ' ')
    for i,meg in enumerate(history):
        if i%2 == 0:
            ret += 'USER:'
        else:
            ret += "ASSISTANT:"
        ret += (' '+meg.strip()+' ')
    if i%2 == 0:
        ret += 'ASSISTANT:'
    history.insert(0,system)
    return ret

"""
    history:List = ["system","user","assistant","user","assistant", ...]
    -> output:String
    Example output:
    [INST] «SYS»\nYou are a helpful, respectful and honest assistant. 
    Always answer as helpfully as possible, while being safe. 
    Your answers should not include any harmful, unethical, racist, 
    sexist, toxic, dangerous, or illegal content. Please ensure that your 
    responses are socially unbiased and positive in nature.\n\n
    If a question does not make any sense, or is not factually coherent, 
    explain why instead of answering something not correct. If you don’t know 
    the answer to a question, please don’t share false information.\n«/SYS»\n\n
    Hi, how are you? [/INST] Good thanks! \n[INST] Can you help me with 
    this math program? [/INST]
"""
def format_llama_chat_input(history):
    assert(len(history)>=2)
    system = history.pop(0)
    firstprompt = history[0]
    if len(system)>0:
        history[0] = B_SYS + system + E_SYS + history[0]
    assert(len(history)%2==1)
    output = [
        B_INST+' '+ask.strip()+' '+E_INST+' '+ans.strip()
        for ask,ans in zip(history[::2],history[1::2])
    ]
    output += B_INST+' '+history[-1].strip()+' '+E_INST
    output = ''.join(output)
    history.pop(0)
    history.insert(0,firstprompt)
    history.insert(0,system)
    return output


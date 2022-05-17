import extract_msg
import glob
import re
import json
from tqdm import tqdm
from dateutil import parser
import hashlib

msg = extract_msg.openMsg("/home/deng.595/workspace/papers/parse/emails/alerts/Yejin Choi - new articles (192).msg")
msg = json.loads(msg.getJson())
def parse_refs(msg):
    date = msg['date']
    body = msg['body'].replace('\r\n', '\n').encode("ascii", "ignore").decode()
    body = re.sub(r"\'|\"|\\",' ',body)
    papers = []
    lines = [line.strip() for line in body.split('\n') if line.strip()]
    i = 0
    tmp = None
    while i < len(lines):
        line = lines[i]
        if 'This message was sent by' in line:
            break
        remaining = re.sub(r'<http.*>|\[PDF\]|\[HTML\]', '', line).strip()
        if '<http' in line and remaining and tmp is None:
            tmp = {}
            tmp['title'] = remaining
            tmp['date'] = date
            i += 1
            tmp['authors'] = lines[i].strip()
            i += 1
            tmp['abs'] = ''
            while i < len(lines) and '<http' not in lines[i]:
                tmp['abs'] += ' ' + lines[i].strip()
                i += 1
            tmp['abs'] = tmp['abs'].strip()
            papers.append(tmp)
            tmp = None
        else:
            i += 1


    return papers

print(parse_refs(msg))
all_papers = {}
for alert in tqdm(glob.glob('/home/deng.595/workspace/papers/parse/emails/alerts/*')):
    msg = extract_msg.openMsg(alert)
    msg = json.loads(msg.getJson())
    papers = parse_refs(msg)
    for paper in papers:
        k = paper['title'] + ' | ' + paper['authors']
        all_papers[k.lower()] = paper
print(f'{len(all_papers)} papers in total')
print([paper for paper in all_papers.values()][:2])
for k, paper in all_papers.items():
    date = parser.parse(paper['date'])
    # date = parser.parse("2022-05-16 03:59:43 -0400")
    with open(f"/home/deng.595/workspace/papers/docs/_posts/{date.strftime('%Y-%m-%d')}-{hashlib.md5(k.encode()).hexdigest()}.markdown", "w") as f:
        f.write(f'---\nlayout: post\ntitle:  "{paper["title"]}"\ndate:   {date.strftime("%Y-%m-%d %X")} -0400\ncategories: jekyll update\nauthor: "{paper["authors"]}"\n---\n{paper["abs"]}')
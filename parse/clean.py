import collections
import glob
import json
import os
import re
import sys

illegal_unichrs = [
    (0x00, 0x08),
    (0x0B, 0x0C),
    (0x0E, 0x1F),
    (0x7F, 0x84),
    (0x86, 0x9F),
    (0xFDD0, 0xFDDF),
    (0xFFFE, 0xFFFF),
]
if sys.maxunicode >= 0x10000:  # not narrow build
    illegal_unichrs.extend(
        [
            (0x1FFFE, 0x1FFFF),
            (0x2FFFE, 0x2FFFF),
            (0x3FFFE, 0x3FFFF),
            (0x4FFFE, 0x4FFFF),
            (0x5FFFE, 0x5FFFF),
            (0x6FFFE, 0x6FFFF),
            (0x7FFFE, 0x7FFFF),
            (0x8FFFE, 0x8FFFF),
            (0x9FFFE, 0x9FFFF),
            (0xAFFFE, 0xAFFFF),
            (0xBFFFE, 0xBFFFF),
            (0xCFFFE, 0xCFFFF),
            (0xDFFFE, 0xDFFFF),
            (0xEFFFE, 0xEFFFF),
            (0xFFFFE, 0xFFFFF),
            (0x10FFFE, 0x10FFFF),
        ]
    )

illegal_ranges = [rf"{chr(low)}-{chr(high)}" for (low, high) in illegal_unichrs]
xml_illegal_character_regex = "[" + "".join(illegal_ranges) + "]"
illegal_xml_chars_re = re.compile(xml_illegal_character_regex)


def compile_expression(x):
    return re.compile(r"\b(" + "|".join(x) + r")\b", re.IGNORECASE)


TOPIC_IGNORE = compile_expression(
    [
        "speech",
        "audio",
        r"russian?|korean?|german|chinese|indian?|arabic|spanish|french|turkish|irish|japanese|hindi|dutch|english|china",
        r"music|song|lyrics?|musical",
        "biology",
        "biological",
        "health",
        "drug",
        "medical",
        "radiology",
        "molecular|dna|rna|molecule",
        "VQA",
        "protein",
        r"multi-?lingual|bi-?lingual|cross-?lingual",
        "internet-of-things?|iot",
        "3D",
        "2D",
        "image",
        "vision transformer",
        "traffic",
        "camera",
        "sensor",
        "videos?",
        "imaging",
        "vision and language",
        r"bio-?medical",
        "gene",
        "disease",
        "uav",
        "eecs",
        "navigation",
        "asr",
        "visual question",
        "clinical|surgical",
        "FPGA",
        r"(bi)?-?lstm",
        r"crypto\w*|blockchain",
        "time series",
        "politic(al)?",
        "mobile device",
        "object (detection|tracking)",
        "multi-?modal",
        "pharmacology",
        "geoscience",
        "psychological",
        "vision task",
        "vision-language",
        "e-commerce",
        "tree species",
        "chemistry",
        "electronic",
        "cancer",
        "ultrasonic",
        "biochemical|chemical",
        "power distribution|voltage",
        "vehicles?",
        "hurricanes?",
        "IoT",
        "diseases?",
        "x-ray",
        "epidemiology",
        "bio-?bert",
        "gender",
        "sonar",
        "vaccination",
        "supply chain",
        "climate",
        "Psychology",
    ]
)
PUB_INGORE = compile_expression(
    [
        "ieee access",
        "clinical",
        "medical",
        "energy",
        "multimedia",
        "drug",
        "music",
        "transactions on power",
        "IoT",
        "vehicles?",
        "security",
        "wireless",
        "sensors?",
        "biology",
        r"bio-?medical",
        "social Sciences?",
        "education",
        "chemical",
        "applied intelligence",
        "health",
        r"bio\w+",
        "patent",
        "USENIX",
        r"\w+chemistry\w+",
        "english",
        "automation",
        "IISE",
    ]
)


paper_to_delete = set()
all_cached_papers = set()
with open("/home/deng.595/workspace/papers/parse/all_papers.tsv", "r") as f:
    for line in f:
        line = line.strip().strip("\"'").lower().split("\t")
        if line[0] == "0":
            paper_to_delete.add(line[2])
        if len(line) > 2:
            all_cached_papers.add(line[1])
print(len(paper_to_delete), list(paper_to_delete)[:5])
to_delete = []
to_modify = []
ignore_count = collections.Counter()
for f_path in glob.glob("/home/deng.595/workspace/papers/docs/_posts/*.markdown"):
    cleaned_line = []
    original_line = []
    with open(f_path, "r") as f:
        for line in f:
            original_line.append(line)
            cleaned_line.append(re.sub("\s+", " ", re.sub(r"[^\x00-\x7f]", "", line)))
            if line.startswith("title:"):
                title = line[6:].strip().strip("\"'").lower()
                if title in paper_to_delete:
                    to_delete.append(f_path)
                if (
                    len(title.strip()) == 0
                    or TOPIC_IGNORE.search(title)
                    or (
                        re.findall("\s+", title)
                        and max([len(x) for x in re.findall("\s+", title)]) > 3
                    )
                ):
                    to_delete.append(f_path)
            elif line.startswith("author:"):
                authors = line[7:].strip().strip("\"'").lower()
                if PUB_INGORE.search(authors):
                    to_delete.append(f_path)
                elif len(authors.split("-")[0].split(",")) == 1:
                    to_delete.append(f_path)
            elif TOPIC_IGNORE.findall(line):
                to_delete.append(f_path)
                ignore_count.update(set(TOPIC_IGNORE.findall(line)))
    if "\n".join(cleaned_line) != "\n".join(original_line):
        to_modify.append(f_path)
    with open(f_path, "w") as f:
        f.write(
            illegal_xml_chars_re.sub(
                "",
                re.sub(
                    r"\nCite", " Cite", re.sub(r"\n+", "\n", "\n".join(cleaned_line))
                ),
            )
            .strip()
            .encode("ascii", "ignore")
            .decode()
        )
to_delete = set(to_delete)
for f_path in to_delete:
    os.remove(f_path)
print(len(to_delete))
print(ignore_count.most_common())
print(len(to_modify))
print(to_modify[:3])

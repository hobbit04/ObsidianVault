# -*- coding: utf-8 -*-
"""
PaperList.md 의 링크로부터 BibTeX 를 받아 references.bib 를 채우고,
_Source/*.md 노트에 citekey 속성을 붙인다.

- arXiv 링크: arxiv.org/bibtex 에서 엔트리를 받아온다.
- venue: _Source 노트의 frontmatter 에 적어둔 값을 사용해 @misc -> @inproceedings 로 승격.
- 이미 references.bib 에 있는 citekey 는 다시 받지 않는다. (paper_sync.py 와 같은 방식)
- arXiv 가 아닌 링크는 TODO 주석으로 남겨 직접 채우게 한다.

사용법: python3 bib_sync.py
"""
import os, re, sys, time, unicodedata
from urllib.request import urlopen, Request

PAPER_LIST = "PaperList.md"
SOURCE_DIR = "_Source"
BIB_FILE   = "references.bib"
SLEEP      = 1.5   # arXiv 에 대한 예의

VENUE_BOOKTITLE = {
    "CVPR":     "Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)",
    "ICCV":     "Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)",
    "ECCV":     "Proceedings of the European Conference on Computer Vision (ECCV)",
    "WACV":     "Proceedings of the IEEE/CVF Winter Conference on Applications of Computer Vision (WACV)",
    "NeurIPS":  "Advances in Neural Information Processing Systems (NeurIPS)",
    "ICLR":     "International Conference on Learning Representations (ICLR)",
    "ICML":     "Proceedings of the International Conference on Machine Learning (ICML)",
    "AAAI":     "Proceedings of the AAAI Conference on Artificial Intelligence (AAAI)",
    "SIGGRAPH": "ACM Transactions on Graphics (Proc. SIGGRAPH)",
    "CoRL":     "Conference on Robot Learning (CoRL)",
    "RSS":      "Robotics: Science and Systems (RSS)",
}

STOPWORDS = {"a","an","the","on","of","for","and","in","with","to","from","via","is","are"}

# arXiv 에 없어서 손으로 채운 엔트리. {PDF 파일명: (citekey, BibTeX 본문)}
# ※ 기억에 의존해 채운 것이라 권/호/페이지는 한 번 확인해 주세요.
MANUAL = {
"COLMAP.pdf": ("schonberger2016colmap", """@inproceedings{schonberger2016colmap,
  title     = {Structure-from-Motion Revisited},
  author    = {Sch\\"{o}nberger, Johannes L. and Frahm, Jan-Michael},
  booktitle = {Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)},
  year      = {2016},
}"""),
"DQN.pdf": ("mnih2015dqn", """@article{mnih2015dqn,
  title   = {Human-level control through deep reinforcement learning},
  author  = {Mnih, Volodymyr and Kavukcuoglu, Koray and Silver, David and Rusu, Andrei A. and
             Veness, Joel and Bellemare, Marc G. and Graves, Alex and Riedmiller, Martin and
             Fidjeland, Andreas K. and Ostrovski, Georg and others},
  journal = {Nature},
  volume  = {518},
  number  = {7540},
  pages   = {529--533},
  year    = {2015},
}"""),
"RL_book.pdf": ("sutton2018rl", """@book{sutton2018rl,
  title     = {Reinforcement Learning: An Introduction},
  author    = {Sutton, Richard S. and Barto, Andrew G.},
  edition   = {2nd},
  publisher = {MIT Press},
  year      = {2018},
}"""),
"mml-book.pdf": ("deisenroth2020mml", """@book{deisenroth2020mml,
  title     = {Mathematics for Machine Learning},
  author    = {Deisenroth, Marc Peter and Faisal, A. Aldo and Ong, Cheng Soon},
  publisher = {Cambridge University Press},
  year      = {2020},
}"""),
"Structure from Motion.pdf": ("tomasi1992sfm", """@article{tomasi1992sfm,
  title   = {Shape and motion from image streams under orthography: a factorization method},
  author  = {Tomasi, Carlo and Kanade, Takeo},
  journal = {International Journal of Computer Vision},
  volume  = {9},
  number  = {2},
  pages   = {137--154},
  year    = {1992},
}"""),
"Signed Distance Function.pdf": ("malladi1995sdf", """@article{malladi1995sdf,
  title   = {Shape modeling with front propagation: a level set approach},
  author  = {Malladi, Ravi and Sethian, James A. and Vemuri, Baba C.},
  journal = {IEEE Transactions on Pattern Analysis and Machine Intelligence},
  volume  = {17},
  number  = {2},
  pages   = {158--175},
  year    = {1995},
}"""),
}

# PaperList 에 중복으로 올라온 PDF (같은 논문의 다른 파일명) - bib 에서는 하나만 쓴다
DUPLICATE_PDFS = {"BatchNorm.pdf", "Human-level control through deep reinforcement learning.pdf"}



# ---------- 유틸 ----------

def slug(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^0-9A-Za-z]", "", s).lower()


def arxiv_id(url):
    m = re.search(r"arxiv\.org/(?:pdf|abs)/([0-9]{4}\.[0-9]{4,5})", url)
    return m.group(1) if m else None


def fetch(url):
    req = Request(url, headers={"User-Agent": "obsidian-bib-sync/1.0"})
    with urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def parse_bibtex(text):
    """arxiv.org/bibtex 응답에서 필드를 뽑는다."""
    fields = {}
    for key in ("title", "author", "year", "eprint", "primaryClass", "doi"):
        m = re.search(r"\b%s\s*=\s*\{(.*?)\}\s*,?\s*\n" % key, text, re.S)
        if m:
            fields[key] = " ".join(m.group(1).split())
    return fields


# arXiv 는 "최신 개정판" 연도를 준다. 대부분은 학회 게재 연도와 같지만,
# 게재 한참 뒤에도 개정되는 논문은 어긋난다. 그런 것만 여기에 적어 바로잡는다.
YEAR_FIX = {
    "1706.03762": "2017",  # Attention Is All You Need (NeurIPS 2017, arXiv 는 2023)
    "2010.02502": "2021",  # DDIM (ICLR 2021)
    "1512.03385": "2016",  # ResNet (CVPR 2016)
    "2303.04137": "2023",  # Diffusion Policy (RSS 2023)
    "2506.02070": "2025",  # Flow Matching 강의노트
}


def resolve_year(aid, arxiv_year):
    return YEAR_FIX.get(aid, arxiv_year)


def short_nick(nickname):
    """통칭이 길면 첫 단어만. (Scholar 가 만드는 키와 같은 관례)"""
    words = [w for w in re.split(r"[\s_\-]+", nickname) if slug(w) and slug(w) not in STOPWORDS]
    joined = slug("".join(words))
    if len(joined) <= 20:
        return joined
    return slug(words[0]) if words else ""


def make_citekey(author, year, nickname):
    """<성><연도><통칭>  예) schonberger2016colmap"""
    first = author.split(" and ")[0].strip()
    last = first.split(",")[0].split()[-1] if "," not in first else first.split(",")[0]
    last = slug(last) or "anon"
    nick = short_nick(nickname)
    if nick.isdigit():
        nick = ""
    return "%s%s%s" % (last, year or "", nick)


def fmt_entry(etype, key, fields, order):
    w = max(len(k) for k in order if k in fields)
    lines = ["@%s{%s," % (etype, key)]
    for k in order:
        if fields.get(k):
            lines.append("  %-*s = {%s}," % (w, k, fields[k]))
    lines.append("}")
    return "\n".join(lines)


# ---------- 볼트에서 정보 모으기 ----------

def read_paper_list():
    papers = []
    with open(PAPER_LIST, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "," not in line:
                continue
            name, link = line.split(",", 1)
            papers.append((name.strip(), link.strip()))
    return papers


def read_source_notes():
    """{pdf 파일명: (노트 경로, venue, title)}"""
    out = {}
    if not os.path.isdir(SOURCE_DIR):
        return out
    for fn in sorted(os.listdir(SOURCE_DIR)):
        if not fn.endswith(".md"):
            continue
        p = os.path.join(SOURCE_DIR, fn)
        t = open(p, encoding="utf-8").read()
        venue = title = None
        m = re.search(r"^venue:\s*(.+)$", t, re.M)
        if m:
            venue = m.group(1).strip().strip('"')
        m = re.search(r"^title:\s*(.+)$", t, re.M)
        if m:
            title = m.group(1).strip().strip('"')
        for pdf in re.findall(r"\[\[([^\[\]|]+\.pdf)\]\]", t):
            out.setdefault(pdf, (p, venue, title))
    return out


def existing_keys():
    if not os.path.exists(BIB_FILE):
        return set(), ""
    text = open(BIB_FILE, encoding="utf-8").read()
    return set(re.findall(r"@\w+\{([^,]+),", text)), text


# ---------- 본 작업 ----------

CACHE = ".bibcache"


def cached_arxiv_bibtex(aid):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, aid + ".bib")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read(), False
    time.sleep(SLEEP)
    text = fetch("https://arxiv.org/bibtex/%s" % aid)
    open(p, "w", encoding="utf-8").write(text)
    return text, True


def main():
    papers = read_paper_list()
    notes = read_source_notes()

    entries = []          # (citekey, pdf_name, note_path, bibtex)
    todos, dups = [], []
    seen_eprint, seen_key = {}, set()

    for pdf_name, url in papers:
        if pdf_name in DUPLICATE_PDFS:
            dups.append((pdf_name, "PaperList 중복 항목"))
            continue

        nickname = re.sub(r"\.pdf$", "", pdf_name)
        note = notes.get(pdf_name)
        note_path = note[0] if note else None

        if pdf_name in MANUAL:
            key, text = MANUAL[pdf_name]
            entries.append((key, pdf_name, note_path, text))
            seen_key.add(key)
            print("  [수동] %-40s -> %s" % (nickname, key))
            continue

        aid = arxiv_id(url)
        if not aid:
            todos.append((nickname, url))
            continue

        try:
            raw, downloaded = cached_arxiv_bibtex(aid)
        except Exception as e:
            print("  [실패] %-40s %s" % (nickname, e))
            todos.append((nickname, url))
            continue

        f = parse_bibtex(raw)
        if not f.get("author"):
            todos.append((nickname, url))
            continue

        if aid in seen_eprint:
            dups.append((pdf_name, "%s 와 같은 arXiv ID" % seen_eprint[aid]))
            continue
        seen_eprint[aid] = pdf_name

        year = resolve_year(aid, f.get("year", ""))
        key = make_citekey(f.get("author", ""), year, nickname)
        n = 2
        base = key
        while key in seen_key:
            key = "%s%c" % (base, ord("a") + n - 2)
            n += 1
        seen_key.add(key)

        if note and note[2]:
            f["title"] = note[2]
        booktitle = VENUE_BOOKTITLE.get(note[1], note[1]) if note else None

        fields = {
            "title":  f.get("title", nickname),
            "author": f.get("author", ""),
            "year":   year,
            "eprint": aid,
            "archivePrefix": "arXiv",
            "primaryClass": f.get("primaryClass", ""),
            "url": "https://arxiv.org/abs/%s" % aid,
        }
        if booktitle:
            fields["booktitle"] = booktitle
            etype = "inproceedings"
            order = ["title", "author", "booktitle", "year", "eprint", "archivePrefix", "primaryClass", "url"]
        else:
            etype = "misc"
            order = ["title", "author", "year", "eprint", "archivePrefix", "primaryClass", "url"]

        entries.append((key, pdf_name, note_path, fmt_entry(etype, key, fields, order)))
        print("  [%s] %-40s -> %s" % ("받음" if downloaded else "캐시", nickname, key))

    body = ["% bib_sync.py 가 생성합니다. 손으로 고친 내용은 스크립트의 MANUAL 에 넣으세요.", ""]
    for key, _, _, text in sorted(entries, key=lambda e: e[0]):
        body.append(text)
        body.append("")
    if todos:
        body.append("% ==== TODO: 자동으로 못 받은 항목. Google Scholar -> BibTeX 로 채우세요 ====")
        for nickname, url in todos:
            body.append("%% %-45s %s" % (nickname, url))
        body.append("")
    open(BIB_FILE, "w", encoding="utf-8").write("\n".join(body))

    touched = 0
    for key, pdf_name, note_path, _ in entries:
        if not note_path:
            continue
        t = open(note_path, encoding="utf-8").read()
        if re.search(r"^citekey:", t, re.M):
            t = re.sub(r"^citekey:.*$", "citekey: %s" % key, t, count=1, flags=re.M)
        else:
            m = re.search(r"^title:.*$", t, re.M)
            if m:
                t = t[:m.end()] + "\ncitekey: %s" % key + t[m.end():]
            else:
                t = t.replace("---\n", "---\ncitekey: %s\n" % key, 1)
        open(note_path, "w", encoding="utf-8").write(t)
        touched += 1

    print("\n---- 요약 ----")
    print("references.bib 엔트리 : %d" % len(entries))
    print("citekey 붙인 노트      : %d" % touched)
    print("수동 입력 필요(TODO)   : %d" % len(todos))
    for n, u in todos:
        print("   - %s" % n)
    if dups:
        print("중복으로 건너뜀        : %d" % len(dups))
        for n, why in dups:
            print("   - %s (%s)" % (n, why))


if __name__ == "__main__":
    main()

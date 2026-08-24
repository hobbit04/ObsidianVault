# Store the list of papers as its name and arXiv link. 
# Name is the key to decide if it needs to download or not. 
from pathlib import Path
from requests import get
import os

def download_file(url, file_name):
    with open(file_name, "wb") as file:   # open in binary mode
        response = get(url)               # get request
        file.write(response.content)      # write to file


archive_folder = "./Archive/"
paper_list = "PaperList.md"  # File where all {key: "paper_name", value: "download link"} is stored.

# key: "paper_name", value: "download link"
papers = {}
with open(paper_list, "r", encoding="utf-8") as file:
    for line in file:
        line = line.strip()
        if not line:
            continue
        name, link = line.split(",", 1)
        papers[name.strip()] = link.strip()

local_papers = []

for path in Path(archive_folder).glob('*.pdf'):
    local_papers.append(path.name)

# Before downloading papers, check if PaperList.md is complete.
for local_paper in local_papers:
    if local_paper not in papers:
        print(f"ALERT: {local_paper} is NOT in {archive_folder}. Please update the PaperList.md")

summary = []
for paper_name, link in papers.items():
    if paper_name not in local_papers:
        print(f"{paper_name} is NOT in {archive_folder}")
        # Download using link
        download_file(link, os.path.join(archive_folder, paper_name))
        summary.append(paper_name)

# Print summary
print("---Task finished---")
print(f"Total {len(summary)} numbers of papers downloaded in {archive_folder}")
if(len(summary) == 0):
    quit()
    
print("----------------List of downloaded papers----------------")
for name in summary:
    print(name)
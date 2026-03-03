---
name: arxiv-paper-reader
description: Read and analyze arXiv papers from a provided arXiv URL by fetching the arXiv source archive from /src/, unpacking LaTeX files locally, locating the TeX entrypoint, and recursively reading relevant source files. Use when asked to read, summarize, explain, or extract details from an arXiv paper URL.
---

# Arxiv Paper Reader

Read the paper from the provided arXiv link via the arXiv source archive.

## Workflow


You will be given a URL of an arxiv paper, for example:

https://www.arxiv.org/abs/2601.07372

### Part 1: Normalize the URL

The goal is to fetch the TeX Source of the paper (not the PDF!), the URL always looks like this:

https://www.arxiv.org/src/2601.07372

Notice the /src/ in the url. Once you have the URL:

### Part 2: Download the paper source

Fetch the url to a local .tar.gz file. A good location is `/tmp/{arxiv_id}.tar.gz`.

(If the file already exists, there is no need to re-download it).

### Part 3: Unpack the file in that folder

Unpack the contents into `/tmp/{arxiv_id}` directory.

### Part 4: Locate the entrypoint

Every latex source usually has an entrypoint, such as `main.tex` or something like that.

### Part 5: Read the paper

Once you've found the entrypoint, Read the contents and then recurse through all other relevant source files to read the paper.
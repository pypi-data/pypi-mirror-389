# CBDB API — Snapshot

Source: https://cbdb.hsites.harvard.edu/cbdb-api

Fetched on: 2025-11-02

Note: The content below was automatically fetched and may be a partial extract of the page's main content. For the authoritative and complete version, visit the source link above.

---

## Introduction to CBDB API

API (application programming interfaces) is an application which allows system interoperability. Through API, each database can retrieve data from another database to supplement its own without actually storing them.

CBDB API now allows other databases to retrieve and present CBDB data on the fly. We accept two types of queries:

1. Query by person ID (CBDB ID)
2. Query by name (Chinese and Pinyin)

How to Call CBDB API — Example for 王安石 (Wang Anshi):

- Query by person ID: https://cbdb.fas.harvard.edu/cbdbapi/person.php?id=1762 (Wang Anshi's CBDB ID)
- Query by name (Chinese): https://cbdb.fas.harvard.edu/cbdbapi/person.php?name=%E7%8E%8B%E5%AE%89%E7%9F%B3
- Query by name (Pinyin): https://cbdb.fas.harvard.edu/cbdbapi/person.php?name=Wang%20Anshi
- JSON output: https://cbdb.fas.harvard.edu/cbdbapi/person.php?name=%E7%8E%8B%E5%AE%89%E7%9F%B3&o=json

Output format: After calling the API, it will return the complete data of the person in CBDB.

Image examples on the page:

- HTML output screenshots: picture1.png, picture2.png
- JSON output screenshot: cbdb-api-json.png

---

## Current Users of CBDB API

- Ming Qing Women's Writings — https://digital.library.mcgill.ca/mingqing/english/index.php
- 人名權威人物傳記資料 — http://archive.ihp.sinica.edu.tw/ttsweb/html_name/index.php
- Communication and Empire: Chinese Empires in Comparative Perspective — https://chinese-empires.eu/
- Digging into Data: Automating Chinese Text Extraction — https://did-acte.org/

---

License notice (from site footer):

© China Biographical Database. Except where otherwise noted, content on this site is licensed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International license.

Harvard University site footer links omitted for brevity.

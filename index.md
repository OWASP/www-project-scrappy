---

layout: col-sidebar
title: OWASP ScrapPy
tags: scraping recon osint owasp pdf discovery
level: 4
type: tool
pitch: ScrapPY is a Python utility for scraping manuals, documents, and other sensitive PDFs to generate targeted wordlists that can be utilized by offensive security tools to perform brute force, forced browsing, and dictionary attacks.

---

<p align="center">
<img width=40% height=40% src="/assets/images/doggo.png">
</p>

# ScrapPY: PDF Scraping Made Easy

ScrapPY is a Python utility for scraping manuals, documents, and other sensitive PDFs to generate targeted wordlists that can be utilized by offensive security tools to perform brute force, forced browsing, and dictionary attacks. ScrapPY performs word frequency, entropy, and metadata analysis, and can run in full output modes to craft custom wordlists for targeted attacks. The tool dives deep to discover keywords and phrases leading to potential passwords or hidden directories, outputting to a text file that is readable by tools such as Hydra, Dirb, and Nmap. Expedite initial access, vulnerability discovery, and lateral movement with ScrapPY!

# Demo:

https://user-images.githubusercontent.com/72598486/201235531-6b037daf-d1f3-4d33-b256-8411e3a0b3da.mov

## Future Development:

- [x] Allow for custom output file naming and increased verbosity
- [x] Integrate different modes of operation including word frequency analysis
- [x] Allow for metadata analysis
- [x] Search for high-entropy data
- [ ] Search for path-like data 
- [ ] Implement image OCR to enumerate data from images in PDFs
- [ ] Allow for processing of multiple PDFs

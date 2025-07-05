"""
Configuration file for Academic Web Crawler Project

Course: Unknown (Winter 2025)
Instructors: Dr. Anwar Al-Hanshiri
Student: Esraa Kablan (Master's Degree Candidate)
Institution: Misurata University, Information Technology Department
Project: Search Engine Implementation Study
"""

# Directory configuration
INDEX_DIR = "indexdir"  # Directory to store Whoosh search index

# Web crawler configuration
USER_AGENT = (
    "SportsSearchBot/1.0 (+https://example.com; research by Esraa Kablan)"
)
# List of target domains for crawling (University websites preferred)

TARGET_SITES = [
    "https://www.goodreads.com/",        
    "https://www.theguardian.com/books",       
    "https://www.nytimes.com/section/books", 
    "https://reedsy.com/discovery",
    "https://www.gutenberg.org/" ,          
]

# Crawling limits
MAX_PAGES_PER_SITE = 20  # Limit to 20 pages per domain (0 for unlimited)

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
    "https://www.bbc.com/sport",        # BBC Sport
    "https://www.nytimes.com/section/sports",  # NY Times Sports
    "https://www.cbssports.com",        # CBS Sports
    "https://www.skysports.com",        # Sky Sports
]

# Crawling limits
MAX_PAGES_PER_SITE = 20  # Limit to 20 pages per domain (0 for unlimited)

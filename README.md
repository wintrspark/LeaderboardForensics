# Kogama Leaderboard Intelligence System

A sophisticated two-component Python system designed for systematic collection and analysis of Kogama player data. The system enables large-scale leaderboard scraping with intelligent storage organization and advanced username filtering with leetspeak detection capabilities.

## 🏗️ System Architecture

### **Data Collection Module (main.py)**
**Purpose:** Efficiently scrape and organize leaderboard data from multiple Kogama servers with fault tolerance and graceful interruption handling.

**Core Features:**
- Multi-server support: www (global), br (Brazil), friends (social)
- Intelligent bucket-based storage (5,000 entries per bucket)
- Automatic resumption from last saved page
- Retry logic with exponential backoff for network resilience
- Real-time progress tracking with percentage completion
- Graceful shutdown with SIGINT/SIGTERM handling

**Storage Strategy:**
```
Data/
├── www/
│   ├── 1to5000/
│   │   └── data.json
│   ├── 5001to10000/
│   │   └── data.json
│   └── last.json (saves progress)
├── br/
└── friends/
   ```

**Key Functions:**
- ```BucketManager``` - Manages rank-based data partitioning
- ```atomic_write()``` - Prevents data corruption with temporary files
- ```normalize_id()``` - Handles multiple ID field naming conventions
- ```fetch_page()``` - Robust HTTP requests with timeout and retry

**Usage:**
   ```
python main.py
# Enter server [br,www,friends]: www
# Progress: 45.231000% page=123 collected=49231 total=108765
   ```

### **Content Analysis Module (slurs.py)**
**Purpose:** Detect inappropriate usernames using comprehensive pattern matching with leetspeak support.

**Detection Capabilities:**
- **Leetspeak Translation**: Recognizes character substitutions (a→4/@, e→3, s→5/$)
- **Multi-format Matching**: Tests raw, normalized, and collapsed username variants
- **Diacritic Normalization**: Uses Unidecode for international character handling
- **Pattern Isolation**: Prevents partial matches with word boundary assertions
- **Batch Processing**: Efficiently scans thousands of stored profiles

**Output Structure:**
```
Hits/
├── inappropriate_accounts.txt (combined results)
├── Inappropriate_words/
│   ├── 1to5000_slurs.txt
│   └── 5001to10000_slurs.txt
└── inappropriate_accounts_collections/
    └── txt/
        ├── slur_fuck.txt
        ├── slur_shit.txt
        └── slur_nword.txt
```

**Pattern Generation Example:**
For slur "test" with leetspeak enabled:
```
Pattern: (?<![a-z0-9])(?:t|7|\+)[\W_]*(?:e|3|€)[\W_]*(?:s|5|\$)[\W_]*(?:t|7|\+)(?![a-z0-9])
Matches: "t3s+", "7€5t", "t.e_s.t", "TEST"
```

## 🚀 Quick Start

### Prerequisites
```
pip install requests unidecode
```
### Step 1: Collect Data
```
# Run the scraper for desired server
python main.py
# Let it run until completion or interrupt with Ctrl+C
```

### Step 2: Prepare Filter List
Create ```flags.json``` with your filtering terms:
```
{
  "explicit": ["slur1", "slur2"],
  "derogatory": ["term1", "term2"],
  "phrases": ["multi word term"]
}
```

### Step 3: Analyze Usernames
```
python slurs.py
# Processing data/www...
# Done. Found 847 accounts with slurs.
# TXT hits written to Data/Hits
```

## 🔧 Configuration

### main.py Constants
```
HOSTNAMES = {
    "www": "https://www.kogama.com/",
    "br": "https://www.kogama.com.br/",
    "friends": "https://friends.kogama.com/"
}
COUNT = 400                # Max entries per API page
BUCKET_SIZE = 5000         # Storage bucket size
SAVE_INTERVAL = 30         # Auto-save interval (seconds)
REQUEST_TIMEOUT = 10.0     # HTTP timeout
```

### slurs.py Customization
- Modify ```LEET_TABLE``` for additional character substitutions
- Adjust ```sanitize_filename()``` maxlen for different OS compatibility
- Toggle leetspeak detection with ```l33t_mode``` parameter

## 📊 Results & Impact

### Verification Timeline
| Date | Server | Action | Accounts Affected |
|------|--------|--------|-------------------|
| 2025-11-23 | www | Bot Account Termination | 580 |
| 2025-11-25 | www | Inappropriate Username Account Termination | 700 |
| 2025-12-03 | www | Inappropriate Username Account Termination | 1,400 |

### Data Quality Features
1. **Atomic Operations**: Prevents data corruption during writes
2. **Incremental Saving**: Regular checkpoints prevent data loss
3. **Resumable Scans**: Continues from last successful page
4. **Duplicate Prevention**: Tracks source pages for each entry
5. **Memory Efficient**: Bucket system limits RAM usage

## 🤝 Credits & Acknowledgments

### Core Development
- **Simon** - Primary architect and filter author
- **Zpayer** (<a href="https://github.com/RandomUser15456">GitHub</a>) - Original KoGaMa-Search implementation that inspired this project's approach

### Community Support
- **Ejota** (<a href="https://kogama.com.br/profile/1176967">Kogama Profile</a>) - Essential moderation liaison, false positive verification, and expedited reporting channel

### Translation & Localization Team
Special thanks to contributors who expanded filtering capabilities across languages:
- **Portuguese Localization**: [Contributor Name]
- **Spanish Localization**: [Contributor Name]
- **Multilingual Support**: [Contributor Name]

*Note: Add translator names as they contribute to the ```flags.json``` expansion*

## ⚠️ Ethical Use & Disclaimer

### Intended Purpose
This system is designed exclusively for:
- Platform moderation assistance
- Community safety research
- Behavioral pattern analysis
- Academic study of online communities

### Strict Prohibitions
Never use this system for:
- Targeted harassment or stalking
- Unauthorized surveillance
- Personal data exploitation
- Any illegal activities
- Violation of platform Terms of Service

### Legal Notice
The developers assume **no responsibility** for misuse of these tools. Users are solely liable for ensuring compliance with:
- Local and international laws
- Platform Terms of Service
- Data protection regulations (GDPR, CCPA, etc.)
- Ethical research guidelines

## 🔄 Project Philosophy

This project prioritizes **data integrity** over code elegance. The architecture is built for:
- **Reproducibility**: Consistent results across multiple runs
- **Auditability**: Clear data provenance and processing history
- **Resilience**: Recovery from interruptions without data loss
- **Transparency**: Understandable data structures and processing steps

The system embodies a "collect now, analyze later" approach, ensuring raw data preservation for future analytical methods not yet conceived.

---

*Last Updated: December 2025 | Version: 2.0 | Maintainer: Simon*

# PyBiographical

**Python library for biographical data management**

Utilities for managing person metadata, location data, and biographical information.

**Use Cases:**
- Person metadata management (biographical, family research)
- Artifact metadata (media tagging, document organization)
- Location data and resolution
- Fuzzy matching and duplicate detection

## Installation

### From PyPI (Recommended)

```bash
# Install the latest version
pip install pybiographical

# Install with optional fuzzy matching support
pip install pybiographical[matching]

# Install with all optional features
pip install pybiographical[full]
```

### In requirements.txt

```txt
# Basic installation
pybiographical>=0.2.0

# With fuzzy matching
pybiographical[matching]>=0.2.0

# With all features
pybiographical[full]>=0.2.0
```

### From Source (for development)

```bash
# Clone and install in editable mode
git clone https://github.com/rickhohler/PyBiographical.git
cd PyBiographical
pip install -e .[dev]
```

## Features

### RAM Disk Utilities

High-performance I/O using RAM disk for faster file operations (especially useful for cloud-synced directories).

**Setup RAM Disk:**

> **Note:** The examples below use 12GB as a reference. Adjust the size based on your use case and available RAM.

#### macOS

```bash
# Create RAM disk if it doesn't exist
if [ ! -d "/Volumes/RAMDisk" ]; then
   diskutil erasevolume HFS+ "RAMDisk" `hdiutil attach -nomount ram://25165824`
fi
```

#### Linux

```bash
# Create RAM disk using tmpfs (12GB)
sudo mkdir -p /mnt/ramdisk
sudo mount -t tmpfs -o size=12G tmpfs /mnt/ramdisk

# To make it permanent, add to /etc/fstab:
# tmpfs /mnt/ramdisk tmpfs nodev,nosuid,size=12G 0 0
```

#### Windows (PowerShell as Administrator)

```powershell
# Using ImDisk Toolkit (free, open-source)
# Download from: https://sourceforge.net/projects/imdisk-toolkit/

# Create 12GB RAM disk at drive R:
imdisk -a -s 12G -m R: -p "/fs:ntfs /q /y"

# Alternative: Use built-in with third-party tools like:
# - AMD Radeon RAMDisk
# - SoftPerfect RAM Disk
# - Dataram RAMDisk
```

**Python Usage:**
```python
from pybiographical import RAMDiskContext
from pathlib import Path

# Automatic staging and copy back
with RAMDiskContext(copy_back_to=Path("output")) as ramdisk:
    if ramdisk.available:
        # Write to ramdisk.temp_dir - very fast!
        for i in range(1000):
            output_file = ramdisk.temp_dir / f"result_{i}.json"
            output_file.write_text(f'{{"data": {i}}}')
        # Files automatically copied to "output/" on exit
```

**Performance**: 2-4x faster for Google Drive-synced directories.

## Modules

### `PyBiographical.io` - File I/O Utilities

**YAML Operations:**
```python
from pybiographical.io import load_yaml, dump_yaml, get_yaml_handler

# Load/save YAML files
data = load_yaml("person.yaml")
dump_yaml(data, "output.yaml")

# Get YAML handler for custom use
yaml = get_yaml_handler()
```

**Backup & Safety:**
```python
from pybiographical.io import create_backup, atomic_write, compute_checksum

# Create timestamped backups
backup_path = create_backup(file_path, backup_dir)

# Atomic file writes (temp + rename)
atomic_write(data, file_path)

# File checksums
checksum = compute_checksum(file_path)
```

### `PyBiographical.persons` - Person Metadata Management

**CRUD Operations:**
```python
from pybiographical.persons import PersonCRUD
from pathlib import Path

# Initialize CRUD handler
crud = PersonCRUD(
    persons_dir=Path("data/persons"),
    backup_dir=Path("data/backups"),
    archive_dir=Path("data/archive")
)

# Create person (idempotent with duplicate detection)
person = crud.create(
    given_names="Johann",
    surname="Johnson",
    birth_year=1825,
    birth_place="Harvey, ND",
    gender="Male"
)

# Read by ID
person = crud.read("I382302780374")

# Fuzzy search with confidence scoring
results = crud.search(
    surname="Johnson",
    birth_year=1825,
    fuzzy=True,
    threshold=80
)
for person, confidence in results:
    print(f"{person['name']['full_name']}: {confidence}%")

# Update with nested keys
crud.update(
    "I382302780374",
    {'vital_events.birth.date': '1825-03-15'}
)

# Delete/archive with automatic backup
crud.delete("I382302780374", archive=True)

# Restore from backup
crud.restore("I382302780374")
```

**Validation:**
```python
from pybiographical.persons import (
    validate_person_yaml,
    validate_directory,
    fix_schema_version
)

# Validate single file
issues = validate_person_yaml("person.yaml")

# Validate entire directory
results = validate_directory(Path("data/persons"))

# Auto-fix schema versions
fixed = fix_schema_version("person.yaml", make_backup=True)
```

**Models:**
```python
from pybiographical.persons import PersonFile, ValidationIssue

# Dataclasses for structured access
person_file = PersonFile(path=Path("person.yaml"), data={...})
issue = ValidationIssue(
    severity="WARNING",
    field="birth_year",
    message="Missing birth year"
)
```

### `PyBiographical.names` - Name Registry & Confidence Scoring

**Name Registry:**
```python
from pybiographical.names import NameRegistry, NameEntry

# Initialize registry
registry = NameRegistry("/path/to/metadata/data/names.json")
registry.load()

# Search with confidence scoring
results = registry.search("Schmidt", include_cognates=True)
for result in results:
    print(f"{result.entry.name}: match={result.confidence:.2f}, validity={result.name_confidence:.2f}")
    # Example output: Schmidt: match=1.00, validity=0.85
```

**Confidence Scoring:**

The Names Registry supports **two types of confidence scores**:

1. **Match Confidence** (`result.confidence`) - How well the search query matches the name (0.0-1.0)
   - `1.0` = Exact match
   - `0.9` = Spelling variant match
   - `0.8` = Cognate/cross-language match
   - `0.0-0.7` = Fuzzy/phonetic match

2. **Name Confidence** (`result.name_confidence`) - How valid the name is as a real person name (0.0-1.0)
   - Factors include etymology, language origin, geographic usage, occurrences
   - Penalties for suspicious patterns (digits, special chars, non-person patterns)
   - Range interpretation:
     - `0.8-1.0` = High quality, well-documented name
     - `0.5-0.79` = Medium quality, valid but limited documentation
     - `0.0-0.49` = Low quality, requires manual review

**Confidence Algorithm:**
```python
# Base confidence: 0.5
# Positive factors:
#   + 0.1  if has etymology
#   + 0.1  if has language_origin
#   + 0.05 per geographic_usage entry (max +0.2)
#   + 0.1  if 10+ occurrences in data
#   + 0.05 if 5-9 occurrences
# Negative factors:
#   - 0.2  if contains digits
#   - 0.2  if has special characters
#   - 0.1  if all UPPERCASE or lowercase
#   - 0.3  if matches non-person patterns (street, company, etc.)
#   - 0.2  if in stoplist (unknown, unnamed, etc.)
# Final score clamped to [0.0, 1.0]
```

**Search Operations:**
```python
# Exact name search
exact_matches = registry.search_exact("Johnson")

# Phonetic search
phonetic_matches = registry.search_phonetic("H460", method="soundex")

# Cognate search (cross-language forms)
cognates = registry.search_cognates("Schmidt")

# Find by etymology
smith_names = registry.find_by_etymology("smith")
# Returns: Smith, Schmidt, Kowalski, Herrera, etc.

# Find by language
german_names = registry.find_by_language("German")

# Find cognate group
group = registry.find_cognate_group("John")
# Returns: {"English": [John], "German": [Johann], "French": [Jean], ...}
```

**CRUD Operations:**
```python
# Create name entry
from pybiographical.names import NameEntry, GeographicUsage

entry = NameEntry(
    id="NAME-001",
    name="Johnson",
    name_type="surname",
    confidence=0.95,  # High confidence
    confidence_factors={
        'has_etymology': True,
        'has_language_origin': True,
        'geographic_usage_count': 3,
        'occurrences': 25
    }
)

registry.create(entry)

# Read
entry = registry.read("NAME-001")

# Update
entry.geographic_usage.append(
    GeographicUsage(
        location_id="LOC-12345",
        region="Baden-Württemberg, Germany",
        country="Germany",
        time_period="1800-1900",
        frequency="common"
    )
)
registry.update(entry)

# Delete
registry.delete("NAME-001")
```

**Enrichment Operations:**
```python
# Backup before changes
backup_path = registry.backup()
print(f"Backup created: {backup_path}")

# Merge geographic usage from person data
from pybiographical.names import GeographicUsage

usage = [
    GeographicUsage(
        location_id="LOC-12345",
        region="Germany",
        frequency="common",
        time_period="1850-1920"
    )
]

registry.merge_geographic_usage(
    "NAME-001",
    usage,
    merge_strategy="accumulate"  # or "replace"
)

# Update specific fields
registry.update_fields("NAME-001", {
    'confidence': 0.95,
    'notes': 'Verified from historical records'
})

# Save changes
registry.save()
```

**Statistics:**
```python
stats = registry.get_statistics()
print(f"Total names: {stats['total_entries']}")
print(f"Surnames: {stats['by_type']['surname']}")
print(f"German names: {stats['by_language']['German']}")
print(f"With etymology: {stats['with_etymology']}")
```

### `PyBiographical.matching` - Fuzzy Matching & Deduplication

**Name Matching:**
```python
from pybiographical.matching import fuzzy_match_name, normalize_name

# Fuzzy name matching (0-100 score)
score = fuzzy_match_name(
    "Hans Mueller",
    "John Johnson",
    check_alternates=["Hans"]
)

# Name normalization
clean_name = normalize_name("John Q. Public, Jr.")
# Returns: "john q public"
```

**Location Matching:**
```python
from pybiographical.matching import fuzzy_match_location, normalize_location

# Location matching with abbreviations
score = fuzzy_match_location(
    "Harvey, North Dakota",
    "Harvey, ND"
)

# Location normalization
clean_loc = normalize_location("St. Paul, MN, USA")
# Returns: "saint paul mn usa"
```

**Duplicate Detection:**
```python
from pybiographical.matching import (
    compute_match_confidence,
    get_detailed_match_breakdown
)

# Overall confidence score
confidence = compute_match_confidence(
    person1={...},
    person2={...}
)

# Detailed breakdown of match factors
breakdown = get_detailed_match_breakdown(person1, person2)
print(f"Name: {breakdown['name_score']}")
print(f"Birth year: {breakdown['birth_year_score']}")
print(f"Overall: {breakdown['overall_confidence']}")
```

**Features:**
- Uses `rapidfuzz` for fast fuzzy matching (optional dependency)
- Fallback to basic string matching if rapidfuzz unavailable
- Configurable thresholds and scoring weights
- Handles alternate spellings and nicknames

### `PyBiographical.ramdisk` - High-Performance I/O

- `RAMDisk` - RAM disk manager class
- `RAMDiskContext` - Context manager for automatic staging/cleanup
- `get_ramdisk_stats()` - Get RAM disk usage statistics
- `log_ramdisk_info()` - Log RAM disk information

## Usage in Projects

### Complete Example - Person Metadata Management

```python
from pybiographical.persons import PersonCRUD, validate_directory
from pybiographical.matching import fuzzy_match_name
from pybiographical.io import create_backup
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

# Initialize CRUD handler
crud = PersonCRUD(
    persons_dir=Path("ORGANIZED/DATA/persons"),
    backup_dir=Path("ORGANIZED/BACKUPS"),
    archive_dir=Path("ORGANIZED/ARCHIVE")
)

# Create new person with duplicate detection
try:
    person = crud.create(
        given_names="Johann",
        surname="Johnson",
        birth_year=1825,
        birth_place="Schwenningen, Baden-Württemberg, Germany",
        gender="Male",
        sources=["an online data source biographical dataset Export"],
        check_duplicates=True  # Idempotent - returns existing if 95%+ match
    )
    print(f"Created: {person['person_id']}")
except FileExistsError:
    print("Person already exists")

# Search for potential matches
matches = crud.search(
    surname="Johnson",
    given_names="Johann",
    birth_year=1825,
    fuzzy=True,
    threshold=75
)

for person, confidence in matches:
    print(f"{confidence}% - {person['name']['full_name']}")
    if confidence >= 90:
        print("  → High confidence match!")

# Validate entire directory
results = validate_directory(Path("ORGANIZED/DATA/persons"))
for result in results:
    if result.issues:
        print(f"{result.file.name}: {len(result.issues)} issues")
```

### biographical - Person Import & Matching

```python
from pybiographical.persons import PersonCRUD
from pybiographical import RAMDiskContext
from pathlib import Path

# Use RAM disk for high-performance batch operations
with RAMDiskContext(prefix="biographical", copy_back_to=Path("output")) as ramdisk:
    if ramdisk.available:
        # Initialize CRUD with RAM disk paths
        crud = PersonCRUD(
            persons_dir=ramdisk.temp_dir / "persons",
            backup_dir=ramdisk.temp_dir / "backups",
            archive_dir=ramdisk.temp_dir / "archive"
        )
        
        # Batch import from biographical dataset with duplicate detection
        for gedcom_person in gedcom_data:
            crud.create(
                given_names=gedcom_person.given_names,
                surname=gedcom_person.surname,
                birth_year=gedcom_person.birth_year,
                check_duplicates=True  # Automatic deduplication
            )
```

### metadata - Validation & Cleanup

```python
from pybiographical.persons import validate_directory, fix_schema_version
from pybiographical.io import create_backup
from pathlib import Path

# Validate all person files
persons_dir = Path("ORGANIZED/DATA/persons")
results = validate_directory(persons_dir)

# Auto-fix schema versions
for result in results:
    for issue in result.issues:
        if "schema_version" in issue.message:
            print(f"Fixing schema: {result.file.name}")
            fix_schema_version(result.file.path, make_backup=True)

# Summary
print(f"Validated {len(results)} files")
print(f"Issues found: {sum(len(r.issues) for r in results)}")
```

## Development

### Setup

```bash
# Clone repo
git clone git@github.com:username/PyBiographical.git
cd PyBiographical

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=PyBiographical --cov-report=html
```

### Code Quality

```bash
# Format code
black src/

# Lint
ruff check src/
```

## Requirements

### Core Requirements

- **Python** ≥3.8
- **ruamel.yaml** ≥0.17.0 (installed automatically)

### Optional Dependencies

- **rapidfuzz** ≥3.0.0 - For fuzzy matching features
  ```bash
  pip install pybiographical[matching]
  ```

- **Development tools** - For contributing
  ```bash
  pip install pybiographical[dev]
  ```

### Platform-Specific Features

**RAM Disk Utilities:**
- Available on macOS, Linux, and Windows
- Optional - library works without RAM disk
- See [RAM Disk Setup](#ram-disk-utilities) for platform-specific instructions

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.2.0 | 2025-11-03 | **Major Feature Release**<br>• Person metadata YAML utilities (load, dump, backup)<br>• Person metadata validation with auto-fix<br>• Fuzzy matching for names and locations<br>• PersonCRUD class with full CRUD operations<br>• Duplicate detection and confidence scoring<br>• Archive/restore functionality<br>• Optional rapidfuzz dependency for performance |
| 0.1.0 | 2025-11-03 | Initial release with RAM disk utilities |

## Project Tracking

All development, features, and issues are tracked using GitHub Projects:

**[PyBiographical Project Board](https://github.com/users/rickhohler/projects/29)**

This includes:
- Feature roadmap
- Bug tracking
- Enhancement requests
- Release planning
- Documentation tasks

### AI-Assisted Development

When using AI agents for development:

1. **Create issues** in GitHub Projects with clear descriptions
2. **Pull issues** into AI context using the sync script in `PyBiographicalAI` repo
3. **Work on issues** with full project context
4. **Update issues** via `gh` CLI as work progresses
5. **Close issues** when complete

See the `PyBiographicalAI` repository for scripts and documentation.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards, and how to submit pull requests.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Support

For issues or questions:
- **GitHub Issues**: [Create an issue](https://github.com/rickhohler/PyBiographical/issues)
- **GitHub Discussions**: [Join the discussion](https://github.com/rickhohler/PyBiographical/discussions)
- **Project Board**: [View progress](https://github.com/users/rickhohler/projects/29)

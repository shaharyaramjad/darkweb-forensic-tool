# Data Folder Structure

This folder contains test data and generated content for the dark web forensic tool.

## Folder Structure

```
data/
├── README.md                    # This file
├── test_samples/                # Manual test HTML files (gitignored)
├── generated_pages/             # Auto-generated test pages (gitignored)
└── darkweb_test_pages/         # Legacy test pages (gitignored)
```

## Git Ignore Rules

The following files and folders are excluded from git:

- `*.html` - All HTML test files
- `darkweb_test_pages/` - Generated test pages
- `forum_sample.csv` - Dataset samples
- `darkweb_test_sample.html` - Test samples
- `test_rag_edge_cases.html` - Edge case tests

## Usage

- **Manual Testing:** Place HTML files in `test_samples/` for manual testing
- **Generated Testing:** Auto-generated pages go in `generated_pages/`
- **Dataset Samples:** Large dataset files should be in `dataset/` folder

## Note

All test data is excluded from git to keep the repository clean and avoid committing large files. 
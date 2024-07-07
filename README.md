# mdsphinx

Convert markdown to any output format that Sphinx supports.

# Installation

```bash
pipx install mdsphinx
```

# Usage

```bash
cd ./example
mdsphinx env create
mdsphinx process example.md --to pdf
mdsphinx process example.md --to html
mdsphinx process example.md --to confluence
```

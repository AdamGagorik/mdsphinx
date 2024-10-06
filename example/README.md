# Examples

## 1

This example demonstrates rendering a single Markdown file.

```bash
cd /path/to/example/1

# Render to Confluence
mdsphinx process example.md --to confluence --using default

# Render to PDF
mdsphinx process example.md --to pdf --using latex --as example.pdf --show-output

# Render to HTML
mdsphinx process example.md --to html --using single.page --as example.html --show-output
```

## 2

This example demonstrates rendering multiple Markdown files in a directory.

```bash
cd /path/to/example/2

# Render to Confluence
mdsphinx process directory --to confluence --using default

# Render to PDF
mdsphinx process directory --to pdf --using latex --as example.pdf --show-output

# Render to HTML
mdsphinx process directory --to html --using single.page --as example.html --show-output
```

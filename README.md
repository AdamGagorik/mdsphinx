# [mdsphinx](https://pypi.org/project/mdsphinx)

Convert markdown to any output format that Sphinx supports.

In contrast to something like pandoc, this tool is useful if you want to...

1) Use Jinja2 templating.
2) Use MyST Markdown syntax.
3) Use other Sphinx extensions.
4) Push Markdown to a Confluence page.

## Installation

```bash
pipx install mdsphinx
```

## Usage

1. Create a markdown file or directory with markdown files.
2. Run `mdsphinx env create` to create the default environment.
3. Optionally, create a `conf.py.jinja` file to customize the Sphinx `conf.py`.
4. Optionally, create a `context.yml` file with variables to be injected via Jinja2.
5. Run `mdsphinx process <inp> --to <fmt> --using <preset> --as <out>` to convert the markdown.

### TLDR

```bash
mdsphinx env create
mdsphinx process input.md --to pdf --using latex
```

You can also process a directory of markdown files.

```bash
mdsphinx process ./inputs --to pdf --using latex --as output.pdf
```

## Output Formats

There are a few different formats you can convert to:

```bash
mdsphinx process input.md --to pdf        --using latex
mdsphinx process input.md --to html       --using default
mdsphinx process input.md --to confluence --using single.page
```

## Environments

The default environment installs the following packages:

- `sphinx`
- `nbsphinx`
- `myst-parser`
- `sphinxcontrib-confluencebuilder`

However, you can register any virtual environment you want to use as long as it contains `sphinx`.

```bash
mdsphinx env add --name my_custom_env --path /path/to/my_custom_env
mdsphinx process input.md --to pdf --using latex --env-name my_custom_env
```

Environments and metadata are stored in the `$MDSPHINX_CONFIG_ROOT`, which defaults to `~/.config/mdsphinx`.

> You can safely delete this directory at any time.

## Jinja2 Templating

Create a file named `context.yml` parallel to the input file or directory.

```yaml
a: 1
b: 2
```

You can then reference these variables in your markdown files.

```markdown
{{ a }} + {{ b }} = {{ a + b }}
```

Support for Mermaid diagrams is available as a custom `jinja2` block.

> You must have `docker` installed and ideally be using the `MyST` parser.

```jinja2
{% mermaid -%}
ext: .png
mode: myst
scale: 3
width: 75
align: center
caption: |
    An example mermaid diagram!
diagram: |
    graph TD
        A --> B
        B --> C
        A --> C
{% endmermaid %}
```

Likewise, you can use the `tikz` block to render LaTeX diagrams.

> You must have `tectonic` installed and ideally be using the `MyST` parser.

```jinja2
{% tikz -%}
ext: .png
mode: myst
diagram: |
    \documentclass[margin=0pt]{standalone}
    \usepackage{tikz}
    \begin{document}
    \begin{tikzpicture}
        \draw (0,0) -- (1,1);
    \end{tikzpicture}
    \end{document}
{% endtikz %}
```

## Sphinx Configuration

Create a file named `conf.py.jinja` parallel to the input file or directory.

```jinja2
{% include main_sphinx_config %}

html_theme = "alabaster"
```

You can generate a copy of the default `conf.py.jinja` file.

```bash
mdsphinx generate conf.py.jinja
````

This file will be used by `sphinx-quickstart` to generate the Sphinx configuration file.

## Confluence Configuration

The default Sphinx `conf.py` sets up a confluence connection by reading your `~/.netrc` and environment variables.

| Sphinx `conf.py` Variable   | Default Source        | Environment Variable Name   | Example Value                        |
|-----------------------------|-----------------------|-----------------------------|--------------------------------------|
| `confluence_publish_dryrun` | `env`                 | `CONFLUENCE_PUBLISH_DRYRUN` | `1`                                  |
| `confluence_server_url`     | `env`                 | `CONFLUENCE_SERVER_URL`     | `https://example.atlassian.net/wiki` |
| `confluence_server_user`    | `netrc[url].login`    | `CONFLUENCE_SERVER_USER`    | `example@gmail.com`                  |
| `confluence_api_token`      | `netrc[url].password` | `CONFLUENCE_API_TOKEN`      | `api-token`                          |
| `confluence_space_key`      | `env`                 | `CONFLUENCE_SPACE_KEY`      | `~MySpace`                           |
| `confluence_parent_page`    | `env`                 | `CONFLUENCE_PARENT_PAGE`    | `ParentPage`                         |

Obtain an API token from your Atlassian account settings and configure your `~/.netrc` file:

```plaintext
machine <confluence_server_url>
  login <confluence_server_user>
  password <confluence_api_token>
```

Create a parent page manually on your confluence space and configure the environment variables.

```bash
export CONFLUENCE_PUBLISH_DRYRUN="0"
export CONFLUENCE_SERVER_URL="https://example.atlassian.net/wiki"
export CONFLUENCE_SPACE_KEY="~MySpace"
export CONFLUENCE_PARENT_PAGE="ParentPage"
mdsphinx process input.md --to confluence --using single.page
```

## LaTeX Configuration

The default LaTeX configuration is set up to use `tectonic` as the LaTeX engine.

However, you can set `MDSPHINX_LATEX_COMMAND` to be a `;` delimited list of commands to run instead.

```bash
export MDSPHINX_LATEX_COMMAND="xelatex {tex}"
```

## Pandoc Configuration

The `pandoc` tool is required to export generated `html` to a single file.

## Mermaid Diagrams

Experimental support for Mermaid diagrams is available as a custom `jinja2` block.
You must have `docker` installed and ideally by using the `MyST` parser.

```jinja2
{% mermaid width=75, caption="An example mermaid diagram" -%}
graph TD
    A --> B
    B --> C
    A --> C
{% endmermaid %}
```

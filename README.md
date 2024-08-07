# mdsphinx

Convert markdown to any output format that Sphinx supports.

## Installation

```bash
pipx install mdsphinx
```

## Usage

```bash
cd ./example
mdsphinx env create
mdsphinx process input.md --to pdf        --using latex
mdsphinx process input.md --to html       --using default
mdsphinx process input.md --to confluence --using single.page
mdsphinx process ./inputs --to html       --using single.page --tmp-root . --reconfigure --show-output --env-name default
```

## Sphinx Configuration

You can alter the default Sphinx `conf.py` file generated by `sphinx-quickstart` by adding `conf.py.jinja` parallel to the input file or directory.

```jinja2
{% include main_sphinx_config %}

html_theme = "alabaster"
```

## Confluence Configuration

The default Sphinx `conf.py` tries to set up a confluence connection by reading your `~/.netrc` and environment variables.

| Sphinx `conf.py` Variable   | Default Source             | Environment Variable Name   | Example Value                        |
|-----------------------------|----------------------------|-----------------------------|--------------------------------------|
| `confluence_publish_dryrun` | `env`                      | `CONFLUENCE_PUBLISH_DRYRUN` | `1`                                  |
| `confluence_server_url`     | `env`                      | `CONFLUENCE_SERVER_URL`     | `https://example.atlassian.net/wiki` |
| `confluence_server_user`    | `netrc[url].login` > `env` | `CONFLUENCE_SERVER_USER`    | `example@gmail.com`                  |
| `confluence_api_token`      | `netrc[url].password`      | `CONFLUENCE_API_TOKEN`      | `api-token`                          |
| `confluence_space_key`      | `env`                      | `CONFLUENCE_SPACE_KEY`      | `~MySpace`                           |
| `confluence_parent_page`    | `env`                      | `CONFLUENCE_PARENT_PAGE`    | `ParentPage`                         |

- Obtain an API token from your Atlassian account settings and configure your `~/.netrc` file:

```plaintext
machine <confluence_server_url>
  login <confluence_server_user>
  password <confluence_api_token>
```

- Create a parent page manually on your confluence space and set your environment variables before running `mdsphinx`:

```bash
export CONFLUENCE_PUBLISH_DRYRUN="0"
export CONFLUENCE_SERVER_URL="https://example.atlassian.net/wiki"
export CONFLUENCE_SPACE_KEY="~MySpace"
export CONFLUENCE_PARENT_PAGE="ParentPage"
mdsphinx process input.md --to confluence --using single.page
```

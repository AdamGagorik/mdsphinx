# Section-A

- The current date is {{ date }}.
- The current time is {{ time }}.

# Section-B

Some **text**!

# Example Table

|A|B|
|-|-|
|0|1|

# Example Admonition

:::{note}
This is a note admonition. You can put any Markdown content inside.
:::

:::{warning}
Be careful! This is a warning admonition.
:::

:::{tip}
Here's a helpful tip for you!
:::

{% mermaid -%}
ext: .png
mode: myst
align: center
width: 10%
align: center
caption: |
    This is a mermaid diagram.
diagram: |
    graph TD
        A --> B
        B --> C
        A --> C
{% endmermaid %}

{% tikz -%}
ext: .png
name: test
mode: myst
width: 25%
align: center
caption: |
    This is a TikZ diagram.
diagram: |
    \coordinate (SE) at (0,0) {};
    \coordinate (NW) at (5,5) {};
    \draw (SE) rectangle (NW);
    \node[draw, rectangle, anchor=south west] at (SE) {SE};
    \node[draw, rectangle, anchor=north east] at (NW) {NW};
tikz_options:
    - remember picture
    - scale=4
{% endtikz %}

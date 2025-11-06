[![Upload Python Package](https://github.com/GrafLearnt/HTMLight/actions/workflows/python-publish.yml/badge.svg)](https://github.com/GrafLearnt/HTMLight/actions/workflows/python-publish.yml) ![PyPI version](https://badge.fury.io/py/HTMLight.svg) ![Python Versions](https://img.shields.io/pypi/pyversions/HTMLight.svg) [![HTMLight](https://snyk.io/advisor/python/HTMLight/badge.svg)](/advisor/python/HTMLight)

# Abstract

Light html generator

# Install

```bash
pip3 install htmlight
```

## Disclaimer

Despite htmlight is able to generate full html page, it is designed to generate small fragments of code like:

```python
from htmlight import h
from flask_babel import lazy_gettext
from flask_login import current_user


TEMPLATE = h.div(h.hr(), h.span("{hello} {username}"), h.hr())


def get_html():
    return TEMPLATE.format(hello=lazy_gettext("Hello"), username=current_user.name)

```

#### or

```python
from htmlight import h
from flask_babel import lazy_gettext
from flask_login import current_user


def get_html():
    return h.div(h.hr(), h.span(lazy_gettext("Hello"), " ", current_user.name), h.hr()))
```

## Usage

### Code

```python
from htmlight import h


landing_page = h.html(
    h.head(
        h.title("Welcome to Our Website"),
        h.link(rel="stylesheet", href="styles.css"),
    ),
    h.body(
        h.header(
            h.h1(
                "Welcome to Our Website",
                style=(
                    " color:"
                    " #333;"
                    " text-align:"
                    " center;"
                    " background-color:"
                    " #F0F0F0;"
                    " padding: 20px;"
                ),
            ),
            h.p(
                "Explore our amazing content",
                style="font-size: 20px; color: #555;",
            ),
        ),
        h.main(
            h.h2("Featured Articles", style="color: #444; text-align: center;"),
            h.article(
                h.h3("Article 1", style="color: #0072d6;"),
                h.p("This is the first article content", style="color: #666;"),
            ),
            h.article(
                h.h3("Article 2", style="color: #00a86b;"),
                h.p("This is the second article content", style="color: #666;"),
            ),
        ),
        h.footer(
            h.p(
                "© 2023 Our Website",
                style=(
                    "text-align: center;"
                    " background-color: #333;"
                    " color: #fff;"
                    " padding: 10px;"
                    " flex-shrink: 0;"
                    " background-color: #333;"
                    " position: absolute;"
                    " left: 0;"
                    " bottom: 0;"
                    " width: 100%;"
                    " overflow: hidden;"
                ),
            ),
        ),
    ),
    style="background-color: #f2f2f2; font-family: Arial, sans-serif;",
)

with open("landing_page.html", "w") as f:
    f.write(landing_page)
```

### Result page

![Result](assets/example.png?raw=true)

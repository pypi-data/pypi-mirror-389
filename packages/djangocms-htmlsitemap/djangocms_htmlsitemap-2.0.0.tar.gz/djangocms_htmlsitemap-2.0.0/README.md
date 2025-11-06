# djangocms-htmlsitemap

[![Latest Version](http://img.shields.io/pypi/v/djangocms-htmlsitemap.svg?style=flat-square)](https://pypi.python.org/pypi/djangocms-htmlsitemap/)
[![License](http://img.shields.io/pypi/l/djangocms-htmlsitemap.svg?style=flat-square)](https://pypi.python.org/pypi/djangocms-htmlsitemap/)


*A Django CMS plugin for building HTML sitemaps showing organized lists of CMS pages.*

## Requirements

Python 3.8.1+, Django 2.2+, Django-CMS 4.1+.

Starting from v2.0, the plugin only supports django CMS 4.1 and above.
For django CMS 3.x, use version 1.x.x.

## Installation

Just run:
```sh
pip install djangocms-htmlsitemap
```

Once installed you just need to add `djangocms_htmlsitemap` to `INSTALLED_APPS` in your project's settings module:
```py
INSTALLED_APPS = (
    # other apps
    'djangocms_htmlsitemap',
)
```

Then install the models:
```py
python manage.py migrate djangocms_htmlsitemap
```

*Congrats! You’re in.*

## Authors

Kapt <dev@kapt.mobi> and [contributors](https://github.com/kapt-labs/djangocms-htmlsitemap/contributors)

## License

BSD. See `LICENSE` for more details.

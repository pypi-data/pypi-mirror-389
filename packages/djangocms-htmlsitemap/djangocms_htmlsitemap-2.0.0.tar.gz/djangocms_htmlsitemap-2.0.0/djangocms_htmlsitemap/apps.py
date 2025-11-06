# Django
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HtmlSitemapConfig(AppConfig):
    name = "djangocms_htmlsitemap"
    verbose_name = _("HTML Sitemap")
    default_auto_field = "django.db.models.AutoField"

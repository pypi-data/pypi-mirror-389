# Django
from django.db import models
from django.utils.translation import gettext_lazy as _

# Third party
from cms.models import CMSPlugin


class HtmlSitemapPluginConf(CMSPlugin):
    min_depth = models.PositiveIntegerField(verbose_name=_("Minimum depth"), default=0)
    max_depth = models.PositiveIntegerField(
        verbose_name=_("Maximum depth"), blank=True, null=True
    )
    in_navigation = models.BooleanField(
        verbose_name=_("In navigation"), default=None, null=True
    )

    class Meta:
        verbose_name = _("HTML Sitemap plugin configuration")
        verbose_name_plural = _("HTML Sitemap plugin configurations")

    def __str__(self):
        return f"Django-CMS HTML Sitemap #{self.pk}"

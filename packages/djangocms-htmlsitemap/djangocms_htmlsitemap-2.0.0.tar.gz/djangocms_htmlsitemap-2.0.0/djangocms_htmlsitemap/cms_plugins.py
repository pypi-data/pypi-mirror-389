# Django
from django.contrib.sites.models import Site
from django.db.models import Exists, OuterRef
from django.utils.translation import gettext_lazy as _

# Third party
from cms.models.contentmodels import PageContent
from cms.models.pagemodel import Page
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from treebeard.models import Node

# Local application / specific library imports
from .models import HtmlSitemapPluginConf


class HtmlSitemapPlugin(CMSPluginBase):
    model = HtmlSitemapPluginConf
    name = _("HTML Sitemap")

    render_template = "djangocms_htmlsitemap/sitemap.html"

    def render(self, context, instance, placeholder):
        request = context["request"]
        language = request.LANGUAGE_CODE

        site = Site.objects.get_current()
        pages = Page.objects.on_site(site).filter(
            login_required=False, depth__gte=instance.min_depth
        )

        if instance.max_depth:
            pages = pages.filter(depth__lte=instance.max_depth)

        pages = pages.annotate(
            is_published=Exists(
                PageContent.objects.filter(page=OuterRef("pk"), language=language)
            )
        ).filter(is_published=True)

        if instance.in_navigation is not None:
            pages = pages.filter(pagecontent_set__in_navigation=instance.in_navigation)

        pages = pages.distinct()

        # nodes = [page for page in pages.select_related("node")]
        annotated_list_qs = Node.get_annotated_list_qs(pages)
        ordered_pages = [
            (page, annotated_list_qs[index][1]) for index, page in enumerate(pages)
        ]

        context["pages"] = pages
        context["instance"] = instance
        context["ordered_pages"] = ordered_pages

        return context


plugin_pool.register_plugin(HtmlSitemapPlugin)

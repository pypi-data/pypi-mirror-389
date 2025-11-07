from cms.toolbar_base import CMSToolbar
from cms.toolbar_pool import toolbar_pool
from cms.utils.urlutils import admin_reverse
from django.utils.translation import gettext_lazy as _

from .models import Config


@toolbar_pool.register
class CommonCatalogToolbar(CMSToolbar):

    supported_apps = ['common_catalog']

    def populate(self):
        if not self.is_current_app:
            return

        label = _('Common Catalog')
        config = None
        if "common_catalog" in self.request.resolver_match.app_names:
            config = Config.objects.filter(namespace__in=self.request.resolver_match.namespaces).first()
            name = " ".join(self.request.resolver_match.namespaces) if config is None else str(config)
            label = f"{label} – {name}"

        menu = self.toolbar.get_or_create_menu('common_catalog_cms_integration-common_catalog', label)

        user = getattr(self.request, 'user', None)
        change_config_perm = user is not None and user.has_perm('common_catalog.change_config')
        change_perm = user is not None and user.has_perm('common_catalog.change_catalogitem')
        delete_perm = user is not None and user.has_perm('common_catalog.delete_catalogitem')
        add_perm = user is not None and user.has_perm('common_catalog.add_catalogitem')

        if config is not None and change_config_perm:
            url = admin_reverse('common_catalog_config_change', kwargs={"object_id": config.pk})
            menu.add_modal_item(_('Configure addon'), url=url)
            menu.add_break()

        if change_perm or delete_perm or add_perm:
            menu.add_modal_item(_('Items list'), url=admin_reverse('common_catalog_catalogitem_changelist'))
        if add_perm:
            menu.add_modal_item(_('Add a new item'), url=admin_reverse('common_catalog_catalogitem_add'))

        if self.request.resolver_match.url_name == 'item' and 'common_catalog' in self.request.resolver_match.app_names:
            object_id = self.request.resolver_match.kwargs.get("pk")
            if object_id:
                if change_perm:
                    url = admin_reverse('common_catalog_catalogitem_change', kwargs={"object_id": object_id})
                    menu.add_modal_item(_('Edit item'), url=url, active=True)
                if delete_perm:
                    url = admin_reverse('common_catalog_catalogitem_delete', kwargs={"object_id": object_id})
                    menu.add_modal_item(_('Delete item'), url=url)

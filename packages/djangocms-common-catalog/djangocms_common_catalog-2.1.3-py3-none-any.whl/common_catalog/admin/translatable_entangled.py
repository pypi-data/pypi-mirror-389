from django.forms.models import ModelFormMetaclass
from django.utils.translation import gettext_lazy as _
from entangled.forms import EntangledFormMetaclass, EntangledModelForm
from parler.forms import TranslatableModelForm, TranslatableModelFormMetaclass, _get_mro_attribute

from ..models import Attribute, AttributeType, CatalogItem
from .fields import AttributesFormField

MODELS = {
    "AttributeForm": Attribute,
    "AttributeTypeForm": AttributeType,
    "CatalogItemForm": CatalogItem,
}


class FixMetaModelMetaclass(ModelFormMetaclass):
    """Fix Meta has no attribute 'model'."""

    def __new__(mcs, name, bases, attrs):
        form_meta = _get_mro_attribute(bases, "_meta")
        if form_meta:
            form_new_meta = attrs.get("Meta", form_meta)
            if form_new_meta:
                first_base_name = bases[0].__name__
                if first_base_name in MODELS:
                    # Fix type object 'Meta' has no attribute 'model'.
                    # https://github.com/django-parler/django-parler/blob/v2.3/parler/forms.py#L254
                    form_new_meta.model = MODELS[first_base_name]
        return super().__new__(mcs, name, bases, attrs)


class CommonCatalogEntangledTranslatableMetaclass(
    EntangledFormMetaclass, FixMetaModelMetaclass, TranslatableModelFormMetaclass
):
    """Metaclass for admin form."""


class CommonCatalogEntangledTranslatableModelForm(
    EntangledModelForm,
    TranslatableModelForm,
    metaclass=CommonCatalogEntangledTranslatableMetaclass,
):
    """Model form with entangled and translatable fields."""

    extra_tag_attrs = AttributesFormField(label=_("Other HTML tag attributes"))

    class Meta:
        model = AttributeType
        entangled_fields = {"attributes": ["extra_tag_attrs"]}

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data["attributes"]:
            del cleaned_data["attributes"]
        return cleaned_data

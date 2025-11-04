from typing import Dict

from NEMO.decorators import customization
from NEMO.exceptions import InvalidCustomizationException
from NEMO.models import Tool
from NEMO.views.customization import CustomizationBase
from django.core.exceptions import ValidationError
from django.core.validators import validate_comma_separated_integer_list


# Class for Tool Categories that can be used for autocomplete
class ToolCategory(object):
    def __init__(self, name):
        self.name = name
        self.id = name

    def __str__(self):
        return self.name

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, ToolCategory):
            return self.id == other.id
        return False


@customization("hydra", "Hydra")
class HydraCustomizations(CustomizationBase):
    variables = {"hydra_excluded_tools": "", "hydra_excluded_tool_categories": ""}

    def validate(self, name, value):
        if name == "hydra_excluded_tools" and value:
            validate_comma_separated_integer_list(value)

    def context(self) -> Dict:
        # Override to add list of tools
        dictionary = super().context()
        categories = set()
        for cat in Tool.objects.filter(visible=True).order_by("_category").values_list("_category").distinct():
            parts = cat[0].split("/")
            prefixes = ["/".join(parts[: i + 1]) for i in range(len(parts))]
            for category in prefixes:
                categories.add(ToolCategory(category))
        dictionary["tools"] = Tool.objects.all()
        dictionary["selected_tools"] = Tool.objects.filter(id__in=self.get_list_int("hydra_excluded_tools"))
        dictionary["categories"] = sorted(categories, key=lambda x: str(x))
        dictionary["selected_categories"] = self.get_list("hydra_excluded_tool_categories")
        return dictionary

    def save(self, request, element=None) -> Dict[str, Dict[str, str]]:
        errors = super().save(request, element)
        exclude_tools = ",".join(request.POST.getlist("hydra_tool_list", []))
        try:
            self.validate("hydra_excluded_tools", exclude_tools)
            type(self).set("hydra_excluded_tools", exclude_tools)
        except (ValidationError, InvalidCustomizationException) as e:
            errors["hydra_excluded_tools"] = {"error": str(e.message or e.msg), "value": exclude_tools}
        exclude_categories = ",".join(request.POST.getlist("hydra_category_list", []))
        try:
            self.validate("hydra_excluded_tool_categories", exclude_categories)
            type(self).set("hydra_excluded_tool_categories", exclude_categories)
        except (ValidationError, InvalidCustomizationException) as e:
            errors["hydra_excluded_tool_categories"] = {"error": str(e.message or e.msg), "value": exclude_categories}
        return errors

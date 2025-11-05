from django.contrib import admin
from django.contrib.admin.options import csrf_protect_m
from django.contrib.admin.options import BaseModelAdmin


class Button(object):

    def __init__(
        self, href, title, target=None, classes=None, icon=None, data=None, **kwargs
    ):
        self.href = href
        self.title = title
        self.target = target or ""
        self.classes = []
        self.icon = icon or ""
        self.data = data or ""
        self.add_classes(classes=classes)
        self.add_classes(classes=kwargs.get("klass", None))

    @classmethod
    def from_dict(cls, data):
        item = cls(**data)
        return item

    def add_classes(self, classes):
        if isinstance(classes, (list, tuple, set)):
            for klass in classes:
                if not klass in self.classes:
                    self.classes.append(klass)
        elif isinstance(classes, str):
            for klass in classes.split():
                if not klass in self.classes:
                    self.classes.append(klass)
        return self.classes


class DjangoChangelistToolbarAdmin(admin.ModelAdmin):

    @csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update(
            {
                "django_changelist_toolbar_buttons": self.get_changelist_toolbar_buttons(
                    request
                )
            }
        )
        return super().changelist_view(request, extra_context)

    def get_changelist_toolbar_buttons(self, request):
        buttons = []
        django_changelist_toolbar_buttons = getattr(
            self,
            "django_changelist_toolbar_buttons",
            [],
        )
        for button in django_changelist_toolbar_buttons:
            buttons.append(self.make_changelist_toolbar_button(button, request))
        return buttons

    def make_changelist_toolbar_button(self, button, request):
        if not isinstance(button, Button):
            if isinstance(button, str):
                target = getattr(self, button, None)
                if target:
                    button = target
                else:
                    button = Button(button, button)
            if callable(button):
                result = button(request)
                if isinstance(result, Button):
                    button = result
                elif isinstance(result, dict):
                    button = Button.from_dict(result)
                elif isinstance(result, str):
                    href = result
                    title = getattr(button, "title", href)
                    target = getattr(button, "target", None)
                    klass = getattr(button, "klass", None)
                    classes = getattr(button, "classes", [])
                    icon = getattr(button, "icon", None)
                    data = getattr(button, "data", None)
                    button = Button(
                        href=href,
                        title=title,
                        target=target,
                        classes=classes,
                        icon=icon,
                        data=data,
                        klass=klass,
                    )
                elif isinstance(result, Button):
                    button = result
        if not isinstance(button, Button):
            raise RuntimeError(
                "make_changelist_toolbar_button无法将以下数据转化为Button类型: {0}".format(
                    button
                )
            )
        info = {
            "href": button.href,
            "title": button.title,
            "target": button.target,
            "classes": button.classes,
            "icon": button.icon,
            "data": button.data,
        }
        return info

    class Media:
        css = {
            "all": [
                "fontawesome/css/all.min.css",
                "django-changelist-toolbar-admin/css/django-changelist-toolbar-admin.css",
            ]
        }

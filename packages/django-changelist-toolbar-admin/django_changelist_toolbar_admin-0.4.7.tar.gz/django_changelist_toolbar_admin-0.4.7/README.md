# django-changelist-toolbar-admin

Provides custom button management function on changelist page of django admin site.

## Install

```shell
pip install django-changelist-toolbar-admin
```

## Usage

**pro/settings.py**

```python
INSTALLED_APPS = [
    ...
    'django_static_fontawesome',
    'django_changelist_toolbar_admin',
    ...
]
```

- django_static_fontawesome is required, for already include the fontawesome css in Media's css settings.

**app/admin.py**

```python
from django.contrib import admin
from django_changelist_toolbar_admin.admin import DjangoChangelistToolbarAdmin
from .models import Category


class CategoryAdmin(DjangoChangelistToolbarAdmin, admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]

    django_changelist_toolbar_buttons = [
        "export_button",
        "say_hi_button",
    ]

    def export_button(self, request):
        return "/export"
    export_button.title = "Export"
    export_button.icon = "fas fa-file-export"
    export_button.target = "_blank"
    
    def say_hi_button(self, request):
        return {
            "href": "javascript:alert('hi');",
            "title": "Say Hi",
            "icon": "fas fa-music",
        } 

admin.site.register(Category, CategoryAdmin)
```

- A button function must returns a Button instance, dict button info, or href.
- Another way is override `make_changelist_toolbar_button` get return the final buttons.

## Releases

### v0.4.7

- Doc update.

### v0.4.6

- Add data attr for toolbar button.

### v0.4.5

- Add button classes support.

### v0.4.3

- Doc update.
- Add django-app-requires support.

### v0.4.0

- Fix document.
- Rename configuration item `changelist_toolbar_buttons` to `django_changelist_toolbar_buttons`.

### v0.3.0

- The main class rename to DjangoChangelistToolbarAdmin. Mixin is a very simple abstract class that provides helper functions, but DjangoChangelistToolbarAdmin is complex base admin, so we remove the mixin suffix.

### v0.2.0

- App rename to django_changelist_toolbar_admin.

### v0.1.0

- First release.

# django‑allauth‑xui

[![CI](https://github.com/youzarsiph/django-allauth-xui/actions/workflows/ci.yml/badge.svg)](https://github.com/youzarsiph/django-allauth-xui/actions/workflows/ci.yml)
[![CD](https://github.com/youzarsiph/django-allauth-xui/actions/workflows/cd.yml/badge.svg)](https://github.com/youzarsiph/django-allauth-xui/actions/workflows/cd.yml)
[![Code Style: Black](https://github.com/youzarsiph/django-allauth-xui/actions/workflows/black.yml/badge.svg)](https://github.com/youzarsiph/django-allauth-xui/actions/workflows/black.yml)
[![Code Linting: Ruff](https://github.com/youzarsiph/django-allauth-xui/actions/workflows/ruff.yml/badge.svg)](https://github.com/youzarsiph/django-allauth-xui/actions/workflows/ruff.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/django-allauth-xui?logo=pypi&logoColor=white)](https://pypi.org/project/django-allauth-xui/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-allauth-xui?logo=python&logoColor=white)](https://pypi.org/project/django-allauth-xui/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/django-allauth-xui?logo=pypi&logoColor=white)](https://pypi.org/project/django-allauth-xui/)
[![PyPI - License](https://img.shields.io/pypi/l/django-allauth-xui?logo=pypi&logoColor=white)](https://pypi.org/project/django-allauth-xui/)

---

## Overview

**django‑allauth‑xui (XUI)** provides a modern, responsive UI layer for [django‑allauth](https://docs.allauth.org/en/latest/introduction/index.html), styled with **Tailwind CSS** and **daisyUI**.  

It’s designed to give authentication flows a clean, contemporary look out of the box, while remaining fully customizable for your brand and product.

## Why XUI?

XUI stands for a flexible, modern UI layer you can shape to your product. The “X” is intentional — a variable you can define.

- **Modern:** Tailwind CSS and daisyUI deliver contemporary, accessible patterns out of the box.
- **Professional:** Clean layouts, sensible defaults, and production‑ready flows that fit real teams.
- **Customizable:** Override templates, extend blocks, and adapt components to your brand.
- **Theme‑able:** Switch between 35+ built‑in themes or roll your own in minutes.
- **Variable (“X”):** X is yours to define — from styling and UX to integrations and workflows.

---

## Key Features

- **Modern UI** — TailwindCSS + daisyUI styling  
- **35+ Built‑in Themes** — all daisyUI themes included  
- **Custom Themes** — create and apply your own in minutes  
- **CI/CD Ready** — GitHub Actions pipelines for testing and deployment  

---

## Screenshots

![Profile](https://github.com/user-attachments/assets/3014eadd-dcde-48ce-a18d-4424a07efdae)
![Login](https://github.com/user-attachments/assets/1722486c-98f1-4f43-bf96-720589aa968c)
![Sign up](https://github.com/user-attachments/assets/3e0ffd63-651a-47cc-8e7f-cee5381669c9)
![Email](https://github.com/user-attachments/assets/71549ddd-5066-489e-aa4e-6e0128f89ba2)
![Password](https://github.com/user-attachments/assets/9b84612f-281e-4f74-8361-a4cbf38ab177)
![2FA](https://github.com/user-attachments/assets/6a79fd57-ac5e-4d62-bbb6-9e89519f4583)

---

## Quick Start

First, install the package (after setting up `django‑allauth`):

```bash
pip install django-allauth-xui
```

Add to `INSTALLED_APPS` (order matters):

```python
INSTALLED_APPS = [
    ...
    "allauth_xui",
    "allauth",
    "allauth.account",
    ...
]
```

Include the URLs:

```python
from django.urls import path, include

urlpatterns = [
    ...
    path("accounts/", include("allauth.urls")),
    path("accounts/", include("allauth_xui.urls")),
    ...
]
```

---

## Customization

XUI is designed to be extended. To override layouts:

```bash
mkdir -p your_app/templates/allauth/layouts
touch your_app/templates/allauth/layouts/base.html
```

Then extend the base template:

```html
{% extends "allauth/layouts/base.html" %}
```

### Add Your Brand

```html
{% extends "allauth/layouts/base.html" %}{% load i18n static %}

<!-- Brand in Navbar -->
{% block branding %}
<li
  class="tooltip tooltip-right rtl:tooltip-left tooltip-primary md:hidden"
  data-tip="{% trans 'YOUR_BRAND' %}"
>
  <a
    href="{% url 'account_profile' %}"
    class="btn btn-square btn-primary lg:btn-lg 2xl:btn-lg"
  >
    <img
      alt="{% trans 'YOUR_BRAND' %}"
      src="{% static 'path/to/your/logo.png' %}"
      class="size-6 lg:size-8 2xl:size-10"
    />
    <span class="sr-only">{% trans 'YOUR_BRAND' %}</span>
  </a>
</li>
{% endblock %}

<!-- Brand in Drawer Menu -->
{% block drawer_branding %}
<li
  class="tooltip tooltip-right rtl:tooltip-left tooltip-primary"
  data-tip="{% trans 'YOUR_BRAND' %}"
>
  <a
    href="{% url 'account_profile' %}"
    class="btn btn-square btn-primary lg:btn-lg 2xl:btn-lg"
  >
    <img
      alt="{% trans 'YOUR_BRAND' %}"
      src="{% static 'path/to/your/logo.png' %}"
      class="size-6 lg:size-8 2xl:size-10"
    />
    <span class="sr-only">{% trans 'YOUR_BRAND' %}</span>
  </a>
</li>
{% endblock %}

<!-- Links in sidebar -->
{% block user_links %}
<li
  class="is-drawer-close:tooltip is-drawer-close:tooltip-right rtl:is-drawer-close:tooltip-left"
  data-tip="{% trans 'Home' %}"
>
  <a href="https://your.domain.com/">
    <i data-lucide="home" class="size-4 lg:size-6"></i>
    <span class="is-drawer-close:sr-only">
      {% trans 'Home' %}
    </span>
  </a>
</li>
...
{% endblock %}
```

### Themes

- **Switch themes:**

```html
{% block theme %}silk{% endblock %}
{% block toggle_theme %}luxury{% endblock %}
```

- **Remove theme controls:**

```html
{% block theme_selector %}{% endblock %}
{% block theme_toggle %}{% endblock %}
```

- **Create your own theme:**  
  Use [daisyUI’s Theme Generator](https://daisyui.com/theme-generator/), add the CSS to your stylesheet, and include it in your template:

```html
{% block extra_head %}
<link rel="stylesheet" href="{% static 'your_app/css/output.css' %}" />
{% endblock %}
```

---

### Available blocks to extend

These template blocks let you tailor layouts, branding, and theming without rewriting core templates. Override only what you need.

- **theme:** Primary theme name like `light`.
- **head:** HTML head.
- **head_title:** Content for the `<title>` tag.
- **extra_head:** Extra content for `<head>`.
- **drawer_content:** Drawer content.
- **navbar_start:** Content in start of navbar.
- **branding:** Branding in navbar.
- **navbar_start:** Content in start of navbar.
- **navbar_center:** Content in center of navbar.
- **navbar_end:** Content in end of navbar.
- **theme_selector:** Theme select dropdown.
- **theme_toggle:** Theme toggle button.
- **toggle_theme:** Secondary theme name `dark`.
- **breadcrumbs:** Breadcrumb navigation.
- **content:** Sidebar content (main content).
- **sidebar_start:** Content in start of sidebar.
- **sidebar_end:** Content in end of sidebar.
- **drawer_header_start:** Content in start of drawer header.
- **drawer_branding:** Branding in drawer header.
- **drawer_header_end:** Content in end of drawer header.
- **drawer_start:** Content in start of drawer.
- **drawer_center:** Content in center of drawer.
- **drawer_end:** Content in end of drawer.
- **extra_body:** Extra body tags like script.

## Contributing

Contributions are welcome! Please see the [CONTRIBUTING](CONTRIBUTING.md) guide for details. Feedback, issues, and pull requests help shape the project.

---

## Support

For questions or support, open an issue or join the conversation in [GitHub Discussions](https://github.com/youzarsiph/django-allauth-xui/discussions).

---

## License

Licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

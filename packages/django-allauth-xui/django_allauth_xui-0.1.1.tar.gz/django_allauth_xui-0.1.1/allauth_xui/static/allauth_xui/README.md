# UI Styles

Basic commands to get started.

First `cd` into dir:

```console
cd allauth_xui/static/allauth_xui
```

To generate the styles:

```console
npm install
cd allauth_xui/static/allauth_xui
npx @tailwindcss/cli -i ../static/allauth_xui/css/app.css -o ../static/allauth_xui/css/styles.css --cwd ../../templates -m -w
```

To format the templates:

```console
npx prettier -w ../../templates
```

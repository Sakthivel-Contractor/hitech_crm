### Hitech Open Borewell Contractors

Borewell contractores

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench install-app hitech
```

### Public Vue website

The public website is built from the sibling `hi_tech_open_well_contractor` repository and packaged
into this app's `hitech/public/vue` and `hitech/www` directories. Build it before deploying an app
change so Frappe Cloud receives the generated website files with the app commit:

```bash
cd apps/hi_tech_open_well_contractor
npm ci
npm run build:frappe -- ../hitech_crm/hitech
cd ../hitech_crm
git add hitech README.md
git commit -m "Serve public Vue site from Frappe"
git push upstream main
```

The package command expects the Vue and Frappe repositories to be siblings; pass the path to this
app's `hitech` directory if they are elsewhere. The Frappe homepage serves the Vue site, `/crm`
serves Frappe CRM, and unmatched public paths fall back to the Vue app. Website lead submissions
use the same-origin Frappe API and session CSRF token.

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/hitech
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit

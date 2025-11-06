# Corporation Handouts

AA module for managing corporation handouts and especially to keep track of their fits/ammo to know if they should be fixed.

[![release](https://img.shields.io/pypi/v/aa-corphandouts?label=release)](https://pypi.org/project/aa-corphandouts/)
[![python](https://img.shields.io/pypi/pyversions/aa-corphandouts)](https://pypi.org/project/aa-corphandouts/)
[![django](https://img.shields.io/pypi/djversions/aa-corphandouts?label=django)](https://pypi.org/project/aa-corphandouts/)
[![license](https://img.shields.io/badge/license-MIT-green)](https://gitlab.com/r0kym/aa-corphandouts/-/blob/master/LICENSE)

## Features:

### Screenshots

![index view](./images/index.png)

![doctrine view](./images/doctrine.png)

![corrections view](./images/corrections.png)

## Installation

### Step 1 - Check prerequisites

1. Corporation handouts is a plugin for Alliance Auth. If you don't have Alliance Auth running already, please install it first before proceeding. (see the official [AA installation guide](https://allianceauth.readthedocs.io/en/latest/installation/auth/allianceauth/) for details)
2. The app requires you to have two other applications installed to work properly:
   1. [fittings](https://gitlab.com/colcrunch/fittings)
   2. [allianceauth-corp-tools](https://github.com/Solar-Helix-Independent-Transport/allianceauth-corp-tools/tree/master)

Make sure to have both properly installed before continuing

### Step 2 - Install app

Make sure you are in the virtual environment (venv) of your Alliance Auth installation. Then install the newest release from PyPI:

```bash
pip install aa-corphandouts
```

### Step 3 - Configure Auth settings

Configure your Auth settings (`local.py`) as follows:

- Add `'corphandouts'` to `INSTALLED_APPS`
- Add below lines to your settings file:

```python
CELERYBEAT_SCHEDULE['corphandouts_update_all'] = {
    'task': 'corphandouts.tasks.update_all_doctrine_reports',
    'schedule': crontab(minute='0', hour='*/1'),
}
```

### Step 4 - Finalize App installation

Run migrations & copy static files

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

Restart your supervisor services for Auth.

## Admin setup

To set up which doctrines should be verified by this module, you need to create new doctrine reports in the admin panel.
`YOURAUTH/admin/corphandouts/doctrinereport`

All fits you want to check need to already be added in the fitting module to be selected.

When creating a new doctrine, you need to determine:
- the doctrine name
- the corporation that has the ships in hangars
- the location of the doctrine
- which corp hangar division (a number between one and seven)

After that you can add all the ships that are part of this doctrine.
You can optionally specify:
- how many ships of this type are expected in corp hangars
- a regex to match ship names

Once the doctrine is saved you can select the doctrine and use an admin action to update it immediately.

### Ship name regex

When your doctrine has several ships of the same types but with different fits, or you have more ships of this type in your hangar than the ones of the doctrine, you should consider using a regex to match ship names.

For example, a loki fleet could use both dps loki and logi loki.
The DPS loki would be name `LOKI DPS` and the logi ones `LOKI LOGI`, entering these values in the regex will only select the ships with this name. \
In case you name your ships with number - for example `LOKI DPS 0` up to `LOKI DPS 9` - you can use a regex to match those `LOKI DPS \d`.

## Permissions

Permissions overview.

| Name         | Description                             |
|--------------|-----------------------------------------|
| basic_access | Can access the module and see doctrines |



## Commands

The following commands can be used when running the module:

| Name                   | Description                              |
|------------------------|------------------------------------------|
| corphandouts_check_all | Updates all doctrine reports in the auth |

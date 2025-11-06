[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CircleCI](https://circleci.com/gh/cknoll/webtogit/tree/main.svg?style=shield)](https://circleci.com/gh/cknoll/webtogit/tree/main)

# WebToGit

WebToGit is a simple command line tool to facilitate decentral archiving of (volatile) web pages in a local git repo. Initial usecase is to archive web based pads (colaboratively edited texts) such as etherpad or hedgedoc.

## How it Works

WebToGit comes with some builtin bootstrapping capabilities. It automatically creates a git repo with the following structure:

```
$HOME
├── <datapath>/webtogit
│   ├── archived-webdocs
│   │   ├── .git/
│   │   ├── webtogit-sources.yml
│   │   ├── README.md
│   │   └── content
│   │       ├── pad1.txt
│   │       ├── page2.html
│   │       └── …
…   …
```

The file `webtogit-sources.yml` contains the URLs which should be saved to the repo (inside `content`), see details below. For WebToGit to be useful `webtogit-sources.yml` must be edited. This file also serves as a marker: if it is present the `webtogit` command is allowed to modify or delete the repo. The file `README.md` contains some generic information to explain the purpose of this repository.


### `webtogit-sources.yml` Example

The file uses [YAML syntax](https://en.wikipedia.org/wiki/YAML#Syntax).

```yaml
# This is a comment and will be ignored. Same for empty lines.

# The top YAML-element is a list.
# Its entries are strings or dictionaries (associative arrays).
# The following two list entries are just simple literal strings
# (one url per line):

- https://pad.url1.org/p/some-pad
- https://pad.url1.org/p/some-other-pad

# The next url needs some additional information.
# It is thus stored as yaml-dictionary.

- "https://pad.url1.org/p/some-third-pad":
    name: explicit_filename.txt
    key2: value2

- https://pad.url2.org/p/yet-another-pad


# save a hedgedoc document including images
- "https://hedgedoc.url3.org/Xa4yGMk9Tm62CGi_F6uCxQ/download":
    name: my_slides.md
    download_images: true
```


The program is expected to be executed regularly (e.g. once a day). It parses `sources.yml` and downloads the content into the working dir of the repo and adds the file to the index. Then if there are changes, it makes a commit to the repo.


## Installation

- Ensure *git* is installed and in your path
- Installation for normal usage: `pip install webtogit`
- Installation for development:
    - Clone the repo
    - Run `pip install -e .` inside the project root.

## Uninstallation

- Find out all paths (configuration and repos):  `webtogit --print-config`
- Manually delete unneeded data.
- `pip uninstall webtogit`

## Usage

### Directories

Two directories are relevant: one to store the configuration (`settings.yml`), another to store data (i.e. repositories). They are set by using the [appdirs](https://pypi.org/project/appdirs/) package.

The appdirs-settings can be overridden by environment variables (`WEBTOGIT_CONFIGDIR_PATH"` and `WEBTOGIT_DATADIR_PATH`) and, alternatively, by commandline options.

### Basic Commands

- Get help: `webtogit --help`
- Get help: `webtogit --print-config`
- Perform general bootstrapping: `webtogit --bootstrap` (needs to be called once after installation)
- Download all sources of default repo and commit changes: `webtogit` **(← this is the regular call)**
- Bootstrap a new repository: `webtogit --bootstrap-repo <reponame>`
- Download all sources of non-default repo and commit changes: `webtogit <reponame>`
- Download all sources of all repos and commit changes: `webtogit --update-all-repos`

### Automating WebToGit

Being a command line tool WebToGit can be easily automated with cron (at least on UNIX-based systems).

- Find out the path to your python interpreter (e.g. `/usr/bin/python3` or some virtual environment)
- Open the crontab inside your default editor: `crontab -e`
- Add the following line and adapt it to your needs: `15 18 * * * /path/to/python -m webtogit.cli`. Cron is triggered after editor is closed.
    - This installs a cronjob which is executed every day at 18:15h (i.e. 6:15 pm).

## Troubleshouting

The software is provided "as is" without any warranties. Installation and intended usecases are tested via continuous integration, see [![CircleCI](https://circleci.com/gh/cknoll/webtogit/tree/main.svg?style=shield)](https://circleci.com/gh/cknoll/webtogit/tree/main). If you experience any trouble you should always be able to run the software inside a docker container like specified in [`.circleci/config.yml`](.circleci/config.yml) or similar conditions. In principle, most modern UNIX-environments should be supported.

Feel free to open issues.


## Development Notes

For local development it is recommended to install this package in [editable mode](https://pip.pypa.io/en/latest/cli/pip_wheel/?highlight=editable#cmdoption-e): `pip install -e .` (run from where `setup.py` lives). Run `python -m unititest` in the project root to execute the tests.

### Feature ideas

- [ ] support a `run-on-change: <arbitrary-command>` key-value-pair
- [ ] setup cron via `webtogit --setup-cron`



## Contributing

Contributions are very welcome. Please file a merge/pull request or reach out otherwise. Contact information can be found in `setup.py`.

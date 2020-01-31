**snooge has been made obsolete by the combination of [rchive](https://github.com/codsane/rchive) and something like [ArchiveBox](https://github.com/pirate/ArchiveBox)**


# ![alt text](http://i.imgur.com/7U0Oqwf.png "Credits: /u/lemonzoidberg") snooge

~~snooge is a Python script that allows you to download all of your saved NSFW posts from reddit and save them locally. snooge supports a variety of websites with help from [youtube-dl](https://rg3.github.io/youtube-dl/).~~

## Requirements

- Python 3
- [configparser](https://docs.python.org/3/library/configparser.html)
- [praw](https://praw.readthedocs.io/en/latest/)
- [youtube-dl](https://rg3.github.io/youtube-dl/)
- [py-gfycat](https://github.com/ankeshanand/py-gfycat)

## Usage

### Configuration File
1. [Create a reddit application (script)](https://www.reddit.com/prefs/apps/) to generate your client ID and client secret.
2. Create a text file with the following format:

	[configuration]

	client_id = Your Client ID

	client_secret = Your Client Secret

	password = Your Reddit Password

	username = Your Reddit Username
3. Save config.txt in the same directory as snooge.py

### Running

Running snooge is as simple as:

	$ python3 snooge.py

By default, a new folder with your reddit username will be created inside the same directory as snooge.py. All files downloaded will be saved there.

If you would like to change this directory, you may run snooge.py followed by the location you would like your files to be saved:

	$ python3 snooge.py /Users/codsane/documents/taxes2017

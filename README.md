# Flashscore.com Team Transfers

Desc: Opens player pages from flashscore.com team transfers URL based on the
      team URL and transfer dates provided from user input.

## Installation

The install script requires python 3 and pip to be installed on your system.
The flashscore_open_transfer.py script requires the requests and selenium
python packages necessary to run, and the install script will help install
those packages and create a shortcut of the .py on your desktop.

For Windows:

1. Extract the zip file to a directory where you want to install the script

2. Run the `install.bat` script or simply run the following command in the
   terminal:

```bash
pip install -r requirements.txt
```

## Usage

Click on the shortcut created on your desktop to run the script and run from
there, or run it yourself in the terminal using the following command:

```bash
python flashscore_open_transfer.py
```

A prompt will appear asking for the team URL and transfer dates. The team URL
can be found by going to the team's page on flashscore.com and clicking on the
"Transfers" tab. By default, the dates are set to the 1st of each month. Change
the DEFAULT_PARAMS variable in the script to allow requests for specific days
for the transfers date. For example:

```python
DEFAULT_PARAMS = {
    'ASK_FOR_DAY': True,
}
```

The script will download a chrome driver executable if it does not already
exist in the same directory as the script, but will reuse and update it if it already exists. This is necessary for the selenium package to work.

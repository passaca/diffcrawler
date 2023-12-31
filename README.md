# DiffCrawler
Cross-platform GUI tool to monitor the content (displayed text) of websites. If the content changes, the website is marked "unread", informing the user of the change.

![Screenshot of the DiffCrawler application on Mac (dark theme)](screenshot_mac.png)

Useful to track updates on sites that don't provide RSS feeds.

Please be aware that the software is still in a very early alpha stage.

## Installation
### Linux and Mac
Make sure git, python (>= 3.10), pip and tkinter are installed on your system. This depends on the package management system of you operating system. On Debian-based distros this could look like this:
```
sudo apt-get install git python3-pip python3-venv python3-tk
```

And on Mac with Homebrew installed:
```
brew install git python python-tk
```

 Change to the path where you want to create the `diffcrawler` directory. Then clone the repository:
```
git clone https://github.com/passaca/diffcrawler
```

Change to the `diffcrawler` directory, create a virtual environment and activate it:
```
cd diffcrawler
python3 -m venv venv
source venv/bin/activate
```

Install the required packages:
```
pip install -r requirements.txt
```

Run the application:
```
python3 -m diffcrawler
```

### Windows
The application is untested on Windows (as I have no system available) but there is no reason it should not run. If anybody wants to test it and provide instructions, feel free.


## Usage

### Adding Websites to Monitor
Websites you wish to monitor can be added to the list via the `Add` button. The properties of each list item can be set in the right pane:

| Property | Meaning |
| ---------|---------|
| URL | URL of the website (must be valid http or https address!)
| Timeout | Timeout in seconds (total allowed time for server response)
| Diff Threshold | Minimum number of content changes to consider website changed/unread
| Favorite | Mark URL as favorite (use-case not implemented yet)
| Date Added | Date at which the website was added to list

### Fetching Website Contents

To fetch/update the content, select the website(s) from the list (hold `Shift`/`Ctrl`/`Command` for multiple selection) and click the `Fetch` button. The selected websites are fetched concurrently (up to 5 simultaneous connections). A successful fetch is shown as a check mark (✔) and an error (most commonly a timeout or DNS error due to a wrong URL) is symbolized as a ballot character (✘).

Date and time of the successful fetches are shown. Once there is a second fetch for a website, the difference (diff) of the two versions is calculated and shown. If it is larger than the "Diff Threshold", the website is considered "changed" and marked unread (bold font). The selected sites can be opened in a browser with the `Open URL` button (and will be marked read when you do so).

The actual diff can be inspected from the `View` menu (`Show Diff`).

A fetch can be undone in case the current version of the website is showing content unrelated to the monitored version (e.g. a "maintentance" message or server error page). For this, select `Undo Fetch` from the `Edit` menu.

## Features
- Cross platform (Mac, Linux, Windows)
- Set individual timeouts and diff thresholds for each website
- Fetch websites with up to 5 simultaneous connections (fetching does not block the UI)
- Save and load to/from file (efficient SQLite-based file format)
- Inspect diffs
- Undo fetch

## Work in progress
- [ ] Search/filter list
- [ ] Reorder list
- [ ] Improve diff implementation (e.g. allow monitoring certain DOM elements)
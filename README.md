# DiffCrawler
Cross-platform GUI tool to monitor the content (displayed text) of websites. If the content changes, the website is marked "unread", informing the user of the change.

Useful to track updates on sites that don't provide RSS feeds.

Please be aware that the software is still in a very early alpha stage.

## Usage

### Adding Websites to Monitor
Websites you wish to monitor can be added to the list via the `Add` button. The properties of each list item can be set in the right pane:

| Property | Meaning |
| ---------|---------|
| URL | URL of the website (must be valid http or https address!)
| Timeout | Timeout in seconds (total allowed time for server response)
| Diff Threshold | Minimum number of content changes to consider website changed/unread
| Favorite | Mark URL as favorite (use-case not implemented yet)
| Added date | Date at which the website was added to list

### Fetching Website Contents

To fetch/update the content, select the website(s) from the list (hold `Shift`/`Ctrl`/`Command` for multiple selection) and click the `Fetch` button. The selected websites are fetched concurrently (up to 5 simultaneous connections). A successful fetch is shown as a check mark (✔) and an error (most commonly a timeout or DNS error due to a wrong URL) is symbolized as a ballot character (✘).

Date and time of the successful fetches are shown. Once there is a second retrieval for a website, the difference (diff) of the two versions is calculated and shown. If it is larger than the "Diff Threshold", the website is considered "changed" and marked unread (bold font). The selected sites can be opened in a browser with the `Open URL` button (and will be marked read when you do so).

The actual diff can be inspected from the `View` menu (`Show Diff`).

A fetch can be undone in case the current version of the website is showing content unrelated to the monitored version (e.g. a "maintentance" message or server error page). Select `Undo Fetch` from the `Edit` menu.

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
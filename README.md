# FINDIT - Find what matters.

A desktop lost-and-found system built with Python, PyQt6 and SQLite.

## Features
- Report lost and found items, with category (choose Other to type what the item is), location, date, description, separate contact name and phone/email, and optional photo
- Report pages show tips plus a live list of the other side's latest reports (a lost item may already have been handed in); click one to open it
- Browse all reports, filter by Lost / Found / Claimed, and view photo and details
- Search-engine style page with type and category filters
- Claim form: record who claimed an item, the proof shown (with the ID number when an ID is shown), who released it and when (reopening keeps the history)
- Activity log: every report, edit, claim, reopen and delete is recorded; filter by action, type, date range or text
- Edit a report to fix mistakes or replace its photo, and delete reports
- Match suggestions: lost and found reports are compared by category, name, description, place and date, and likely matches are shown after saving a report or from View items
- Dashboard counters for lost, found and claimed items

## Run
```
pip install -r requirements.txt
python main.py
```

## Design
Colors and fonts live in the `Theme` class in `dashboard/theme.py`. The logo, illustrations and icons are PNG files in
`asset/art/`. Icons are saved in one color and `graphics.load()` repaints them, so the colors still come from `Theme`.

## Project structure
```
main.py                   starts the app
database/database.py      all SQLite code (items, claims, categories); no other file touches the database
dashboard/dashboard.py    main window: sidebar, pages, counters
dashboard/theme.py        the Theme class (colors, fonts), the stylesheet and small UI helpers
dashboard/graphics.py     loads the PNG pictures from asset/art
asset/art/                the logo, illustrations and icons (PNG files)
asset/image/              photos uploaded with reports
features/lost_items.py    Report lost form (the base class for both report forms)
features/found_items.py   Report found form (reuses the lost form)
features/browse_items.py  View items table and its buttons
features/search_items.py  Search items page
features/activity_log.py  Activity log page with filters
features/claim_item.py    claim form      features/change_status.py   claim or reopen
features/edit_item.py     edit form       features/delete_items.py    delete
features/match_dialog.py   the matches window
features/side_panel.py    tips and recent reports beside the report forms
features/upload_items.py  photo upload
logic/validation.py       input rules (no Qt), raises ValidationError
logic/matching.py         match suggestions (no Qt)
logic/labels.py           text for categories and contacts (no Qt)
logic/timeago.py          '3 days ago' dates (no Qt)
```

## Author
Luiella Jane C. Mentes, Computer Science student  
luiellamentes@gmail.com

# Interactive CLI

This project demonstrates a simple interactive command line interface built with [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit).

## Setup

Install the dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Usage

Run the CLI with Python:

```bash
python cli.py
```

You will be greeted with an interactive prompt. Type `help` to see available commands and `exit` to quit.

The CLI now supports simple management of **categories** and **content** items. Each category may have a `parent` category. Content has `content_type`, `category` and `action` fields. Use the following commands to manage them:

```
add_category <name> [parent]
list_categories
get_category <name>
update_category <name> <parent>
delete_category <name>

add_content <name> <content_type> <category> <action>
list_contents
get_content <name>
update_content <name> <field> <value>
delete_content <name>
```

These commands operate on in-memory data only and are intended for experimentation.

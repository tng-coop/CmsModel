# Interactive GUI

This project demonstrates a simple interface built with
[PyQt](https://riverbankcomputing.com/software/pyqt/) for the graphical
tree view. The command line functionality still uses
[prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit).

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
The application opens a PyQt window showing the category tree. Closing the
window returns you to the interactive prompt. Type `help` to see available
commands and `exit` to quit.

You can also launch the GUI directly without entering the CLI:

```bash
python gui.py
```

The CLI now supports simple management of **categories** and **articles**. Each category has an optional `parent` and a `sort_order_index`. Articles store a list of categories and an `archived` flag. Use the following commands to manage them:

```
add_category <name> [parent]
list_categories
get_category <name>
update_category <name> <parent>
delete_category <name>

add_content <name> <categories> [archived]
list_contents
get_content <name>
update_content <name> <field> <value>
delete_content <name>
seed_data
clear_all
tree_view
tree_edit [name] [parent]
tree_ui
```

These commands operate on in-memory data only and are intended for experimentation.
On startup the CLI is pre-populated with sample categories and articles. Top
level items such as `Home` and `About` appear directly in the menu. The
`seed_data` command can be used to reload this data at any time. `clear_all`
removes all categories and articles. `tree_view` prints the categories in a
hierarchical tree and `tree_edit` lets you change the parent of a category.
The `tree_ui` command opens the same PyQt window for editing categories and
articles. Right-click a category to rename or delete it and double click an
article item to edit its fields.
When run with no arguments, it opens a mouse-friendly chooser for the
category and then the parent. If a name is provided but no parent, only the
parent selection dialog is shown. The command validates that the selected
parent exists and is not the category itself. Tab completion is available
for commands and relevant arguments such as category names and article names.

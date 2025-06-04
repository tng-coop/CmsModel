"""Command line interface for the CMS demo."""

from typing import Dict, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import radiolist_dialog

from .completer import CmsCompleter
from .data import print_category_tree, seed_data
from .models import Category, Content


COMMANDS = [
    'help', 'exit', 'greet',
    'add_category', 'list_categories', 'get_category',
    'update_category', 'delete_category',
    'add_content', 'list_contents', 'get_content',
    'update_content', 'delete_content',
    'seed_data', 'clear_all', 'tree_view', 'tree_edit', 'tree_ui'
]


def _choose_category(categories: Dict[str, Category]) -> Optional[str]:
    """Interactive dialog to select a category."""
    result = radiolist_dialog(
        title='Edit Category',
        text='Select category to edit:',
        values=[(n, n) for n in sorted(categories.keys())],
    ).run()
    return result


def _choose_parent(categories: Dict[str, Category], current: str) -> Optional[str]:
    """Interactive dialog to choose a new parent."""
    options = [('none', 'None')] + [
        (n, n) for n in sorted(categories.keys()) if n != current
    ]
    result = radiolist_dialog(
        title='Edit Category',
        text=f'Select new parent for "{current}":',
        values=options,
    ).run()
    if result is None:
        return None
    return None if result == 'none' else result


def handle_tree_edit(tokens: list[str], categories: Dict[str, Category]) -> None:
    """Handle the tree_edit command with optional arguments."""
    if len(tokens) not in {1, 2, 3}:
        print('Usage: tree_edit [name] [parent]')
        return

    if not categories:
        print('No categories.')
        return

    if len(tokens) == 1:
        name = _choose_category(categories)
        if name is None:
            print('Edit cancelled.')
            return
    else:
        name = tokens[1]
        if name not in categories:
            print('Category not found.')
            return

    if len(tokens) == 3:
        parent = tokens[2]
        if parent.lower() == 'none':
            parent = None
        elif parent not in categories:
            print('Parent category does not exist.')
            return
        elif parent == name:
            print('A category cannot be its own parent.')
            return
    else:
        parent = _choose_parent(categories, name)
        if parent is None:
            print('Edit cancelled.')
            return

    categories[name].parent = parent
    print('Category updated.')


def run_cli() -> None:
    """Start the interactive command loop."""
    session = PromptSession()
    categories: Dict[str, Category] = {}
    contents: Dict[str, Content] = {}
    seed_data(categories, contents)
    from .tree_gui import TreeGui
    TreeGui(categories, contents).run()
    completer = CmsCompleter(COMMANDS, categories, contents)
    print('Interactive CLI. Sample data loaded. Type "help" for commands.')

    while True:
        try:
            text = session.prompt('> ', completer=completer)
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

        tokens = text.strip().split()
        if not tokens:
            continue
        cmd = tokens[0].lower()

        if cmd == 'exit':
            break
        elif cmd == 'help':
            print('Available commands: ' + ', '.join(COMMANDS))
        elif cmd == 'greet':
            print('Hello!')
        elif cmd == 'add_category':
            if len(tokens) < 2:
                print('Usage: add_category <name> [parent]')
                continue
            name = tokens[1]
            parent = tokens[2] if len(tokens) > 2 else None
            categories[name] = Category(name=name, parent=parent)
            print(f'Category "{name}" added.')
        elif cmd == 'list_categories':
            if categories:
                for cat in categories.values():
                    print(f'{cat.name} (parent: {cat.parent})')
            else:
                print('No categories.')
        elif cmd == 'get_category':
            if len(tokens) != 2:
                print('Usage: get_category <name>')
                continue
            cat = categories.get(tokens[1])
            if cat:
                print(f'{cat.name} (parent: {cat.parent})')
            else:
                print('Category not found.')
        elif cmd == 'update_category':
            if len(tokens) != 3:
                print('Usage: update_category <name> <parent>')
                continue
            name, parent = tokens[1], tokens[2]
            cat = categories.get(name)
            if cat:
                cat.parent = parent
                print('Category updated.')
            else:
                print('Category not found.')
        elif cmd == 'delete_category':
            if len(tokens) != 2:
                print('Usage: delete_category <name>')
                continue
            if categories.pop(tokens[1], None):
                print('Category deleted.')
            else:
                print('Category not found.')
        elif cmd == 'add_content':
            if len(tokens) != 5:
                print('Usage: add_content <name> <content_type> <category> <action>')
                continue
            name, ctype, cat, action = tokens[1:5]
            if cat not in categories:
                print('Category does not exist.')
                continue
            contents[name] = Content(name=name, content_type=ctype, category=cat, action=action)
            print(f'Content "{name}" added.')
        elif cmd == 'list_contents':
            if contents:
                for c in contents.values():
                    print(f'{c.name}: type={c.content_type} category={c.category} action={c.action}')
            else:
                print('No contents.')
        elif cmd == 'get_content':
            if len(tokens) != 2:
                print('Usage: get_content <name>')
                continue
            c = contents.get(tokens[1])
            if c:
                print(f'{c.name}: type={c.content_type} category={c.category} action={c.action}')
            else:
                print('Content not found.')
        elif cmd == 'update_content':
            if len(tokens) != 4:
                print('Usage: update_content <name> <field> <value>')
                continue
            name, field_name, value = tokens[1:4]
            c = contents.get(name)
            if not c:
                print('Content not found.')
                continue
            if field_name == 'content_type':
                c.content_type = value
            elif field_name == 'category':
                if value not in categories:
                    print('Category does not exist.')
                    continue
                c.category = value
            elif field_name == 'action':
                c.action = value
            else:
                print('Unknown field.')
                continue
            print('Content updated.')
        elif cmd == 'delete_content':
            if len(tokens) != 2:
                print('Usage: delete_content <name>')
                continue
            if contents.pop(tokens[1], None):
                print('Content deleted.')
            else:
                print('Content not found.')
        elif cmd == 'clear_all':
            categories.clear()
            contents.clear()
            print('All data cleared.')
        elif cmd == 'tree_view':
            if categories:
                print_category_tree(categories)
            else:
                print('No categories.')
        elif cmd == 'tree_edit':
            handle_tree_edit(tokens, categories)
        elif cmd == 'tree_ui':
            if categories:
                from .tree_gui import TreeGui
                TreeGui(categories, contents).run()
            else:
                print('No categories.')
        elif cmd == 'seed_data':
            seed_data(categories, contents)
            print('Sample data loaded.')
        else:
            print(f'Unknown command: {cmd}')

    print('Goodbye!')


if __name__ == '__main__':
    run_cli()

from dataclasses import dataclass
from typing import Dict, Optional, List

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion


@dataclass
class Category:
    name: str
    parent: Optional[str] = None


@dataclass
class Content:
    name: str
    content_type: str
    category: str
    action: str


def seed_data(categories: Dict[str, 'Category'], contents: Dict[str, 'Content']) -> None:
    """Populate dictionaries with sample catholic church data."""
    categories.clear()
    contents.clear()

    seed_categories = {
        'Home': Category('Home'),
        'About': Category('About'),
        'Mass Times': Category('Mass Times'),
        'Sacraments': Category('Sacraments'),
        'Ministries': Category('Ministries'),
        'Downloads': Category('Downloads'),
        'Staff': Category('Staff', parent='About'),
        'History': Category('History', parent='About'),
        'Contact': Category('Contact', parent='About'),
        'Baptism': Category('Baptism', parent='Sacraments'),
        'Confirmation': Category('Confirmation', parent='Sacraments'),
        'Marriage': Category('Marriage', parent='Sacraments'),
        'Youth Ministry': Category('Youth Ministry', parent='Ministries'),
        'Choir': Category('Choir', parent='Ministries'),
        'High School': Category('High School', parent='Youth Ministry'),
    }
    categories.update(seed_categories)

    seed_contents = {
        'office_hours': Content('office_hours', 'office_info', 'Home', 'update'),
        'welcome': Content('welcome', 'tinymce', 'Home', 'new'),
        'bulletin': Content('bulletin', 'pdf', 'Downloads', 'update'),
        'youth_banner': Content('youth_banner', 'banner', 'Youth Ministry', 'new'),
        'old_news': Content('old_news', 'tinymce', 'Home', 'delete'),
    }
    contents.update(seed_contents)


def print_category_tree(categories: Dict[str, Category]) -> None:
    """Display categories in a hierarchical tree."""
    children: Dict[Optional[str], List[str]] = {}
    for cat in categories.values():
        children.setdefault(cat.parent, []).append(cat.name)

    def _print(node: Optional[str], indent: int = 0) -> None:
        for child in sorted(children.get(node, [])):
            print('  ' * indent + child)
            _print(child, indent + 1)

    _print(None)


class CmsCompleter(Completer):
    """Context aware tab completion for the CLI."""

    def __init__(self, commands, categories, contents):
        self.commands = commands
        self.categories = categories
        self.contents = contents

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.lstrip()
        tokens = text.split()
        word = document.get_word_before_cursor()

        def yield_words(options):
            for opt in options:
                if opt.lower().startswith(word.lower()):
                    yield Completion(opt, start_position=-len(word))

        if len(tokens) <= 1:
            yield from yield_words(self.commands)
            return

        cmd = tokens[0]
        arg_index = len(tokens) - 1
        if text.endswith(' '):
            arg_index += 1
            word = ''

        if cmd in {'get_category', 'delete_category', 'update_category'}:
            if arg_index == 1:
                yield from yield_words(self.categories.keys())
            elif arg_index == 2 and cmd == 'update_category':
                yield from yield_words(self.categories.keys())
        elif cmd == 'add_category':
            if arg_index == 2:
                yield from yield_words(self.categories.keys())
        elif cmd in {'get_content', 'delete_content'}:
            if arg_index == 1:
                yield from yield_words(self.contents.keys())
        elif cmd == 'update_content':
            if arg_index == 1:
                yield from yield_words(self.contents.keys())
            elif arg_index == 2:
                yield from yield_words(['content_type', 'category', 'action'])
            elif arg_index == 3:
                field = tokens[2]
                if field == 'content_type':
                    yield from yield_words(['office_info', 'tinymce', 'pdf', 'banner'])
                elif field == 'category':
                    yield from yield_words(self.categories.keys())
                elif field == 'action':
                    yield from yield_words(['delete', 'update', 'new'])
        elif cmd == 'add_content':
            if arg_index == 2:
                yield from yield_words(['office_info', 'tinymce', 'pdf', 'banner'])
            elif arg_index == 3:
                yield from yield_words(self.categories.keys())
            elif arg_index == 4:
                yield from yield_words(['delete', 'update', 'new'])
        elif cmd == 'tree_edit':
            if arg_index == 1:
                yield from yield_words(self.categories.keys())
            elif arg_index == 2:
                yield from yield_words(self.categories.keys())
        else:
            yield from yield_words(self.commands)


def main():
    session = PromptSession()
    commands = [
        'help', 'exit', 'greet',
        'add_category', 'list_categories', 'get_category',
        'update_category', 'delete_category',
        'add_content', 'list_contents', 'get_content',
        'update_content', 'delete_content',
        'seed_data', 'clear_all', 'tree_view', 'tree_edit'
    ]
    categories: Dict[str, Category] = {}
    contents: Dict[str, Content] = {}
    seed_data(categories, contents)
    completer = CmsCompleter(commands, categories, contents)
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
            print('Available commands: ' + ', '.join(commands))
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
            if len(tokens) != 3:
                print('Usage: tree_edit <name> <parent>')
                continue
            name, parent = tokens[1], tokens[2]
            cat = categories.get(name)
            if cat:
                cat.parent = None if parent.lower() == 'none' else parent
                print('Category updated.')
            else:
                print('Category not found.')

        elif cmd == 'seed_data':
            seed_data(categories, contents)
            print('Sample data loaded.')

        else:
            print(f'Unknown command: {cmd}')
    print('Goodbye!')


if __name__ == '__main__':
    main()

from dataclasses import dataclass, field
from typing import Dict, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter


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


def main():
    session = PromptSession()
    commands = [
        'help', 'exit', 'greet',
        'add_category', 'list_categories', 'get_category',
        'update_category', 'delete_category',
        'add_content', 'list_contents', 'get_content',
        'update_content', 'delete_content',
    ]
    completer = WordCompleter(commands, ignore_case=True)
    categories: Dict[str, Category] = {}
    contents: Dict[str, Content] = {}
    print('Interactive CLI. Type "help" for commands.')
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

        else:
            print(f'Unknown command: {cmd}')
    print('Goodbye!')


if __name__ == '__main__':
    main()

"""Prompt toolkit completer for the CMS CLI."""

from typing import Dict, Iterable

from prompt_toolkit.completion import Completer, Completion

from models import Category, Article


class CmsCompleter(Completer):
    """Context aware tab completion for the CLI."""

    def __init__(self, commands: Iterable[str], categories: Dict[str, Category], contents: Dict[str, Article]):
        self.commands = list(commands)
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
                yield from yield_words(['categories', 'archived'])
            elif arg_index == 3:
                field = tokens[2]
                if field == 'categories':
                    yield from yield_words(self.categories.keys())
                elif field == 'archived':
                    yield from yield_words(['true', 'false'])
        elif cmd == 'add_content':
            if arg_index == 2:
                yield from yield_words(self.categories.keys())
            elif arg_index == 3:
                yield from yield_words(['true', 'false'])
        elif cmd == 'tree_edit':
            if arg_index == 1:
                yield from yield_words(self.categories.keys())
            elif arg_index == 2:
                yield from yield_words(self.categories.keys())
        else:
            yield from yield_words(self.commands)

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter


def main():
    session = PromptSession()
    commands = ['help', 'exit', 'greet']
    completer = WordCompleter(commands, ignore_case=True)
    print('Interactive CLI. Type "help" for commands.')
    while True:
        try:
            text = session.prompt('> ', completer=completer)
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        cmd = text.strip().lower()
        if cmd == 'exit':
            break
        elif cmd == 'help':
            print('Available commands: ' + ', '.join(commands))
        elif cmd == 'greet':
            print('Hello!')
        elif cmd:
            print(f'Unknown command: {cmd}')
    print('Goodbye!')


if __name__ == '__main__':
    main()

from __future__ import annotations

from blessed import Terminal
from typing import List, Optional
term = Terminal()

__all__ = [
    'question', 'credentials',
    'select', 'checkbox'
]


def question(question_text: str, default: Optional[str] = ' ') -> str:

    question_text = '\33[92m[?]\33[0m ' + question_text + ': '
    value = ''
    req_flag = False
    def drw():
        template = '\33[2m' + default + '\33[0m'
        if req_flag:
            template = '\033[31m<required>\33[0m'
        print(
            '\r' + ' ' * (term.width) + \
            term.move_left(term.width) + \
            question_text + value + (
                template + \
                term.move_left(
                    10
                    if req_flag else
                    len(default)
                )
                if not value else ''
            ),
            end='', flush=True
        )
    drw()
    with term.cbreak():
        while True:
            if req_flag:
                drw()
                term.inkey(timeout=0.5)
                inp = ''
                req_flag = False
                drw()
            else:
                inp = term.inkey()
            if repr(inp) == 'KEY_ENTER':
                if value == '':
                    if default == ' ':
                        req_flag = True
                    else:
                        value = default
                        break
                else:
                    break
            elif repr(inp) == 'KEY_BACKSPACE':
                value = value[:-1]
                if value == '':
                    drw()
                else:
                    drw()
            elif len(repr(inp)) == 3:
                value += inp
                drw()
        drw()
        print()
        return value


def credentials(question_text: str) -> str:
    question_text = '\33[31m[*]\33[0m ' + question_text + ': '
    value = ''
    req_flag = False
    def drw():
        print(
            '\r' + ' ' * (term.width) + \
            term.move_left(term.width) + \
            question_text + '•' * len(value) + (
                '\033[31m<required>\33[0m' + term.move_left(10)
                if req_flag else ''
            ),
            end='', flush=True
        )
    drw()
    with term.cbreak():
        while True:
            if req_flag:
                drw()
                term.inkey(timeout=0.5)
                inp = ''
                req_flag = False
                drw()
            else:
                inp = term.inkey()
            if repr(inp) == 'KEY_ENTER':
                if value == '':
                    req_flag = True
                else:
                    break
            elif repr(inp) == 'KEY_BACKSPACE':
                value = value[:-1]
                if value == '':
                    drw()
                else:
                    drw()
            elif len(repr(inp)) == 3:
                value += inp
                drw()
        drw()
        print()
        return value


def select(question_text: str, options: List[str]) -> str:
    question_text = '\33[34m[~]\33[0m ' + question_text + ':'
    print(question_text)
    current = 0
    def drw():
        for index, option in enumerate(options):
            if index == current:
                print(' \033[36m>' + ' ' + option + '\33[0m')
            else:
                print(' ○' + ' ' + option)
        print(end=term.move_up(len(options)))
    drw()
    with term.cbreak(), term.hidden_cursor():
        while True:
            inp = term.inkey()
            if repr(inp) == 'KEY_DOWN':
                current = (current + 1) % len(options)
            elif repr(inp) == 'KEY_UP':
                current = (current - 1) % len(options)
            elif repr(inp) == 'KEY_ENTER':
                current = options[current]
                break
            drw()
    print(
        (' ' * term.width + '\n') * len(options) + \
        term.move_up(1 + len(options)) + \
        question_text + ' ' + current
    )
    return current


def checkbox(question_text: str, default: Optional[bool] = False) -> bool:
    value = default
    def drw():
        template = ('\033[92m✓\033[0m' if value else '\033[31mx\033[0m')
        print(f'\33[30m[\33[0m{template}\33[30m]\33[0m ' + question_text, end='\r')
    drw()
    with term.cbreak(), term.hidden_cursor():
        while True:
            inp = term.inkey()
            if repr(inp) == '\' \'':
                value = not value
            if repr(inp) == 'KEY_TAB':
                value = not value
            if repr(inp) == 'KEY_ENTER':
                break
            drw()
        drw()
        print()
        return value

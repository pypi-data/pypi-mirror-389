SAFE          = lambda r: f'{r}AAA583B9B0954BF58F3A9B6DA53F2DE9'
SWITCH        = 'SWITCH'
SWITCH_END    = 'END'
COMMENT_BEGIN = '/*'
COMMENT_END   = '*/'
OFF           = '//OFF:'
ENABLE        = lambda line: line if not line.startswith(OFF)                 else line[len(OFF):]
DISABLE       = lambda line: line if not line.strip() or line.startswith(OFF) else f'{OFF}{line}'

import re
import typing

class Feedback:

    def __init__(self):

        self.enabled :set[str] = set()
        self.disabled:set[str] = set()

def do_it(fn     :str,
          enable :typing.Callable[[str],bool],
          disable:typing.Callable[[str],bool]):
    
    with open(fn, 'r', encoding='utf-8') as f: 
        
        source = f.read()
    
    fb = Feedback()
    def repl(cases:str,
             block:str):

        if cases is None: raise AssertionError()
        cases:list[str] = cases.split(',')
        cases_enabled  = list(filter(enable,  cases))
        cases_disabled = list(filter(disable, cases))
        if   cases_enabled:
            
            fb.enabled.update(cases_enabled)
            return '\n'.join(map(ENABLE, block.split('\n')))

        elif cases_disabled:
            
            fb.disabled.update(cases_enabled)
            return '\n'.join(map(DISABLE, block.split('\n')))
        
        else: return block

    a = re.sub(pattern=''.join((
        
        f'(?s)',
        f'(?P<sw>'   +f'{re.escape(COMMENT_BEGIN)}\\s*{re.escape(SWITCH)}'   +f':(?P<cases>\\S+)'+f'\\s*{re.escape(COMMENT_END)})',
        f'(?P<swcontent>.*?)',
        f'(?P<swend>'+f'{re.escape(COMMENT_BEGIN)}\\s*{re.escape(SWITCH_END)}'                   +f'\\s*{re.escape(COMMENT_END)})',
        
    )), repl=lambda match: f'{match.group('sw')}{repl(match.group('cases'),match.group('swcontent'))}{match.group('swend')}', string=source)
    with open(fn, 'w', encoding='utf-8') as f:

        f.write(a)
    
    return fb

if __name__ == '__main__':

    import argparse

    p = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, 
                                description    =f'Switch code blocks ON or OFF in a Java source file\nDeactivated blocks are preceeded with a comment {repr(OFF)}.')
    p.add_argument('f',
                   help   ='file to process')
    p.add_argument('--on',
                   help   ='blocks to enable (switch ON)',
                   nargs  ='+',
                   default=[])
    p.add_argument('--off',
                   help   ='blocks to disable (switch OFF)',
                   nargs  ='+',
                   default=[])
    args = p.parse_args()
    print(args.on)
    print(args.off)
    do_it(fn     =args.f,
          enable =set(args.on) .__contains__,
          disable=set(args.off).__contains__)

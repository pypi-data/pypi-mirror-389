import re
import typing

if __name__ == '__main__': # business as usual
    import jl95terceira.pytools.pp as pp
else: # running in unittest or other
    from . import pp 

REGEX      = 'PPCMD'
SAFE_REGEX = f'{REGEX}98006097C52D49A0961609C7E687AF2B'
BEGIN:typing.Callable[[str],str] = lambda r: f'{r}:BEGIN'
END  :typing.Callable[[str],str] = lambda r: f'{r}:END'
TAIL :typing.Callable[[str],str] = lambda r: f'{r}:TAIL'

class Processor(pp.Processor):

    @typing.override
    def __init__(self):

        super().__init__(pis=[pp.ProcessingInstruction(abort_if=lambda fcontent,_a=abort_if_match_safe_rex: ((lambda m: m) if _a else (lambda m: not m))(re.match(pattern=f'.*{SAFE_REGEX}.*',string=fcontent)),
                                               pattern =f'( *:: *){BEGIN(rex)} *(.*?)\n( *:: *){END(rex)}.*?( *:: *){TAIL(rex)}',
                                               capture =lambda match                              : match.group(2),
                                               descape =lambda input                              : re.sub(pattern='\n *::',repl='\n',string=input),
                                               repl    =lambda output,match,rex=rex               : (f'{match.group(1)}{BEGIN(rex)}{match.group(2)}\n{match.group(3)}{END(rex)}\n{output}{match.group(3)}{TAIL(rex)}')) for abort_if_match_safe_rex,rex in [(True,  REGEX), 
                                                                                                                                                                                                                                                              (False, SAFE_REGEX)]])
    
def main(): 
    
    pp.main_simple(Processor(), 'CMD/BAT')

if __name__ == '__main__': main()

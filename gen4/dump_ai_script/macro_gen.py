from re import sub

from consts import COMMANDS

def snake_case(s):
    return '_'.join(
        sub('([A-Z][a-z]+)', r' \1',
        sub('([A-Z]+)', r' \1',
        s.replace('-', ' '))).split()).lower()

out_file = open('aicmd.inc', 'w')

for i, cmd in enumerate(COMMANDS):
    name = cmd.name
    params = [snake_case(p.__name__) for p in cmd.params]

    print(f'    .macro {name} {", ".join(params)}', file=out_file)
    print(f'    .long {i}', file=out_file)
    for j, p in enumerate(params):
        if p == 'label':
            if j != len(params) - 1:
                print(f'    .long (\\{p}-.) / 4 - 2', file=out_file)
            else:
                print(f'    .long (\\{p}-.) / 4 - 1', file=out_file)
        else:
            print(f'    .long \\{p}', file=out_file)
    print('    .endm\n', file=out_file)

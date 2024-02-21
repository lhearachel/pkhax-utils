from argparse import ArgumentParser
from collections.abc import Iterable
from pathlib import Path
from enum import Enum

from consts import COMMANDS, TYPE_LOADERS, enums, types

def format_params(param: any, labels: dict, i: int, label_offset: int) -> list[str]:
    params = []

    match param:
        case Enum():
            params.append(param.name)
        case types.Label():
            label = f'_{(i + param.addr + label_offset + 1):05}'
            labels[i + param.addr + label_offset + 1] = label
            params.append(label)
        case bool():
            params.append('TRUE' if param else 'FALSE')
        case _:
            params.append(str(param))
    
    return params

def format_loaded(param: any, loaded_type) -> list[str]:
    params = []

    if issubclass(loaded_type, Enum):
        params.append(loaded_type(param.val).name)
    elif loaded_type == bool:
        params.append('TRUE' if param else 'FALSE')
    else:
        params.append(str(param.val))

    return params

def read_table(cur: int, chunks: Iterable, T: Enum) -> list:
    table = []
    val = cur
    while val != 0xFFFFFFFF:
        table.append(f'{T(val).name}')
        val = next(chunks)
    
    table.append('TABLE_END')

    return table

TABLE_LOCATIONS = {
    (0x1B88 // 4): enums.Item,
    (0x2164 // 4): enums.ItemHoldEffect,
    (0x2170 // 4): enums.ItemHoldEffect,
    (0x2178 // 4): enums.ItemHoldEffect,
    (0x3258 // 4): enums.Move,
    (0x3470 // 4): enums.Type,
    (0x3624 // 4): enums.Type,
    (0x392C // 4): enums.Type,
    (0x3ABC // 4): enums.Type,
    (0x4210 // 4): enums.Type,
    (0x4530 // 4): enums.Type,
    (0x49B0 // 4): enums.Type,
    (0x4A34 // 4): enums.BattleEffect,
    (0x4DB0 // 4): enums.ItemHoldEffect,
    (0x57C4 // 4): enums.Type,
    (0x5A8C // 4): enums.Type,
    (0x6024 // 4): enums.ItemHoldEffect,
    (0x603C // 4): enums.ItemHoldEffect,
    (0x6074 // 4): enums.ItemHoldEffect,
    (0x607C // 4): enums.ItemHoldEffect,
    (0x6084 // 4): enums.ItemHoldEffect,
    (0x608C // 4): enums.ItemHoldEffect,
    (0x60E4 // 4): enums.ItemHoldEffect,
    (0x6178 // 4): enums.Ability,
    (0x6310 // 4): enums.Item,
    (0x6A88 // 4): enums.ItemHoldEffect,
    (0x6F4C // 4): enums.Item,
    (0x7064 // 4): enums.ItemHoldEffect,
    (0x7620 // 4): enums.Move,
    (0x83C8 // 4): enums.BattleEffect,
    (0x8524 // 4): enums.BattleEffect,
    (0x867C // 4): enums.Move,
    (0xA02C // 4): enums.BattleEffect,
    (0xA060 // 4): enums.BattleEffect,
    (0xA11C // 4): enums.BattleEffect,
    (0xA1EC // 4): enums.BattleEffect,
    (0xA1F0 // 4): enums.BattleEffect,
    (0xA29C // 4): enums.BattleEffect,
    (0xA490 // 4): enums.BattleEffect,
}

def parse_commands(chunks: Iterable) -> tuple[list, dict, dict]:
    parsed = []
    labels = {}
    tables = {}
    i = 32 # start of the script, after the leading table
    loaded_type = enums.Dummy

    for chunk in chunks:
        # check for tables
        if i in TABLE_LOCATIONS:
            tables[i] = read_table(chunk, chunks, TABLE_LOCATIONS[i])
            labels[i] = f'_{i:05}'
            print(f'@ {hex(i * 4)}: TABLE -> {tables[i]}')
            i = i + len(tables[i])
            continue

        try:
            command = COMMANDS[chunk]
        except IndexError as e:
            print(f'Unrecognized command value: {chunk}; is this a table?\n')
            raise e

        parsed.append(command.name)
        params = []
        j = len(command.params)

        if command.name in TYPE_LOADERS:
            loaded_type = TYPE_LOADERS[command.name]
        
        print(f'@ {hex(i * 4)}: ', end='')
        for param_type in command.params:
            param = param_type(next(chunks))
            j = j - 1
            i = i + 1

            if param_type == types.LoadedVal:
                params.extend(format_loaded(param, loaded_type))
            else:
                params.extend(format_params(param, labels, i, j))
        
        print(f'{command.name} -> {params}')
        parsed.append(params)
        i = i + 1
    
    return parsed, labels, tables
    
def pairwise(it: Iterable) -> Iterable:
    a = iter(it)
    return zip(a, a)

def collect_flag_labels(chunks: Iterable) -> dict:
    labels = {}

    for _ in range(32):
        addr = types.sint(next(chunks), 32)
        label = f'_{addr:05}'
        labels[addr] = label
    
    return labels

def dumps(scr: bytes) -> str:
    flag_table = [int.from_bytes(scr[(i*4):((i+1)*4)], 'little') for i in range(32)]
    chunks = [int.from_bytes(scr[(i*4):((i+1)*4)], 'little') for i in range(32, len(scr) // 4)]

    i = 0
    lines = [
        '    .include "macros/aicmd.inc"',
        '',
        '    .data',
        '',
        '_0000:',
    ]
    
    # The first 32 words of the binary is a list of labels; each is associated with
    # a particular AI flag. We collect its labels and spit them out immediately, as there
    # are duplicates within the table.
    flag_labels = collect_flag_labels(iter(flag_table))
    print(flag_labels)
    for j in flag_table:
        lines.append(f'    TableEntry {flag_labels[types.sint(j, 32)]}')

    # Everything hereafter is part of the AI script.
    # First pass: parse to types, convert labels to strings, record future labels
    parsed, labels, tables = parse_commands(iter(chunks))
    all_labels = labels | flag_labels

    # Second pass: output
    i = 32
    for command, params in pairwise(parsed):        
        while i in tables:
            # each table also has a label
            lines.append(f'\n{all_labels[i]}:')
            lines.extend([f'    TableEntry {value}' for value in tables[i]])
            i = i + len(tables[i])
        
        if i in all_labels:
            lines.append(f'\n{all_labels[i]}:')

        lines.append(f'    {command} {", ".join(params)}')
        i = i + 1 + len(params)
    
    lines.append('')
    return '\n'.join(lines)

def dump(fin_name: str, fout_name: str):
    with open(fin_name, 'rb') as fin, open(fout_name, 'w') as fout:
        scr = fin.read()
        fout.write(dumps(scr))

if __name__ == '__main__':
    ARGP = ArgumentParser(
        description='Dumps bytecode sequences from Gen4 AI script to human-readable text'
    )
    ARGP.add_argument('-i', '--input',
                      help='path to the script file to be dumped',
                      required=True)
    ARGP.add_argument('-o', '--output',
                      help='path to which the parsed script file will be dumped',
                      required=True)
    
    args = ARGP.parse_args()
    dump(args.input, args.output)

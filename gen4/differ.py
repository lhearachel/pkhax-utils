from argparse import ArgumentParser
from dataclasses import dataclass
from enum import StrEnum, auto
from pathlib import Path
from sys import stderr


@dataclass
class NARCDirs:
    cpue_dir: Path
    made_dir: Path
    chunk_size: int = 1


class SupportedNARCs(StrEnum):
    BE_SEQ = auto()
    SUB_SEQ = auto()
    PL_OTHERPOKE = auto()
    PL_POKEGRA = auto()


SUPPORTED_NARCS = {
    SupportedNARCs.BE_SEQ: NARCDirs('res/prebuilt/battle/skill', 'build/res/battle/scripts', 4),
    SupportedNARCs.SUB_SEQ: NARCDirs('res/prebuilt/battle/skill', 'build/res/battle/scripts', 4),
    SupportedNARCs.PL_OTHERPOKE: NARCDirs('tmp/', 'build/res/pokemon'),
    SupportedNARCs.PL_POKEGRA: NARCDirs('tmp/', 'build/res/pokemon'),
}


ARGP = ArgumentParser('narc_diff.py',
                      description='Simple diff-finder for NARC files')
ARGP.add_argument('-p', '--prefix',
                  help='prefix applied to the name of each made file')
ARGP.add_argument('narc_names', metavar='narcs',
                  action='append',
                  choices=SupportedNARCs,
                  help='names of narcs to diff')

diff_dir = Path('diff')
diff_dir.mkdir(parents=True, exist_ok=True)

diff = False
args = ARGP.parse_args()
narcs = map(SupportedNARCs, args.narcs)

for narc in narcs:
    cpue_narc = SUPPORTED_NARCS[narc].cpue_dir / narc + '.narc'
    made_files = SUPPORTED_NARCS[narc].made_dir / narc + '.p'

    # Deflate the CPUE NARC, if it hasn't been already
    cpue_files = diff_dir / f'cpue_{narc.name}'
    cpue_files.mkdir(exist_ok=True)
    cpue_file_count = len(list(cpue_files.glob('*')))
    if cpue_file_count == 0:
        deflate_narc(cpue_narc, cpue_files)

    # Verify number of files matches
    made_file_count = len(list(made_files.glob('*')))
    if cpue_file_count != made_file_count:
        diff = True
        print(f'Diff in file count; CPUE: {cpue_file_count}, PKPT: {made_file_count}', file=stderr)

    # Compare files 1:1
    for i in range(cpue_file_count):
        cpue_file = cpue_files / f'{narc.name}_{i:08}.bin'
        made_file = made_files / f'{args.prefix}_{i:04}.bin'

        cpue_bytes = open(cpue_file, 'rb').read()
        made_bytes = open(made_file, 'rb').read()

        num_cpue_chunks = len(cpue_bytes) // narc.chunk_size
        num_made_chunks = len(made_bytes) // narc.chunk_size
        if num_cpue_chunks != num_made_chunks:
            diff = True
            print(f'Diff in chunk count in file {i:04}.bin; CPUE: {num_cpue_chunks}, PKPT: {num_made_chunks}', file=stderr)

        for chunk_i in range(num_cpue_chunks):
            cpue_chunk = cpue_bytes[chunk_i * narc.chunk_size : (chunk_i + 1) * narc.chunk_size]
            made_chunk = made_bytes[chunk_i * narc.chunk_size : (chunk_i + 1) * narc.chunk_size]

            if int.from_bytes(cpue_chunk, 'little') != int.from_bytes(made_chunk, 'little'):
                diff = True
                print(f'Diff in chunk {chunk_i} in file {i:04}.bin; CPUE: {cpue_chunk.hex()}, PKPT: {made_chunk.hex()}')

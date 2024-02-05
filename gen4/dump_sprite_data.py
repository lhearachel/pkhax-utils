import json
import pathlib

from tools.json2bin.consts.pokemon import species, shadow


def sint(i: int) -> int:
    if i > 127:
        return i - 256
    return i


def dump_frames(frame_data: bytes) -> list:
    assert len(frame_data) == 40

    frames = []
    for i in range(10):
        frame = frame_data[i*4:(i+1)*4]

        frames.append({
            'sprite_frame': sint(frame[0]),
            'frame_delay': frame[1],
            'x_shift': sint(frame[2]),
            'y_shift': sint(frame[3]),
        })
    
    return frames


SPDATA_SIZE = 89

spdata_path = pathlib.Path('tmp/pl_poke_data/pl_poke_data_00000000.bin')
spdata_file = open(spdata_path, 'rb')
spdata = spdata_file.read()
spdata_file.close()

md_spdata_path = pathlib.Path('tmp/pl_poke_data.p/0000.bin')
md_spdata_file = open(md_spdata_path, 'rb')
md_spdata = md_spdata_file.read()
md_spdata_file.close()

height_path = pathlib.Path('tmp/height')


def cmp_spdata(pk: species.PokemonSpecies):
    if pk.value > species.PokemonSpecies.SPECIES_ARCEUS.value:
        return

    og_chunk = spdata[pk.value*89:(pk.value+1)*89]
    md_chunk = md_spdata[pk.value*89:(pk.value+1)*89]
    if og_chunk != md_chunk:
        for i in range(89):
            if og_chunk[i] != md_chunk[i]:
                print(f'Diff for species {pk.name[8:]} @ {i}: expected {og_chunk[i]}, actual {md_chunk[i]}')


def dump_spdata(pk: species.PokemonSpecies) -> dict:
    if pk.value > species.PokemonSpecies.SPECIES_ARCEUS.value:
        return

    if pk == species.PokemonSpecies.SPECIES_NONE:
        spk = '000'
    else:
        spk = pk.name[8:].lower()

    spdata_offs = pk.value * SPDATA_SIZE
    spdata_chunk = spdata[spdata_offs:spdata_offs+SPDATA_SIZE]

    height_offs = pk.value * 4
    female_back_offs = height_offs
    male_back_offs = height_offs + 1
    female_front_offs = height_offs + 2
    male_front_offs = height_offs + 3

    female_back = int.from_bytes(open(height_path / f'height_{female_back_offs:08}.bin', 'rb').read())
    male_back = int.from_bytes(open(height_path / f'height_{male_back_offs:08}.bin', 'rb').read())
    female_front = int.from_bytes(open(height_path / f'height_{female_front_offs:08}.bin', 'rb').read())
    male_front = int.from_bytes(open(height_path / f'height_{male_front_offs:08}.bin', 'rb').read())

    return {
        'front': {
            'y_offset': {
                'female': female_front,
                'male': male_front
            },
            'addl_y_offset': sint(spdata_chunk[86]),
            'animation': spdata_chunk[1],
            'cry_delay': spdata_chunk[0],
            'start_delay': spdata_chunk[2],
            'frames': dump_frames(spdata_chunk[3:43])
        },
        'back': {
            'y_offset': {
                'female': female_back,
                'male': male_back
            },
            'animation': spdata_chunk[44],
            'cry_delay': spdata_chunk[43],
            'start_delay': spdata_chunk[45],
            'frames': dump_frames(spdata_chunk[46:86])
        },
        'shadow': {
            'x_offset': sint(spdata_chunk[87]),
            'size': shadow.ShadowSize(spdata_chunk[88]).name
        }
    }


def dump_all():
    for pk in species.PokemonSpecies:
        if pk.value > species.PokemonSpecies.SPECIES_ARCEUS.value:
            continue

        if pk == species.PokemonSpecies.SPECIES_NONE:
            spk = '000'
        else:
            spk = pk.name[8:].lower()

        new_pkdata = dump_spdata(pk)
        pkdata_path = pathlib.Path('res/pokemon') / spk / 'sprite_data.json'
        with open(pkdata_path, 'w', encoding='utf-8') as pkfile:
            json.dump(new_pkdata, pkfile, indent=4, ensure_ascii=False)

import requests, json, argparse

POKEAPI = 'https://pokeapi.co/api/v2/ability/'
MAX_LINE_LEN = 27 # max supported in vanilla gen4, apparently
ARGPARSER = argparse.ArgumentParser()
ARGPARSER.add_argument('abilities', metavar='name-in-this-case', nargs='+', action='extend')
ARGPARSER.add_argument('--start', default=0)

args = ARGPARSER.parse_args()

by_ability = {}
for ability in args.abilities:
    print(f'processing {ability}...')
    resp = requests.get(POKEAPI + ability).json()
    candidates = {}
    for fte in resp['flavor_text_entries']:
        if fte['language']['name'] != 'en':
            continue

        entry = fte['flavor_text'].replace('\n', ' ')
        words = entry.split()
        lines = []
        curr = ''

        for word in words:
            if len(curr) + len(word) + 1 > MAX_LINE_LEN:
                lines.append(f'{curr[:-1]}\n')
                curr = ''

            curr = curr + word + ' '

        lines.append(curr[:-1])
        desc = ''.join(lines)
        desc = desc.replace('\n', '\\n').replace('\'', '’')

        # Don't add descriptions identical to another already listed
        if any(map(lambda v: v == desc, candidates.values())):
            continue
        
        if len(lines) <= 2:
            candidates[fte['version_group']['name']] = desc

    by_ability[ability] = candidates

print('')

choices = []
for i, (ability, desc_set) in enumerate(by_ability.items(), start=int(args.start)):
    if len(desc_set) == 0:
        print(f'No good description found for {ability}; good luck!')

    # Prompt to pick from the choices
    chosen_desc = list(desc_set.values())[0]

    if len(desc_set) > 1:
        print(f'Collison on {ability}; which would you like?')
        
        for j, (_, desc) in enumerate(desc_set.items(), start=1):
            print(f'    {j} - "{desc}"')
        
        choice = int(input('Choice: '))
        chosen_desc = list(desc_set.values())[choice - 1]

    choices.append((
        f'\t<row id="pl_msg_00000612_{i:05}" index="{i}">\n'
        '\t\t<attribute name="window_context_name">used</attribute>\n'
        f'\t\t<language name="English">{chosen_desc}</language>\n'
        '\t</row>'
    ))

for c in choices:
    print(c)


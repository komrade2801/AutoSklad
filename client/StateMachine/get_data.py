from state_map import states, transitions, screen


def collect_strings_by_key(data_list: list, key: str):
    result = []
    for item in data_list:
        if key.lower() not in item.lower():
            result.append(item)
    return set(result)


def Generator_foo_collect_strings_by_key(data_list: list, key: str):
    result = []
    for item in data_list:
        if key.lower() in item.lower():
            foo = (f"\tdef {item}(self, data: dict, event: list) -> dict:"
                   f"\n\t\tsource = self.{item}.__name__"
                   f"\n\t\tresult = []"
                   f"\n\t\tfor transition in transitions:"
                   f"\n\t\t\tif transition['source'] == source:"
                   f"\n\t\t\t\tresult.append("
                   + "{'trigger': transition['trigger'], 'dest': transition['dest']})" +
                   f"\n\t\treturn data"
                   )

            result.append(foo)
    return set(result)


def find_transitions_get_triggerAnddest_by_source(source):
    result = []

    for transition in transitions:
        if transition['source'] == source:
            result.append({'trigger': transition['trigger'], 'dest': transition['dest']})

            return result


# def e_system_start(self):
#     return self.system_start()

def get_find_transitions(target, key):
    result = []

    for transition in transitions:
        if key.lower() in transition[target].lower():
            result.append(
                f"\tdef e_{transition[target]}(self):\n\t\treturn self.{transition[target]}()\n"
            )
    return set(result)


def collect_strings_not_key(data_list: list, key: str):
    result = []
    for item in data_list:
        if key.lower() not in item['name'].lower():
            result.append(f"\tdef {item['name']}(sef, data: dict, event: dict) -> dict: \n \t\treturn data")
    return set(result)


def group_by_first_key(data_list):
    groups = {}

    for item in data_list:
        first_key = item['name'].split('_', 1)[0]
        if first_key not in groups:
            groups[first_key] = []
        groups[first_key].append(item['name'])

    return groups


if __name__ == "__main__":
    key = "btn_"
    target = "trigger"  # source trigger dest
    found_strings = group_by_first_key(states)
    found_trigger = get_find_transitions(target, key)
    collect = collect_strings_not_key(states, "screen_")
    for i in collect:
        print(i)
        # print(*found_strings)

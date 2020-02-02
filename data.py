import json


def merge(files, output_file_name):
    if len(files) == 0:
        return

    data_objects = []
    for file in files:
        with open(file) as f:
            data_objects.append(json.load(f))

    master = data_objects[0]
    for data in data_objects[1:]:
        for key, value in data.items():
            if key not in master:
                master[key] = value
            else:
                # TODO merge existing benchmarks
                continue
                # raise NotImplementedError

    with open(output_file_name, 'w') as f:
        json.dump(master, f)

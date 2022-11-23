import ujson

def load_config(file_name):
    with open(file_name) as config_file:
        return ujson.loads(config_file.read())


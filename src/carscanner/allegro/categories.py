import yaml


def get_categories():
    with open('categories.yaml') as f:
        return yaml.safe_load(f)

import pprint

import carscanner.allegro


def main():
    client = carscanner.allegro.get_client()

    result = client.get_category_parameters('255460')
    pprint.pprint(result)


if __name__ == '__main__':
    main()

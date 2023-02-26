from argparse import ArgumentParser
import json
import json5
from requests import Session
from loguru import logger

def shutterfly_get_items(site_name: str, node_id: int, session: Session=None) -> 'tuple[str, Session]':
    logger.debug('Getting items for site %s with nodeId %i' % (site_name, node_id))
    payload: 'dict[str, str]' = {
        'startIndex': 0,
        'size': -1,
        'pageSize': -1,
        'page': '%s/pictures' % (site_name,),
        'nodeId': node_id,
        'format': 'js',
    }

    s = session if session else Session()

    logger.info('Posting request')
    response = s.post(
        'https://cmd.shutterfly.com/commands/pictures/getitems?site=%s&' % (site_name,),
        data=payload
    )

    if response.status_code >= 400:
        logger.error('Request failed with status code %i' % (response.status_code,))
        raise Exception("Error: request returned status %i" % (response.status_code,))
    else:
        logger.debug('Request successful')

    return response.text, s


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('site_name', help='Name of the shutterfly site to collect metadata from')
    args = parser.parse_args()

    text, session = shutterfly_get_items(args.site_name, 5)
    logger.info(text)
    pass

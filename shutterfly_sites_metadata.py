from argparse import ArgumentParser
import json
import json5
from requests import Session
from loguru import logger


class ShutterflySitesItem:
    capture_date: int = 0
    node_id: int = 0
    description: str = ''
    title: str = ''
    created: int = 0
    modified: int = 0

    def __init__(self, item_dict: 'dict[str, any]') -> None:
        if item_dict.get('nodeType', '') == 'shutterflyItem':
            self.capture_date = item_dict.get('capture_date', 0)
            self.node_id = item_dict.get('nodeId', 0)
            self.description = item_dict.get('text', '')
            self.title = item_dict.get('title', '')
            self.created = item_dict.get('created', 0)
            self.modified = item_dict.get('modified', 0)
            logger.debug('Created item object with title: %s' % (self.title,))
        else:
            logger.error('Error creating item: input object is not of nodeType "shutterflyItem"')


class ShutterflySitesAlbum:
    title: str = ''
    description_html: str = ''
    created: int = 0
    modified: int = 0
    count: int = 0
    items: 'list[ShutterflySitesItem]' = []
    node_id: int = 0

    def __init__(self, album_dict: 'dict[str, any]') -> None:
        if album_dict.get('nodeType', '') == 'albumGroup':
            self.title = album_dict.get('title', '')
            self.description_html = album_dict.get('text', '')
            self.created = album_dict.get('created', 0)
            self.modified = album_dict.get('modified', 0)
            self.count = album_dict.get('count', 0)
            self.node_id = album_dict.get('nodeId', 0)
            logger.debug('Created album object with title: %s' % (self.title,))
        else:
            logger.error('Error creating album: input object is not of nodeType "albumGroup"')


def shutterfly_get_items(site_name: str, node_id: int, layout: str, session: Session=None) -> 'tuple[str, Session]':
    logger.debug('Getting items for site %s with nodeId %i' % (site_name, node_id))
    payload: 'dict[str, str]' = {
        'startIndex': 0,
        'size': -1,
        'pageSize': -1,
        'page': '%s/pictures' % (site_name,),
        'nodeId': node_id,
        'layout': layout,
        'format': 'js',
    }

    s = session if session else Session()

    logger.info('POST-ing request')
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

    albums_js, session = shutterfly_get_items(args.site_name, 5, 'ManagementAlbums')
    logger.info('Converting js data to dict')
    albums_data: dict = json5.loads(albums_js)

    logger.info('Saving json data to albums.json')
    with open('temp/albums.json', 'w', encoding='utf-8') as json_file:
        json_file.write(json.dumps(albums_data))

    albums: 'list[dict]' = albums_data['result']['section']['groups']
    logger.debug('albums len: %i' % (len(albums),))

    shutter_albums: 'list[ShutterflySitesAlbum]' = []
    for album in albums:
        shutter_album = ShutterflySitesAlbum(album)
        album_js, session = shutterfly_get_items(args.site_name, shutter_album.node_id, 'ManagementAlbumPictures', session)
        logger.info('Converting js data to dict')
        album_data: dict = json5.loads(album_js)

        logger.info('Saving json data to album.json')
        with open('temp/album.json', 'w', encoding='utf-8') as json_file:
            json_file.write(json.dumps(album_data))

        items: 'list[dict]' = album_data['result']['section']['items']
        logger.debug('items len: %i' % (len(items),))

        if len(items) != shutter_album.count:
            logger.error('Incorrect number of items received from items call. Expected %i, got %i' % (shutter_album.count, len(items)))
            raise Exception('Incorrect number of items received from items call. Expected %i, got %i' % (shutter_album.count, len(items)))
        else:
            logger.debug('Got correct number of items for this album')

        for item in items:
            shutter_album_item = ShutterflySitesItem(item)
            shutter_album.items.append(shutter_album_item)

        shutter_albums.append(shutter_album)

    pass

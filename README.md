# HTML to RSS

This is a simple script that converts a HTML page to RSS feed.

It is useful for websites that don't have RSS feed but have a list of links on a page.


## Configuration

### Example configuration

```json
{
    "url": "https://www.monash.edu/students/support/international/events",
    "refresh": 300,
    "alias": "some_alias",
    "rss": {
        "title": "//*[@class='intl-events']/div/div/a/@data-title",
        "url": "//*[@class='intl-events']/div/div/a/@href",
        "image": "//*[@class='intl-events']/div/div//img/@src",
        "description": "//*[@class='intl-events']/div/div//p",
        "guid": "//*[@class='intl-events']/div/div/a/@href",
        "enclosure": {
            "url": "//*[@class='intl-events']/div/div//img/@src"
        }
    }
}
```

`alias` is optional. If not specified, the alias will be the base name of the configuration file. for example, `monash_events.json` will have an alias of `monash_events`.

`refresh` is the number of seconds between each refresh. If not specified, the default value is 300 seconds (5 minutes).

config file can be placed in the config directory or folders in the config directory. For example, `config/monash_events.json` or `config/monash/monash_events.json` are acceptable, as long as the file format is `.json`.

If the nodes found by the XPath expression is not a Unicode Result (`lxml.etree._ElementUnicodeResult`), the script will try to convert it by using `node.xpath("string()")`. It is useful for nodes that contains multiple text nodes.

#### Enclosure

```json
{
    "enclosure": {
        "url": "//*[@class='intl-events']/div/div//img/@src",
        "length": "//*[@class='intl-events']/div/div//img/@length",
        "type": "image/jpeg"
    }
}
```

Enclosure is optional. If not specified, the enclosure will not be included in the RSS feed.

If both `length` and `type` are not specified, it will do a HTTP HEAD request to get the length and type of the file.

### Config Directory

The default config directory is `config`. It can be changed by setting the environment variable `HTML2RSS_CONFIG_FOLDER`.

### HOST and PORT

By default, the API server will run on port 8000, host `0.0.0.0`

You can change the host and port by setting the environment variable `UVICORN_HOST` and `UVICORN_PORT` respectively.

## Usage

### CLI

1. Clone this project
2. Install dependencies by running `pip3 install -r requirements.txt`
3. Setup all the configuration files in the `config` directory
4. Run `uvicorn html2rss.api:app --log-config ./conf/log.yml`

### Docker

```bash
docker run -d \
    -v /path/to/config:/app/config \
    -p 8000:8000 \
    --name html2rss \
    --restart unless-stopped \
    rankki/html2rss:latest
```

### API

```bash
curl -X GET http://127.0.0.1:8000/rss/<alias_or_url>
```

You can use the alias or the url of the configuration file.
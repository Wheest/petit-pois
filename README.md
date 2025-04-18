<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/Wheest/petit-pois/">
    <img src="logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">Petit Pois</h3>

  <p align="center">
    A tool to archive podcasts and create a feed for them.
    <br />
  </p>
</div>

## Usage

Create a `feeds.jsonl` file with the following format:

``` sh
{"url": "https://pod.url1.com/FFFFF", "name": "Podname XYZ"}
{"url": "https://pod.url2.com/FFFFF", "name": "Podname ABC"}
{"url": "https://pod.url3.com/FFFFF", "name": "Podname DEF"}
```

### Download podcasts

Next, run the script to download all the missing episodes and metadata.  By default it will be stored under the `pods` directory, with one sub-directory per podcast.
We recommend if you plan on serving this over the web to use a different directory, such as `/srv/www/petit-pois/pods`.

``` sh
python3 download_podcasts.py \
  --archive_dir /srv/www/petit-pois/pods
```

### Generate podcast feed tokens (optional)

Again, if you're interested serving, we don't want expose the podcast to just anyone, so we need to create a token for each podcast.  This is done by running the `generate_tokens.py` script:

``` sh
sudo python3 generate_token_map.py \
  --archive_dir /srv/www/petit-pois/pods \
  --map_file /etc/nginx/podcast_tokens.map
```

### Generate podcast feeds (optional)

Next, run the script to generate the feeds, with the optional inclusion of a token map file:

``` sh
python3 generate_feeds.py \
  --archive_dir /srv/www/petit-pois/pods \
  --base_url http://yourdomain.com/pods
```

Now, each podcast will have a `archive.xml` file in its directory.

If you want to serve the files using a web-server, there are a few options.  The next section gives an example using Nginx.

## ⚠️ Disclaimer

This tool is meant for personal archival, preservation, and research use only. It helps you download and locally serve podcast episodes and metadata to create a self-hosted or offline archive.

Please make sure you're respecting copyright laws and the original creators' terms of use. Many podcasts are protected by copyright, and redistributing or republishing them (especially publicly) without permission might be illegal.

Before archiving or sharing anything, it’s a good idea to:

- Check the podcast's license or usage terms
- Look for any [Creative Commons](https://creativecommons.org/) indicators
- Read up on [fair use](https://en.wikipedia.org/wiki/Fair_use) if you're in the U.S., or [fair dealing](https://en.wikipedia.org/wiki/Fair_dealing) in other countries such as the U.K.

## Nginx Example

Install Nginx:

``` sh
sudo apt update && sudo apt install nginx
```

Create a config file (e.g., `/etc/nginx/sites-available/petit-pois`):


``` sh
map $secure_token $podcast_dir {
    default "";
    include /etc/nginx/podcast_tokens.map;
}

server {
    server_name podcasts.archive.example.com;

    location ~ ^/secure/([^/]+)/(.+)$ {
    set $secure_token $1;
    set $filename $2;

    if ($podcast_dir = "") {
        return 403;
    }

    # Optional debug logging
    error_log /var/log/nginx/podcast_debug.log info;

    root /srv/www/petit-pois/pods;
    try_files /$podcast_dir/$filename =404;
}


    # Optional: deny bare token URLs like /secure/abc123/
    location ~ ^/secure/([^/]+)/?$ {
        return 403;
    }

    location /pods/ {
        deny all;
    }


    location = / {
        deny all;
    }


    ###### 🔐 TLS CONFIG (UNCHANGED) ######
    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/podcasts.archive.example.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/podcasts.archive.example.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}

server {
    if ($host = podcasts.archive.example.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

    listen 80;
    server_name podcasts.archive.example.com;
    return 404; # managed by Certbot
}

```

Enable the site and restart nginx:

``` sh
sudo ln -s /etc/nginx/sites-available/petit-pois /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Further information on Nginx and web server configuration is outwith the scope of this guide.

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
Next, run the script to download all the missing episodes and metadata.  By default it will be stored under the `pods` directory, with one sub-directory per podcast.

``` sh
python3 download_podcasts.py
```

Next, run the script to generate the feeds:

``` sh
python3 generate_feeds.py --base_url http://yourdomain.com/pods
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
server {
    listen 80;
    server_name archive.example.com;

    root /srv/podcast-archive/; # Change to your directory

    location /pods/ {
        autoindex on;  # optional, shows file listings
        try_files $uri $uri/ =404;
    }

    location / {
        return 302 /pods/;
    }
}
```

Enable the site and restart nginx:

``` sh
sudo ln -s /etc/nginx/sites-available/petit-pois /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Further information on Nginx and web server configuration is outwith the scope of this guide.

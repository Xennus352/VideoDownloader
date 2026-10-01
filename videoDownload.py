import cloudscraper, sys, os, re, time

def download_video(url, output=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    scraper = cloudscraper.create_scraper()

    if not output:
        ep_match = re.search(r'episode[^\d]*(\d+)', url, re.I)
        ep = ep_match.group(1) if ep_match else 'unknown'
        output = f'Episode {ep}.mp4'

    if os.path.exists(output):
        print(f'  [!] {output} already exists, skipping')
        return output

    print(f'  [*] Fetching page ...')
    r = scraper.get(url, headers=headers)
    if r.status_code != 200:
        print(f'  [!] Failed to load page: {r.status_code}')
        return None

    srcs = re.findall(r'<source\s+src=["\']([^"\']+)["\']', r.text)
    if not srcs:
        print(f'  [!] No video source found')
        return None

    video_url = srcs[0]
    print(f'  [*] Source: {video_url}')

    video_headers = {
        'User-Agent': headers['User-Agent'],
        'Accept': 'video/mp4,video/*,*/*',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://smrstream.site/',
        'Range': 'bytes=0-',
    }

    print(f'  [*] Downloading ...')
    r2 = scraper.get(video_url, headers=video_headers, stream=True)
    if r2.status_code not in (200, 206):
        print(f'  [!] Download failed: {r2.status_code}')
        return None

    total = int(r2.headers.get('Content-Length', 0))
    dl = 0
    with open(output, 'wb') as f:
        for chunk in r2.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                dl += len(chunk)
                if total:
                    pct = dl * 100 // total
                    print(f'\r  [*] {pct}% ({dl//1024//1024}MB / {total//1024//1024}MB)', end='', flush=True)

    mb = dl / 1024 / 1024
    print(f'\n  [+] Saved: {output} ({mb:.0f}MB)')
    return output


def download_from_file(links_path):
    links_path = os.path.abspath(links_path)
    out_dir = os.path.dirname(links_path)

    if not os.path.exists(links_path):
        print(f'[!] File not found: {links_path}')
        sys.exit(1)

    with open(links_path) as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    if not urls:
        print('[!] No URLs found in file')
        sys.exit(1)

    print(f'[*] Found {len(urls)} URLs in {os.path.basename(links_path)}')
    print(f'[*] Output folder: {out_dir}')
    print()

    ok = 0
    fail = 0
    for i, url in enumerate(urls, 1):
        print(f'[{i}/{len(urls)}] {url}')
        out = download_video(url)
        if out:
            ok += 1
        else:
            fail += 1
        print()
        if i < len(urls):
            time.sleep(1)

    print(f'[+] Done: {ok} succeeded, {fail} failed')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage:')
        print('  python videoDownload.py <smrstream.url>             # single video')
        print('  python videoDownload.py <path/to/links.txt>        # batch from file')
        sys.exit(1)

    arg = sys.argv[1]
    if arg.endswith('.txt') and os.path.exists(arg):
        download_from_file(arg)
    else:
        output = sys.argv[2] if len(sys.argv) > 2 else None
        download_video(arg, output)

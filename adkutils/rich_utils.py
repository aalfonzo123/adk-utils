from urllib.parse import urlparse, parse_qs

def rich_format_url(url):
    url_parts = urlparse(url)
    qs_parts = parse_qs(url_parts.query)
    formatted_url = url_parts.scheme + "://" + url_parts.netloc + url_parts.path
    first = True

    # note: this does not handle multiple values    
    for k in sorted(qs_parts.keys()):       
        for v in qs_parts[k]:
            if first:
                first = False
                separator = "?"
            else:
                separator = "&"
            formatted_url += f"[yellow]{separator}[/yellow][green]{k}[/green]={v}" 
    return formatted_url
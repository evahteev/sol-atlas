import re

def on_post_page(output, page, config):
    """Make asset and page paths absolute using base_path from config"""
    # Get base_path from config, default to /docs if not set
    base_path = config.get('extra', {}).get('base_path', '/docs')

    # Replace relative asset paths with absolute ones
    output = re.sub(
        r'(href|src)="assets/',
        rf'\1="{base_path}/assets/',
        output
    )

    # Replace relative page links (e.g., href="getting-started.html" or href="../index.html")
    # First handle parent directory links like ../something.html
    output = re.sub(
        r'href="\.\./([^"]*\.html)"',
        rf'href="{base_path}/\1"',
        output
    )

    # Then handle same directory links like something.html (but not absolute or external links)
    output = re.sub(
        r'href="(?!http|/|#)([^"]*\.html)"',
        rf'href="{base_path}/\1"',
        output
    )

    return output

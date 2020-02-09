import sys, os, importlib, shutil
import http.server
import socketserver
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from content_type.content import Content

def collect_site_content():
    site = {
        "config": {
            "title": "",
            "subtitle": "",
            "theme": "default",
            "url": "http://127.0.0.1:8000/",
            "staticurl": "/static/theme"
        },
        "content_type": [],
        "content": {}
    }
    for type_name in os.listdir("content"):
        ent = os.path.join("content", type_name)
        if type_name == "static":
            dst = os.path.join("public", "static", "content")
            Path(os.path.join("public", "static")).mkdir(parents=True, exist_ok=True)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(ent, dst)
        elif type_name == "site.md":
            content = Content(ent)
            site["config"].update(content.meta)
        elif os.path.isdir(ent):
            content_class = \
                getattr(\
                    importlib.import_module("content_type." + type_name),\
                    type_name.capitalize()\
                )
            site["content_type"].append(type_name)
            site["content"][type_name] = []
            for root, dirs, files in os.walk(ent):
                for name in files:
                    post = content_class(os.path.join(root, name))
                    site["content"][type_name].append(post)
            
    return site

def process_theme(site):
    theme_path = os.path.join("theme", site["config"]["theme"])
    if os.path.exists(os.path.join(theme_path, "static")):
            dst = os.path.join("public", "static", "theme")
            Path(os.path.join("public", "static")).mkdir(parents=True, exist_ok=True)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(os.path.join(theme_path, "static"), dst)
    env = Environment(
        loader=FileSystemLoader(theme_path)
    )
    theme = {
        "index": env.get_template("index.html"),
        "single": {}
    }
    for content_type in site["content_type"]:
        theme["single"][content_type] = env.get_template("%s.html" % content_type)
    return theme

def generate_site(site, theme):
    print("writing index.html")
    with open(os.path.join("public", "index.html"), "w") as f:
        f.write(theme["index"].render(site))
    for content_type in site["content_type"]:
        for post in site["content"][content_type]:
            print('writing', content_type, "with name", post.filename, "into", post.permalink)
            Path("public/" + post.path).mkdir(parents=True, exist_ok=True)
            with open(Path("public" + post.permalink), "w") as f:
                f.write(theme["single"][content_type].render({
                    "config": site["config"],
                    "content_type": site["content_type"],
                    "content": site["content"],
                    content_type: post
                }))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "serve":
            PORT = 8000
            web_dir = os.path.join(os.path.dirname(__file__), 'public')
            os.chdir(web_dir)

            Handler = http.server.SimpleHTTPRequestHandler
            socketserver.TCPServer.allow_reuse_address = True
            httpd = socketserver.TCPServer(("", PORT), Handler)
            print("serving at port", PORT)
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                httpd.shutdown()
                httpd.server_close()
    else:
        site = collect_site_content()
        theme = process_theme(site)
        generate_site(site, theme)
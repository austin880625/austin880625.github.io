import os

class Content:
    def __init__(self, name):
        self.meta = {
            "path": ""
        }
        self.filename = os.path.basename(name)
        self.raw_content = ""
        with open(name) as f:
            lines = f.readlines()
            for (i, line) in enumerate(lines):
                if line.strip() == "---":
                    self.raw_content = "".join(lines[i+1:])
                    break
                else:
                    kv = line.split(":")
                    key = kv[0]
                    self.meta[key] = ""
                    if len(kv) < 2:
                        continue
                    value = kv[1].strip()
                    self.meta[key] = value
        name_ext = os.path.splitext(self.filename)
        self.path = self.meta.get("path")
        if self.path == None or self.path == "":
            self.permalink = "/" + name_ext[0]
        else:
            self.permalink = "/" + self.path + "/" + name_ext[0]
        self.file_type = name_ext[-1]
    def get_content(self):
        return self.raw_content
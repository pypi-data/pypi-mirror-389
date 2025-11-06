from __future__ import annotations

import re
import hashlib
from urllib.parse import quote

QQ_MAIL = re.compile(r"^[1-9]\d{4,10}@qq.com$")


class AvatarConvertor:
    def __init__(self, **options):
        self.options = options

    def convert(self, email: str, name: str | None) -> str:
        if QQ_MAIL.match(email):
            qq_num = email.replace("@qq.com", "")
            return f"https://thirdqq.qlogo.cn/g?b=sdk&nk={qq_num}&s=140"

        email_sha = hashlib.sha256(email.encode("utf-8")).hexdigest()
        default_size = self.options.get("size", 400)
        url = f"https://gravatar.com/avatar/{email_sha}?s={default_size}"
        if name:
            return f"{url}&d=initials&name={quote(name)}"
        else:
            gravatar_default = self.options.get("gravatar_default", "robohash")
            return f"{url}&d={gravatar_default}"

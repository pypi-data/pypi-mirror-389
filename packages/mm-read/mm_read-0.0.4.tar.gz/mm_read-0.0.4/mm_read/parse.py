import re

sub_trailing_spaces = re.compile(r"[ \t]+$", re.MULTILINE)
sub_multiple_lines = re.compile(r"\n{3,}")


def post_process(text: str):
    text = text.replace("\r", "")
    text = sub_trailing_spaces.sub("", text)
    text = sub_multiple_lines.sub("\n\n", text)
    return text


def normalize_links(markdown: str, baseurl: str) -> str:
    from mistune import create_markdown
    from mistune.renderers.markdown import MarkdownRenderer

    if "#" in baseurl:
        baseurl = baseurl.split("#", 1)[0]

    class LinkNormalizingRenderer(MarkdownRenderer):
        def link(self, token, state):
            attrs: dict = token["attrs"]
            url: str = attrs["url"]
            if "#" in url:
                rest, hash = url.split("#", 1)
                if rest == baseurl:
                    attrs["url"] = f"#{hash}"
            return super().link(token, state)

    processor = create_markdown(renderer=LinkNormalizingRenderer())

    return processor(markdown)  # type: ignore


def to_markdown(html: str, baseurl: str):
    from html2text import html2text

    md = html2text(html, baseurl, bodywidth=0)
    md = normalize_links(md, baseurl)

    return post_process(md)

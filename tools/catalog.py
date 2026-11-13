"""Generate the Chinese GitHub Pages catalog from the repository's style data."""

import argparse
import re
import shutil
from html import escape
from pathlib import Path

import build
import styles

ROOT = build.ROOT
SOURCE = build.HERE / "catalog"
NEEDS = {"code": "代码可做", "mixed": "代码 + 素材", "art": "主要靠美术"}
UPSTREAM_GALLERY = "https://homkathon.github.io/awesome-opus-game-art-styles/x-posts/"
DEMO_IDS = {file.stem for file in (ROOT / "demos").glob("*.html")} - {"index"}


def link(url, label):
    return f'<a href="{escape(url)}">{escape(label)}</a>'


def screenshot(ref, *, eager=False):
    game_id, url = build.shot(ref)
    name = escape(styles.GAMES[int(game_id)])
    loading = "" if eager else ' loading="lazy"'
    return f'<img src="{escape(url)}" alt="{name} 游戏截图"{loading} decoding="async">'


def layout(title, prefix, content, *, catalog=False):
    back = link(prefix, "游戏画风图鉴")
    demos = link(f"{prefix}../demos/", "着色器演示")
    gallery = link(UPSTREAM_GALLERY, "X 技术帖")
    script = '<script src="catalog.js" defer></script>' if catalog else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<link rel="stylesheet" href="{prefix}catalog.css">
{script}
</head>
<body>
<a class="skip" href="#main">跳到正文</a>
<header class="top"><nav class="wrap" aria-label="主导航">
  {back}<div>{demos}{gallery}</div>
</nav></header>
<main id="main" class="wrap">
{content}
</main>
<footer class="wrap">{link(build.REPO, "画风资料来源 · GitHub")} <span>游戏截图由 Steam 提供</span></footer>
</body>
</html>
"""


def card(style):
    sid = style["id"]
    need = styles.NEEDS[sid][0]
    games = [styles.GAMES[game] for game in style["games"]]
    summary = styles.SUMMARY_ZH[sid]
    keywords = " ".join([
        style["zh"], style["title"], summary, *games,
        *styles.TECHNIQUES_ZH[sid], *style["techniques"],
    ])
    demo = '<span class="demo-mark">有演示</span>' if sid in DEMO_IDS else ""
    return f"""<article class="card" data-need="{need}" data-search="{escape(keywords)}">
  <a href="{escape(sid)}/">
    {screenshot(style["hero"])}
    <div class="card-copy">
      <div class="meta">{NEEDS[need]}{demo}</div>
      <h3>{escape(style["zh"])}</h3>
      <span class="en">{escape(style["title"])}</span>
      <p>{escape(summary)}</p>
      <p class="games">{escape(" · ".join(games))}</p>
    </div>
  </a>
</article>"""


def home():
    groups = []
    for index, name in enumerate(styles.SECTIONS_ZH):
        cards = "\n".join(card(style) for style in styles.STYLES if style["section"] == index)
        groups.append(f"""<section class="group" data-section="{index}">
  <h2>{escape(name)}</h2>
  <div class="cards">{cards}</div>
</section>""")
    categories = "".join(f'<option value="{i}">{escape(name)}</option>'
                         for i, name in enumerate(styles.SECTIONS_ZH))
    requirements = "".join(f'<option value="{key}">{label}</option>' for key, label in NEEDS.items())
    total = len(styles.STYLES)
    return layout("游戏画风图鉴", "./", f"""
<div class="intro">
  <h1>游戏画风图鉴</h1>
  <p>从 {total} 种画风中找到你的游戏想要的视觉效果。每种都有参考游戏、实现技术和可交给编程智能体的步骤。</p>
</div>
<form class="filters" hidden>
  <label>搜索<input type="search" name="q" placeholder="画风、游戏或技术，例如 Hades"></label>
  <label>分类<select name="section"><option value="">全部分类</option>{categories}</select></label>
  <label>制作需求<select name="need"><option value="">全部需求</option>{requirements}</select></label>
  <button type="reset">清除筛选</button>
</form>
<p class="count" role="status">{total} 种画风</p>
<p class="empty" hidden>没有符合条件的画风。试试其他关键词或清除筛选。</p>
{"".join(groups)}
""", catalog=True)


def item_text(text):
    parts = re.split(r"`([^`]+)`", text)
    return "".join(f"<code>{escape(part)}</code>" if i % 2 else escape(part)
                   for i, part in enumerate(parts))


def item_list(title, items, *, ordered=False):
    entries = "".join(f"<li>{item}</li>" for item in items)
    if not entries:
        return ""
    tag = "ol" if ordered else "ul"
    return f'<section><h2>{title}</h2><{tag}>{entries}</{tag}></section>'


def detail(style):
    sid = style["id"]
    need = styles.NEEDS[sid][0]
    demo = link(f"../../demos/{sid}.html", "运行着色器演示") if sid in DEMO_IDS else ""
    gallery = []
    for index, ref in enumerate([style["hero"], *style["gallery"]]):
        game_id, _ = build.shot(ref)
        game = escape(styles.GAMES[int(game_id)])
        gallery.append(f"""<figure><a href="{build.store(game_id)}">
          {screenshot(ref, eager=index == 0)}</a><figcaption>{game}</figcaption></figure>""")
    learn_links = [f"{link(url, title)} · {escape(credit)}"
                   for title, url, credit in (styles.LEARN[key] for key in style["learn"])]
    asset_links = [f"{link(url, name)} · {escape(licence)}"
                   for name, url, licence in (styles.ASSETS[key] for key in style["assets"])]
    sections = [
        item_list("怎么认出来", map(item_text, styles.SPOT_ZH[sid])),
        item_list("实现技术", map(item_text, styles.TECHNIQUES_ZH[sid])),
        item_list("实现步骤", map(item_text, styles.AGENT_ZH[sid]), ordered=True),
        item_list("参考游戏", (link(build.store(g), styles.GAMES[g]) for g in style["games"])),
        item_list("教程与资料", learn_links),
        item_list("入门素材与许可", asset_links),
        item_list("相近画风", (link(f"../{other}/", build.BY_ID[other]["zh"]) for other in style["similar"])),
    ]
    return layout(f'{style["zh"]} · 游戏画风图鉴', "../", f"""
<article class="detail">
  <p class="breadcrumb">{link("../", "← 全部画风")} / {escape(styles.SECTIONS_ZH[style["section"]])}</p>
  <div class="intro">
    <span class="en">{escape(style["title"])}</span>
    <h1>{escape(style["zh"])}</h1>
    <p>{escape(styles.SUMMARY_ZH[sid])}</p>
    <div class="meta"><strong>{NEEDS[need]}</strong> {escape(styles.NEEDS_ZH.get(sid, ""))}</div>
    <div class="demo-link">{demo}</div>
  </div>
  <section>
    <h2>游戏截图</h2>
    <div class="screenshots">{"".join(gallery)}</div>
  </section>
  <div class="notes">{"".join(sections)}</div>
</article>
""")


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    if errors := build.validate():
        parser.exit(1, "\n".join(errors) + "\n")
    write(output / "index.html", """<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><title>游戏画风图鉴</title>
<meta http-equiv="refresh" content="0; url=styles/">
<a href="styles/">打开游戏画风图鉴</a></html>
""")
    catalog = output / "styles"
    write(catalog / "index.html", home())
    for style in styles.STYLES:
        write(catalog / style["id"] / "index.html", detail(style))
    for name in ("catalog.css", "catalog.js"):
        shutil.copyfile(SOURCE / name, catalog / name)
    shutil.copytree(ROOT / "demos", output / "demos", dirs_exist_ok=True)
    print(f"Built {len(styles.STYLES)} catalog entries in {output}")


if __name__ == "__main__":
    main()

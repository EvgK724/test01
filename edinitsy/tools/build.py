#!/usr/bin/env python3
"""Сборка: data.js (единицы) + tools/template.html → index.html. Запуск из корня репозитория: python3 edinitsy/tools/build.py"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    tpl = (ROOT / "tools" / "template.html").read_text()
    data = (ROOT / "data.js").read_text().replace("</", "<\\/")
    (ROOT / "index.html").write_text(tpl.replace("/*__DATA__*/", data))
    print("→ edinitsy/index.html")


if __name__ == "__main__":
    main()

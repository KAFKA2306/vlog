#!/usr/bin/env python3

import re
import argparse
from pathlib import Path


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def save_text(path: Path, txt: str) -> None:
    path.write_text(txt, encoding="utf-8")


def remove_fillers(txt: str, mask: bool = False, aggressive: bool = False) -> str:
    fillers = [
        r"えー",
        r"あのー",
        r"うーん",
        r"えっと",
        r"なんて",
        r"まあ",
        r"そうですね",
        r"あー",
        r"んー",
    ]

    if aggressive:
        fillers.extend(
            [
                r"うん",
                r"ふん",
                r"あ",
                r"はは",
                r"ははは",
                r"なんか",
                r"え",
                r"お",
                r"ふんふん",
                r"ふんふんふん",
                r"うんうん",
                r"うんうんうん",
                r"はいはい",
                r"はいはいはい",
                r"はいはいはいはい",
                r"おー",
            ]
        )

    fillers.sort(key=len, reverse=True)
    pattern_str = "|".join(fillers)
    pattern = f"(?:^|\\s)({pattern_str})(?=[\\s、。?!]|$)"

    def repl(m):
        if mask:
            return " [FILLER] "
        return " "

    prev_txt = ""
    while txt != prev_txt:
        prev_txt = txt
        txt = re.sub(pattern, " ", txt)

    txt = re.sub(r"\s+", " ", txt).strip()

    txt = re.sub(r"([、。])\1+", r"\1", txt)
    txt = re.sub(r"^[、。]+", "", txt).strip()
    txt = re.sub(r"\s+[、。]+", "", txt)
    txt = re.sub(r"\s+", " ", txt).strip()

    return txt


def dedupe_words(txt: str) -> str:
    return re.sub(r"(\S+)\s+\1\b", r"\1", txt)


def merge_lines(txt: str) -> str:
    txt = txt.replace("\n", " ")
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def main():
    parser = argparse.ArgumentParser(description="Preprocess transcript for LLM")
    parser.add_argument("infile", type=Path, help="Input file path")
    parser.add_argument("-o", "--outfile", type=Path, help="Output file path")
    parser.add_argument(
        "--remove-fillers", action="store_true", help="Remove common fillers"
    )
    parser.add_argument(
        "--merge-lines", action="store_true", help="Merge all lines into one paragraph"
    )
    parser.add_argument(
        "--mask-fillers", action="store_true", help="Replace fillers with [FILLER]"
    )
    parser.add_argument(
        "--aggressive", action="store_true", help="Aggressive filler removal"
    )
    parser.add_argument(
        "--dedupe", action="store_true", help="Deduplicate consecutive words"
    )

    args = parser.parse_args()

    if not args.infile.exists():
        print(f"Error: File {args.infile} not found.")
        return

    txt = load_text(args.infile)

    if args.remove_fillers:
        txt = remove_fillers(txt, mask=args.mask_fillers, aggressive=args.aggressive)

    if args.dedupe:
        txt = dedupe_words(txt)

    if args.merge_lines:
        txt = merge_lines(txt)

    if args.outfile:
        save_text(args.outfile, txt)
        print(f"Processed text saved to {args.outfile}")
    else:
        print(txt)


if __name__ == "__main__":
    main()

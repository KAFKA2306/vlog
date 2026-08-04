import json
from pathlib import Path
from typing import Any, Dict, List

import google.generativeai as genai

from src.infrastructure.graph_storage import GraphStorage
from src.infrastructure.settings import settings


class ExtractGraphUseCase:
    def __init__(self, storage: GraphStorage):
        self.storage = storage
        self._model = None

    def execute(self, summary_path: Path) -> int:
        if not summary_path.exists():
            return 0

        if self.storage.is_source_processed(summary_path.name):
            return 0

        print(f"Extracting graph from {summary_path.name}...")
        content = summary_path.read_text(encoding="utf-8")
        triples = self._extract_with_llm(content)

        self.storage.add_triples(triples, source=summary_path.name)
        if triples:
            print(f"  -> Extracted {len(triples)} triples")
            return len(triples)
        return 0

    def _extract_with_llm(self, text: str) -> List[Dict[str, Any]]:
        if not self._model:
            genai.configure(api_key=settings.gemini_api_key)
            self._model = genai.GenerativeModel(settings.gemini_model)

        profile_text = (
            settings.profile_path.read_text(encoding="utf-8")
            if settings.profile_path.exists()
            else ""
        )
        profile_content = (
            f"\n【かふかの不変の制約・背景】\n{profile_text}\n" if profile_text else ""
        )

        prompt = (
            "以下のテキスト（VRChatの活動ログ要約）から、\n"
            "重要なエンティティ（人物、場所、出来事、概念、好み）とその関係性を抽出してください。\n"
            "出力は以下のJSONリスト形式のみにしてください。他の説明は不要です。\n"
            f"{profile_content}\n"
            "【抽出のルール】\n"
            "- 日記の主役（投稿者、筆者、著者、私など）は、\n"
            "  主語として「かふか」という名前に統一してください。\n"
            "- 述語（predicate）および目的語（object）は\n"
            "  必ず日本語で抽出してください。\n"
            "- 上記の【不変の制約・背景】に矛盾しないように抽出してください。\n"
            "- 偏屈または極端に鋭すぎる（とがりすぎた）表現は避け、"
            "事実を淡々と抽出してください。\n"
            "- 重複する情報は避け、"
            "新しい事実や重要な関係性を優先してください。\n\n"
            "形式:\n"
            "[\n"
            '  {"subject": "主語", "predicate": "関係（動詞など）", '
            '"object": "目的語/属性"}\n'
            "]\n\n"
            "例:\n"
            f'- {{"subject": "かふか", "predicate": "訪れた", "object": "ラウンジ"}}\n'
            f'- {{"subject": "かふか", "predicate": "は", "object": "AI開発者"}}\n'
            f'- {{"subject": "かふか", "predicate": "好む", "object": "Unity"}}\n\n'
            "テキスト:\n"
            f"{text}\n"
        )
        response = self._model.generate_content(prompt)
        result_text = response.text.strip()

        # Extract JSON block
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        return json.loads(result_text)

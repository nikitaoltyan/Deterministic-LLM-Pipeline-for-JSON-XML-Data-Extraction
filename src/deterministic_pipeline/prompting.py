from __future__ import annotations

import json

from deterministic_pipeline.contracts import PromptPackage
from deterministic_pipeline.reproducibility import sha256_json, sha256_text


def get_prompt_template_spec(version: str) -> dict:
    if version != "v1":
        raise ValueError("Unsupported prompt template version: {0}".format(version))
    return {
        "template_version": version,
        "system_template": (
            "You produce JSON only. "
            "Return a single JSON document that follows the provided schema and required fields exactly."
        ),
        "user_template_parts": {
            "prefix": "Input text:\n",
            "schema_header": "\n\nSchema:\n",
            "grammar_header": "\n\nGrammar artifact:\n",
        },
    }


def build_prompt(normalized_text: str, schema: dict, grammar: dict, prompt_template: dict) -> PromptPackage:
    system_prompt = prompt_template["system_template"]
    user_template_parts = prompt_template["user_template_parts"]
    grammar_summary = {
        "artifact_version": grammar.get("artifact_version"),
        "formalism": grammar.get("formalism"),
        "schema_name": grammar.get("schema_name"),
        "fingerprint": grammar.get("fingerprint"),
        "root_type": grammar.get("root_type"),
        "required": grammar.get("required"),
        "properties": grammar.get("properties"),
    }
    schema_text = json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    grammar_text = json.dumps(grammar_summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    user_prompt = (
        user_template_parts["prefix"]
        + normalized_text
        + user_template_parts["schema_header"]
        + schema_text
        + user_template_parts["grammar_header"]
        + grammar_text
    )
    template_metadata = {
        "template_version": prompt_template["template_version"],
        "template_fingerprint": sha256_json(prompt_template),
        "system_template_hash": sha256_text(system_prompt),
        "user_template_structure_hash": sha256_json(user_template_parts),
        "schema_embedding_hash": sha256_text(schema_text),
        "grammar_summary_hash": sha256_text(grammar_text),
    }
    return PromptPackage(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=schema,
        grammar=grammar,
        template_metadata=template_metadata,
    )

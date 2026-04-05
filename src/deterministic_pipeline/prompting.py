from __future__ import annotations

import json

from deterministic_pipeline.contracts import PromptPackage
from deterministic_pipeline.formats import StructuredFormat
from deterministic_pipeline.reproducibility import sha256_json, sha256_text


def get_prompt_template_spec(version: str, output_format: StructuredFormat = StructuredFormat.JSON) -> dict:
    if version != "v1":
        raise ValueError("Unsupported prompt template version: {0}".format(version))
    if output_format == StructuredFormat.JSON:
        system_template = (
            "You produce JSON only. "
            "Return a single JSON document that follows the provided schema and required fields exactly."
        )
        schema_label = "Schema"
        grammar_label = "Grammar artifact"
    elif output_format == StructuredFormat.XML:
        system_template = (
            "You produce XML only. "
            "Return a single XML document with one root element that follows the provided structural constraints."
        )
        schema_label = "Source schema"
        grammar_label = "XML runtime artifact"
    else:
        raise ValueError("Unsupported output format for prompt template: {0}".format(output_format.value))
    return {
        "template_version": version,
        "output_format": output_format.value,
        "system_template": system_template,
        "user_template_parts": {
            "prefix": "Input text:\n",
            "schema_header": f"\n\n{schema_label}:\n",
            "grammar_header": f"\n\n{grammar_label}:\n",
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

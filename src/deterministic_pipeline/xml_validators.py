from __future__ import annotations

from typing import Any

from deterministic_pipeline.contracts import ValidationIssue


class XmlBaselineValidator:
    def validate(self, document: dict[str, Any], schema: dict[str, Any]) -> list[ValidationIssue]:
        if not document.get("tag"):
            return [ValidationIssue(path="$", message="XML root element must define a tag.", validator="xml_root")]
        children = document.get("children", [])
        if children is not None and not isinstance(children, list):
            return [ValidationIssue(path="$.children", message="XML children must be a list when present.", validator="xml_structure")]
        if schema.get("formalism") == "normalized-xsd-subset":
            return _validate_against_normalized_xsd(document, schema["normalized_schema"]["root_element"], "$")
        return []


def _validate_against_normalized_xsd(
    document: dict[str, Any],
    schema_element: dict[str, Any],
    path: str,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if document.get("tag") != schema_element["name"]:
        issues.append(
            ValidationIssue(
                path=path,
                message=f"Expected XML element <{schema_element['name']}> but found <{document.get('tag')}>.",
                validator="xsd_element_name",
            )
        )
        return issues

    attributes = document.get("attributes", {})
    if not isinstance(attributes, dict):
        issues.append(ValidationIssue(path=f"{path}.attributes", message="XML attributes must be an object.", validator="xml_structure"))
        return issues
    unexpected_attributes = sorted(set(attributes.keys()) - set(schema_element.get("attributes", {}).keys()))
    for name in unexpected_attributes:
        issues.append(
            ValidationIssue(
                path=f"{path}.@{name}",
                message=f"Unexpected XML attribute '{name}'.",
                validator="xsd_unexpected_attribute",
            )
        )
    for name, attribute_schema in schema_element.get("attributes", {}).items():
        if attribute_schema.get("required") and name not in attributes:
            issues.append(
                ValidationIssue(
                    path=f"{path}.@{name}",
                    message=f"Required XML attribute '{name}' is missing.",
                    validator="xsd_required_attribute",
                )
            )
            continue
        if name in attributes and not _matches_scalar_type(attributes[name], attribute_schema.get("type")):
            issues.append(
                ValidationIssue(
                    path=f"{path}.@{name}",
                    message=f"XML attribute '{name}' does not match type {attribute_schema.get('type')}.",
                    validator="xsd_attribute_type",
                )
            )

    child_documents = document.get("children", [])
    if not isinstance(child_documents, list):
        issues.append(ValidationIssue(path=f"{path}.children", message="XML children must be a list.", validator="xml_structure"))
        return issues
    if schema_element.get("type") == "complex" and document.get("text") is not None:
        issues.append(
            ValidationIssue(
                path=path,
                message=f"Complex XML element '{schema_element['name']}' must not contain direct text content.",
                validator="xsd_mixed_content",
            )
        )

    expected_children = schema_element.get("children", [])
    cursor = 0
    for child_schema in expected_children:
        matched = 0
        max_occurs = child_schema.get("max_occurs", 1)
        while cursor < len(child_documents) and child_documents[cursor].get("tag") == child_schema["name"]:
            issues.extend(_validate_child_node(child_documents[cursor], child_schema, f"{path}.{child_schema['name']}[{matched}]"))
            matched += 1
            cursor += 1
            if max_occurs != "unbounded" and matched >= max_occurs:
                break
        if matched < child_schema.get("min_occurs", 1):
            issues.append(
                ValidationIssue(
                    path=f"{path}.{child_schema['name']}",
                    message=f"XML element '{child_schema['name']}' occurs {matched} times but at least {child_schema.get('min_occurs', 1)} required.",
                    validator="xsd_min_occurs",
                )
            )
    if cursor < len(child_documents):
        unexpected = child_documents[cursor]
        issues.append(
            ValidationIssue(
                path=f"{path}.{unexpected.get('tag')}",
                message=f"Unexpected XML element '{unexpected.get('tag')}' for the current XSD sequence.",
                validator="xsd_unexpected_element",
            )
        )
    return issues


def _validate_child_node(document: dict[str, Any], schema_element: dict[str, Any], path: str) -> list[ValidationIssue]:
    if schema_element.get("type") == "complex":
        return _validate_against_normalized_xsd(document, schema_element, path)
    text = document.get("text")
    if text is None:
        return [
            ValidationIssue(
                path=path,
                message=f"Scalar XML element '{schema_element['name']}' must contain text.",
                validator="xsd_missing_text",
            )
        ]
    if not _matches_scalar_type(text, schema_element.get("type")):
        return [
            ValidationIssue(
                path=path,
                message=f"XML element '{schema_element['name']}' does not match type {schema_element.get('type')}.",
                validator="xsd_element_type",
            )
        ]
    if document.get("children"):
        return [
            ValidationIssue(
                path=path,
                message=f"Scalar XML element '{schema_element['name']}' must not contain child elements.",
                validator="xsd_scalar_children",
            )
        ]
    return []


def _matches_scalar_type(value: Any, expected_type: str | None) -> bool:
    if expected_type in {None, "string"}:
        return isinstance(value, str)
    if not isinstance(value, str):
        return False
    if expected_type == "integer":
        if value.startswith("-"):
            return value[1:].isdigit()
        return value.isdigit()
    if expected_type == "number":
        try:
            float(value)
        except (TypeError, ValueError):
            return False
        return True
    if expected_type == "boolean":
        return value in {"true", "false"}
    return False

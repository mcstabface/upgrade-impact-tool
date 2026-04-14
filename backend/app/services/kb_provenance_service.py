class KBProvenanceValidationError(Exception):
    pass


class KBProvenanceService:
    def validate_change_record_provenance(self, record: dict) -> None:
        required_fields = [
            "kb_article_number",
            "kb_title",
            "kb_url",
        ]

        missing = [field for field in required_fields if not record.get(field)]
        if missing:
            raise KBProvenanceValidationError(
                f"Change record missing required KB provenance fields: {', '.join(missing)}"
            )
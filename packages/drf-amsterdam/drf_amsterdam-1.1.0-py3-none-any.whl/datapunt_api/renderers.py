from typing import Any, Mapping

from rest_framework_csv.renderers import CSVRenderer


class PaginatedCSVRenderer(CSVRenderer):
    results_field: str = 'results'

    def render(
            self,
            data: Any,
            media_type: str | None = None,
            renderer_context: Mapping[str, Any] | None = {},
            writer_opts: Mapping[str, Any] | None = None,
    ) -> Any:
        if not isinstance(data, list):
            data = data.get(self.results_field, [])

        return super(PaginatedCSVRenderer, self).render(data, media_type, renderer_context, writer_opts)

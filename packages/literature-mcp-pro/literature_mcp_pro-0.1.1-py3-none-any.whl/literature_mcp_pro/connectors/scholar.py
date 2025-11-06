"""Google Scholar connector (disabled).

Provides a class with the expected interface that raises NotImplementedError.
This keeps imports working while documenting the disabled state.
"""


class ScholarService:
    @staticmethod
    async def search(*args, **kwargs):
        raise NotImplementedError("ScholarService is disabled in this MCP build")

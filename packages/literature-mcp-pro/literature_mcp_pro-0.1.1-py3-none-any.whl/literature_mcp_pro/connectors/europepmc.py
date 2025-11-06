"""Europe PMC connector (disabled).

Provides a class with the expected interface that raises NotImplementedError.
This keeps imports working while documenting the disabled state.
"""


class EuropePMCService:
    @staticmethod
    async def search(*args, **kwargs):
        raise NotImplementedError("EuropePMCService is disabled in this MCP build")

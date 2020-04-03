from starlette.graphql import GraphQLApp
from starlette.requests import Request
from starlette.types import Receive, Scope, Send


class LessCrappyGQLApp(GraphQLApp):
    """App that injects our custom directive middleware when calling `schema.execute`."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_cookies = {}

    async def execute(self,
                      query,
                      variables=None,
                      context=None,
                      operation_name=None):
        if self.is_async:
            resp = await self.schema.execute(
                query,
                variables=variables,
                operation_name=operation_name,
                executor=self.executor,
                return_promise=True,
                context=context,
            )
            self.custom_cookies = context.get("cookies", {})
            return resp
        else:
            raise NotImplementedError("Synchronous execution is not supported.")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.executor is None and self.executor_class is not None:
            self.executor = self.executor_class()

        request = Request(scope, receive=receive)
        response = await self.handle_graphql(request)
        for k,v in self.custom_cookies.items():            
            response.set_cookie(k, v, httponly=True)
        await response(scope, receive, send)

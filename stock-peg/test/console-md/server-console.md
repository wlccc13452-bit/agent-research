INFO:     127.0.0.1:14900 - "GET /api/stocks/indices/quotes HTTP/1.1" 200 OK
19:41:44 - ERROR - 发送消息失败:
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\uvicorn\protocols\websockets\websockets_impl.py", line 244, in run_asgi
    result = await self.app(self.scope, self.asgi_receive, self.asgi_send)  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\uvicorn\middleware\proxy_headers.py", line 60, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\applications.py", line 1160, in __call__
    await super().__call__(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\applications.py", line 107, in __call__
    await self.middleware_stack(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\middleware\errors.py", line 151, in __call__
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\middleware\base.py", line 103, in __call__
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\middleware\cors.py", line 79, in __call__
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\middleware\exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\routing.py", line 716, in __call__
    await self.middleware_stack(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\routing.py", line 736, in app
    await route.handle(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\routing.py", line 364, in handle
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\routing.py", line 156, in app
    await wrap_app_handling_exceptions(app, session)(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\routing.py", line 153, in app
    await func(session)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\routing.py", line 760, in app
    await dependant.call(**solved_result.values)
  File "D:\play-ground\股票研究\stock-peg\backend\routers\websocket.py", line 22, in websocket_endpoint
    data = await websocket.receive_text()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\websockets.py", line 118, in receive_text
    raise RuntimeError('WebSocket is not connected. Need to call "accept" first.')
RuntimeError: WebSocket is not connected. Need to call "accept" first.
INFO:     connection closed
19:41:44 - ERROR - 发送消息失败:
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\uvicorn\protocols\websockets\websockets_impl.py", line 244, in run_asgi
    result = await self.app(self.scope, self.asgi_receive, self.asgi_send)  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\uvicorn\middleware\proxy_headers.py", line 60, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\applications.py", line 1160, in __call__
    await super().__call__(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\applications.py", line 107, in __call__
    await self.middleware_stack(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\middleware\errors.py", line 151, in __call__
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\middleware\base.py", line 103, in __call__
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\middleware\cors.py", line 79, in __call__
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\middleware\exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\routing.py", line 716, in __call__
    await self.middleware_stack(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\routing.py", line 736, in app
    await route.handle(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\routing.py", line 364, in handle
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\routing.py", line 156, in app
    await wrap_app_handling_exceptions(app, session)(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\routing.py", line 153, in app
    await func(session)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\routing.py", line 760, in app
    await dependant.call(**solved_result.values)
  File "D:\play-ground\股票研究\stock-peg\backend\routers\websocket.py", line 22, in websocket_endpoint
    data = await websocket.receive_text()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\websockets.py", line 118, in receive_text
    raise RuntimeError('WebSocket is not connected. Need to call "accept" first.')
RuntimeError: WebSocket is not connected. Need to call "accept" first.
INFO:     connection closed
19:41:44 - ERROR - 发送消息失败:
ERROR:    Exception in ASGI application
Traceback (most recent call last):
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\uvicorn\protocols\websockets\websockets_impl.py", line 244, in run_asgi
    result = await self.app(self.scope, self.asgi_receive, self.asgi_send)  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\uvicorn\middleware\proxy_headers.py", line 60, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\applications.py", line 1160, in __call__
    await super().__call__(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\applications.py", line 107, in __call__
    await self.middleware_stack(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\middleware\errors.py", line 151, in __call__
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\middleware\base.py", line 103, in __call__
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\middleware\cors.py", line 79, in __call__
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\middleware\exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\middleware\asyncexitstack.py", line 18, in __call__
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\routing.py", line 716, in __call__
    await self.middleware_stack(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\routing.py", line 736, in app
    await route.handle(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\routing.py", line 364, in handle
    await self.app(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\routing.py", line 156, in app
    await wrap_app_handling_exceptions(app, session)(scope, receive, send)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\routing.py", line 153, in app
    await func(session)
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\fastapi\routing.py", line 760, in app
    await dependant.call(**solved_result.values)
  File "D:\play-ground\股票研究\stock-peg\backend\routers\websocket.py", line 22, in websocket_endpoint
    data = await websocket.receive_text()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "D:\play-ground\股票研究\stock-peg\backend\.venv\Lib\site-packages\starlette\websockets.py", line 118, in receive_text
    raise RuntimeError('WebSocket is not connected. Need to call "accept" first.')
RuntimeError: WebSocket is not connected. Need to call "accept" first.

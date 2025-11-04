from .simple_function import say_hello
from .web import (
    jg_answer_back,
    jg_handle_error,
    jg_load_html,
    jg_render_html,
    jg_get,
    jg_post,
    jg_web_app,
    jg_start_server,
    jg_create_app
)

__all__ = [
    "say_hello",
    "jg_answer_back",
    "jg_handle_error",
    "jg_load_html",
    "jg_render_html",
    "jg_get",
    "jg_post",
    "jg_web_app",
    "jg_start_server",
    "jg_create_app"
]

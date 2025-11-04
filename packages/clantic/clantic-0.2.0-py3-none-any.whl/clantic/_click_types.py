from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict

from typing_extensions import NotRequired

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from click import Argument, Context, types
    from click.shell_completion import CompletionItem


class ClickParameterFields(TypedDict):
    param_decls: NotRequired[Sequence[str] | None]
    type: NotRequired[types.ParamType | Any | None]
    multiple: NotRequired[bool]
    default: NotRequired[Any | Callable[[], Any] | None]
    callback: NotRequired[Callable[[Context, Argument, Any], Any] | None]
    nargs: NotRequired[int | None]
    metavar: NotRequired[str | None]
    expose_value: NotRequired[bool]
    is_eager: NotRequired[bool]
    envvar: NotRequired[str | Sequence[str] | None]
    shell_complete: NotRequired[
        Callable[[Context, Argument, str], list[CompletionItem] | list[str]] | None
    ]


class ClickArgumentFields(ClickParameterFields):
    pass


class ClickOptionFields(ClickParameterFields):
    show_default: NotRequired[bool | str | None]
    prompt: NotRequired[bool | str]
    confirmation_prompt: NotRequired[bool | str]
    prompt_required: NotRequired[bool]
    hide_input: NotRequired[bool]
    is_flag: NotRequired[bool | None]
    flag_value: NotRequired[Any | None]
    count: NotRequired[bool]
    allow_from_autoenv: NotRequired[bool]
    help: NotRequired[str | None]
    hidden: NotRequired[bool]
    show_choices: NotRequired[bool]
    show_envvar: NotRequired[bool]

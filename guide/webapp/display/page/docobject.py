from __future__ import annotations

import importlib
import inspect
import pkgutil

from collections import defaultdict
from dataclasses import dataclass, field
from html import escape

from docstring_parser import Docstring, DocstringParam, DocstringRaises
from docstring_parser import parse as parse_docstring
from docstring_parser.common import DocstringExample
from html5tagger import HTML, Builder, E  # type: ignore

from ..markdown import render_markdown, slugify


@dataclass
class DocObject:
    name: str
    module_name: str
    full_name: str
    signature: inspect.Signature | None
    docstring: Docstring
    object_type: str = ""
    methods: list[DocObject] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)


def _extract_classes_methods(obj, full_name, docstrings):
    methods = []
    for method_name, method in inspect.getmembers(obj, _is_public_member):
        try:
            signature = _get_method_signature(method)
            docstring = inspect.getdoc(method)
            decorators = _detect_decorators(obj, method)
            methods.append(
                DocObject(
                    name=method_name,
                    module_name="",
                    full_name=f"{full_name}.{method_name}",
                    signature=signature,
                    docstring=parse_docstring(docstring or ""),
                    decorators=decorators,
                    object_type=_get_object_type(method),
                )
            )
        except ValueError:
            pass

    docstrings[full_name].methods = methods


def _get_method_signature(method):
    try:
        return inspect.signature(method)
    except TypeError:
        signature = None
        if func := getattr(method, "fget", None):
            signature = inspect.signature(func)
    return signature


def _is_public_member(obj: object) -> bool:
    obj_name = getattr(obj, "__name__", "")
    if func := getattr(obj, "fget", None):
        obj_name = getattr(func, "__name__", "")
    return (
        not obj_name.startswith("_")
        and not obj_name.isupper()
        and (
            inspect.ismethod(obj)
            or inspect.isfunction(obj)
            or isinstance(obj, property)
            or isinstance(obj, property)
        )
    )


def _detect_decorators(cls, method):
    decorators = []
    method_name = getattr(method, "__name__", None)
    if isinstance(cls.__dict__.get(method_name), classmethod):
        decorators.append("classmethod")
    if isinstance(cls.__dict__.get(method_name), staticmethod):
        decorators.append("staticmethod")
    if isinstance(method, property):
        decorators.append("property")
    return decorators


def _get_object_type(obj) -> str:
    if inspect.isclass(obj):
        return "class"

    # If the object is a method, get the underlying function
    if inspect.ismethod(obj):
        obj = obj.__func__

    # If the object is a coroutine or a coroutine function
    if inspect.iscoroutine(obj) or inspect.iscoroutinefunction(obj):
        return "async def"

    return "def"


def organize_docobjects(package_name: str) -> dict[str, str]:
    page_content: defaultdict[str, str] = defaultdict(str)
    docobjects = _extract_docobjects(package_name)
    page_registry: defaultdict[str, list[str]] = defaultdict(list)
    for module, docobject in docobjects.items():
        builder = Builder(name="Partial")
        _docobject_to_html(docobject, builder)
        ref = module.rsplit(".", module.count(".") - 1)[0]
        page_registry[ref].append(module)
        page_content[f"/api/{ref}.md"] += str(builder)
    for ref, objects in page_registry.items():
        page_content[f"/api/{ref}.md"] = (
            _table_of_contents(objects) + page_content[f"/api/{ref}.md"]
        )
    return page_content


def _table_of_contents(objects: list[str]) -> str:
    builder = Builder(name="Partial")
    with builder.div(class_="table-of-contents"):
        builder.h3("Table of Contents", class_="is-size-4")
        for obj in objects:
            module, name = obj.rsplit(".", 1)
            builder.a(
                E.strong(name),
                E.small(module),
                href=f"#{slugify(obj.replace('.', '-'))}",
                class_="table-of-contents-item",
            )
    return str(builder)


def _extract_docobjects(package_name: str) -> dict[str, DocObject]:
    docstrings = {}
    package = importlib.import_module(package_name)

    for _, name, _ in pkgutil.walk_packages(
        package.__path__, package_name + "."
    ):
        module = importlib.import_module(name)
        for obj_name, obj in inspect.getmembers(module):
            if (
                obj_name.startswith("_")
                or inspect.getmodule(obj) != module
                or not callable(obj)
            ):
                continue
            try:
                signature = inspect.signature(obj)
            except ValueError:
                signature = None
            docstring = inspect.getdoc(obj)
            full_name = f"{name}.{obj_name}"
            docstrings[full_name] = DocObject(
                name=obj_name,
                full_name=full_name,
                module_name=name,
                signature=signature,
                docstring=parse_docstring(docstring or ""),
                object_type=_get_object_type(obj),
            )
            if inspect.isclass(obj):
                _extract_classes_methods(obj, full_name, docstrings)

    return docstrings


def _docobject_to_html(
    docobject: DocObject, builder: Builder, as_method: bool = False
) -> None:
    anchor_id = slugify(docobject.full_name.replace(".", "-"))
    anchor = E.a("#", class_="anchor", href=f"#{anchor_id}")
    class_name, heading = _define_heading_and_class(
        docobject, anchor, as_method
    )

    with builder.div(class_=class_name):
        builder(heading)

        if docobject.docstring.short_description:
            builder.div(
                HTML(render_markdown(docobject.docstring.short_description)),
                class_="short-description mt-3 is-size-5",
            )

        if docobject.object_type == "class":
            mro = [
                item
                for idx, item in enumerate(
                    inspect.getmro(
                        getattr(
                            importlib.import_module(docobject.module_name),
                            docobject.name,
                        )
                    )
                )
                if idx > 0 and item not in (object, type)
            ]
            if mro:
                builder.div(
                    E.span("Inherits from: ", class_="is-italic"),
                    E.span(
                        ", ".join([cls.__name__ for cls in mro]),
                        class_="has-text-weight-bold",
                    ),
                    class_="short-description mt-3 is-size-5",
                )

        builder.p(
            HTML(
                _signature_to_html(
                    docobject.name,
                    docobject.object_type,
                    docobject.signature,
                    docobject.decorators,
                )
            ),
            class_="signature notification is-family-monospace",
        )

        if docobject.docstring.long_description:
            builder.div(
                HTML(render_markdown(docobject.docstring.long_description)),
                class_="long-description mt-3",
            )

        if docobject.docstring.params:
            with builder.div(class_="box mt-5"):
                builder.h5(
                    "Parameters", class_="is-size-5 has-text-weight-bold"
                )
                _render_params(builder, docobject.docstring.params)

        if docobject.docstring.returns:
            _render_returns(builder, docobject)

        if docobject.docstring.raises:
            _render_raises(builder, docobject.docstring.raises)

        if docobject.docstring.examples:
            _render_examples(builder, docobject.docstring.examples)

        for method in docobject.methods:
            _docobject_to_html(method, builder, as_method=True)


def _signature_to_html(
    name: str,
    object_type: str,
    signature: inspect.Signature | None,
    decorators: list[str],
) -> str:
    parts = []
    parts.append("<span class='function-signature'>")
    for decorator in decorators:
        parts.append(
            f"<span class='function-decorator'>@{decorator}</span><br>"
        )
    parts.append(
        f"<span class='is-italic'>{object_type}</span> "
        f"<span class='has-text-weight-bold'>{name}</span>("
    )
    if not signature:
        parts.append("<span class='param-name'>self</span>)")
        parts.append("</span>")
        return "".join(parts)
    for i, param in enumerate(signature.parameters.values()):
        parts.append(f"<span class='param-name'>{escape(param.name)}</span>")
        annotation = ""
        if param.annotation != inspect.Parameter.empty:
            annotation = escape(str(param.annotation))
            parts.append(
                f": <span class='param-annotation'>{annotation}</span>"
            )
        if param.default != inspect.Parameter.empty:
            default = escape(str(param.default))
            if annotation == "str":
                default = f'"{default}"'
            parts.append(f" = <span class='param-default'>{default}</span>")
        if i < len(signature.parameters) - 1:
            parts.append(", ")
    parts.append(")")
    if signature.return_annotation != inspect.Signature.empty:
        return_annotation = escape(str(signature.return_annotation))
        parts.append(
            f": -> <span class='return-annotation'>{return_annotation}</span>"
        )
    parts.append("</span>")
    return "".join(parts)


def _define_heading_and_class(
    docobject: DocObject, anchor: Builder, as_method: bool
) -> tuple[str, Builder]:
    anchor_id = slugify(docobject.full_name.replace(".", "-"))
    anchor = E.a("#", class_="anchor", href=f"#{anchor_id}")
    if as_method:
        class_name = "method"
        heading = E.h3(
            docobject.name,
            anchor,
            class_="is-size-4 has-text-weight-bold mt-6",
            id_=anchor_id,
        )
    else:
        class_name = "docobject"
        heading = E.h2(
            E.span(docobject.module_name, class_="has-text-weight-light"),
            ".",
            E.span(docobject.name, class_="has-text-weight-bold is-size-1"),
            anchor,
            class_="is-size-2",
            id_=anchor_id,
        )
    return class_name, heading


def _render_params(builder: Builder, params: list[DocstringParam]) -> None:
    for param in params:
        with builder.dl(class_="mt-2"):
            dt_args = [param.arg_name]
            if param.type_name:
                parts = [
                    E.br(),
                    E.span(
                        param.type_name,
                        class_=(
                            "has-text-weight-normal has-text-purple "
                            "is-size-7 ml-2"
                        ),
                    ),
                ]
                dt_args.extend(parts)
            builder.dt(*dt_args, class_="is-family-monospace")
            builder.dd(
                HTML(
                    render_markdown(
                        param.description
                        or param.arg_name
                        or param.type_name
                        or ""
                    )
                )
            )


def _render_raises(builder: Builder, raises: list[DocstringRaises]) -> None:
    with builder.div(class_="box mt-5"):
        builder.h5("Raises", class_="is-size-5 has-text-weight-bold")
        for raise_ in raises:
            with builder.dl(class_="mt-2"):
                builder.dt(raise_.type_name, class_="is-family-monospace")
                builder.dd(
                    HTML(
                        render_markdown(
                            raise_.description or raise_.type_name or ""
                        )
                    )
                )


def _render_returns(builder: Builder, docobject: DocObject) -> None:
    assert docobject.docstring.returns
    return_type = docobject.docstring.returns.type_name
    if not return_type or return_type == "None":
        return
    with builder.div(class_="box mt-5"):
        if not return_type and docobject.signature:
            return_type = docobject.signature.return_annotation

        if not return_type or return_type == inspect.Signature.empty:
            return_type = "N/A"

        term = (
            "Return"
            if not docobject.docstring.returns.is_generator
            else "Yields"
        )
        builder.h5(term, class_="is-size-5 has-text-weight-bold")
        with builder.dl(class_="mt-2"):
            builder.dt(return_type, class_="is-family-monospace")
            builder.dd(
                HTML(
                    render_markdown(
                        docobject.docstring.returns.description
                        or docobject.docstring.returns.type_name
                        or ""
                    )
                )
            )


def _render_examples(
    builder: Builder, examples: list[DocstringExample]
) -> None:
    with builder.div(class_="box mt-5"):
        builder.h5("Examples", class_="is-size-5 has-text-weight-bold")
        for example in examples:
            with builder.div(class_="mt-2"):
                builder(
                    HTML(
                        render_markdown(
                            example.description or example.snippet or ""
                        )
                    )
                )

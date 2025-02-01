---
hide:
  - navigation
---


# DocStrands

When documenting your functions, you might find yourself documenting the
same parameters over and over again. DocStrands provides a framework for
re-using docstring information.

## Example

Imagine you’re writing an HTTP library. You start with a `get` function,
but add the `@docstring` decorator to tell DocStrands that it function
uses Google-style docstrings.

``` python
from docstrands import docstring

@docstring("google")
def get(url: str, headers: dict[str, str], params: dict[str, str]) -> str:
    """
    Makes an HTTP GET request

    Params:
        url: Path to the resource to request
        headers: Dictionary of HTTP headers. Keys will be automatically capitalised.
        params: Dictionary of query parameters which will be URL encoded.

    Returns:
        The raw HTTP response body as a string.
    """
```

Next, you want to write a corresponding `post` function. The annoying
thing is that many of these parameters are exactly the same as on our
`get` function. Here DocStrands solves this by copying the repeated
documentation using `@get.copy_*` functions:

``` python
@get.copy_params("url", "headers")
@get.copy_returns()
@docstring("google")
def post(url: str, headers: dict[str, str], body: bytes) -> str:
    """
    Makes an HTTP POST request.

    Params:
        body: POST body. Text such as JSON will have to be encoded beforehand.
    """
```

Finally, you can call `help` to prove this worked correctly:

``` python
help(post)
```

    Help on ParsedFunc in module docstrands.parsed_func:

    <function post>
        Makes an HTTP POST request.

        Args:
            body: POST body. Text such as JSON will have to be encoded beforehand.
            url: Path to the resource to request
            headers: Dictionary of HTTP headers. Keys will be automatically capitalised.

        Returns:
            : The raw HTTP response body as a string.

## Type Annotations

DocStrands supports another approach to re-using documentation:
attaching it to types. The above example represents a common case where
both functions shared the same return documentation and return type, so
we can encode this using Python’s type system:

``` python
from typing import Annotated
from docstrands import Description

HttpResponse = Annotated[str, Description("The raw HTTP response body as a string.")]
Url = Annotated[str, Description("Path to the resource to request")]
Headers = Annotated[dict[str, str], Description("Dictionary of HTTP headers. Keys will be automatically capitalised.")]
Params = Annotated[dict[str, str], Description("Dictionary of query parameters which will be URL encoded.")]
```

Then apply them to our new function. Note that we still need to define
the function description, and we still need to use the `@docstring`
decorator:

``` python
@docstring("google")
def get(url: Url, headers: Headers, params: Params) -> HttpResponse:
    """
    Makes an HTTP POST request.
    """

help(get)
```

    Help on ParsedFunc in module docstrands.parsed_func:

    <function get>
        Makes an HTTP POST request.

        Args:
            url: Path to the resource to request
            headers: Dictionary of HTTP headers. Keys will be automatically capitalised.
            params: Dictionary of query parameters which will be URL encoded.

        Returns:
            : The raw HTTP response body as a string.

Of course, we can then re-use these parameters with `post`:

``` python
Body = Annotated[bytes, Description("POST body. Text such as JSON will have to be encoded beforehand.")]

@docstring("google")
def post(url: Url, headers: Headers, body: Body) -> HttpResponse:
    """
    Makes an HTTP POST request.
    """

help(post)
```

    Help on ParsedFunc in module docstrands.parsed_func:

    <function post>
        Makes an HTTP POST request.

        Args:
            url: Path to the resource to request
            headers: Dictionary of HTTP headers. Keys will be automatically capitalised.
            body: POST body. Text such as JSON will have to be encoded beforehand.

        Returns:
            : The raw HTTP response body as a string.

You can even re-use the same types as parameters and return values:

``` python
@docstring("google")
def make_accept_headers() -> Headers:
    """
    Calculates the the `Accept`, `Accept-Encoding` and `Accept-Language` headers based on the capacity of the HTTP client
    """

help(make_accept_headers)
```

    Help on ParsedFunc in module docstrands.parsed_func:

    <function make_accept_headers>
        Calculates the the `Accept`, `Accept-Encoding` and `Accept-Language` headers based on the capacity of the HTTP client

        Returns:
            : Dictionary of HTTP headers. Keys will be automatically capitalised.

## Alternatives

There are other solutions to this problem.

We could choose to not use DocStrands at all, but then `post` would have
an incomplete docstring:

We could also copy the entire docstring from `Weapon` and add it to
`Wand` with the extra `element` parameter, but then we would have to
keep both docstrings in sync.

Finally, it is possible to link between docstrings using cross
references (e.g. in
[Sphinx](https://www.sphinx-doc.org/en/master/usage/referencing.html) or
[`mkdocstrings`](https://mkdocstrings.github.io/usage/#cross-references)).
Firstly, this only shows up in your final HTML documentation: standard
Python functions like `help()` don’t understand this. Secondly, it can
be frustrating to read documentation that sends you to several other
pages just to understand one function. In contrast, DocStrands keeps
everything all in one place.

# little-a2s

[![](https://img.shields.io/pypi/v/little-a2s?style=flat-square&logo=pypi)](https://pypi.org/project/little-a2s/)
[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/little-a2s/publish.yml?style=flat-square&logo=uv&label=build)](https://docs.astral.sh/uv/)
[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/little-a2s/pytest.yml?style=flat-square&logo=pytest&label=tests)](https://docs.pytest.org/)
[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/little-a2s/pyright-lint.yml?style=flat-square&label=pyright)](https://microsoft.github.io/pyright/#/)
[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/little-a2s/ruff-check.yml?style=flat-square&logo=ruff&label=lints)](https://docs.astral.sh/ruff/)
[![](https://img.shields.io/github/actions/workflow/status/thegamecracks/little-a2s/ruff-format.yml?style=flat-square&logo=ruff&label=style)](https://docs.astral.sh/ruff/)

A synchronous and sans-I/O library implementing the A2S Valve Source Query protocol.

```py
from little_a2s import A2S

with A2S.from_addr("example.com", 27015, timeout=1) as a2s:
    print(a2s.info())
    print(a2s.players())
    print(a2s.rules())
```

## Installation

This project requires Python 3.11 or newer.

```sh
$ python3 -m venv
$ .venv/bin/activate
(.venv) $ pip install little-a2s
```

## Usage

For now, see the [examples] directory for basic usage or the [documentation]
for a complete API reference.

[examples]: https://github.com/thegamecracks/little-a2s/tree/main/examples
[documentation]: https://little-a2s.rtfd.io/

## License

This project is written under the [MIT License].

[MIT License]: /LICENSE

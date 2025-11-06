# AI4CE Helpers
A set of tools to help interact with the AI4CE backend.

For mor information, please refer to the [AI4CE Project](https://gitlab.com/ai4ce/public-info).

# How to Publush
``` bash
poetry config pypi-token.pypi <your-api-token>

poetry version minor
# or
poetry version patch

poetry publish --build
```
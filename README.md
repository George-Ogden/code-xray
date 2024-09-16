# Code X-Ray
Have you noticed that your code is opaque.
There's so much happening between the lines that you can't even see.
Well, now you can:

![binary search Code X-Ray example](https://github.com/George-Ogden/code-xray-samples/blob/master/images/binary-search-annotations.png)
## Install
0. Make sure you have Python>=3.11 and Visual Studio Code Insiders installed.
1. Download the latest `.vsix` from the [Releases](https://github.com/George-Ogden/code-xray/releases) page or [Open VSX Registry](https://open-vsx.org/extension/George-Ogden/xray).
1. **Install from VSIX...** (see the [official page](https://code.visualstudio.com/api/advanced-topics/using-proposed-api#sharing-extensions-using-the-proposed-api) for more info).
1. Launch code with the proposed API: `code-insiders . --enable-proposed-api=George-Ogden.xray` (see the [official page](https://code.visualstudio.com/api/advanced-topics/using-proposed-api#sharing-extensions-using-the-proposed-api) for more info).

## Usage
1. Write your tests in the same workspace.
1. **Python: Select Interpreter** to choose the environment with your packages installed.
1. Click `Run Code X-Ray` or type `Ctrl+Enter` in the function definition.
1. Select the test to run.

![binary search selection example](https://github.com/George-Ogden/code-xray-samples/blob/master/images/binary-search-select.png)
### Advanced Usage
- Hover over the annotations for more info.
- Use `Ctrl+Del` to remove annotations.

![json annotations hover example](https://github.com/George-Ogden/code-xray-samples/blob/master/images/json-annotations-hover.png)
- Run on your tests as well as your code.

![json annotations test example](https://github.com/George-Ogden/code-xray-samples/blob/master/images/json-test-annotations.png)
## Examples
Head over to https://github.com/George-Ogden/code-xray-samples to see more examples and screenshots.
## Issues and Limitations
The annotations are only as good as the debugger makes them.
To get the most out of this project:
- write clean code
- use temporary variables
- define `__repr__` on your classes

Currently, Python is the only language supported.
If there's enough demand, I might add other languages.

This code is designed to help you write fewer bugs.
But it is almost certainly not bug-free itself.
Please, use the issue tracker to report issues.
## Inspiration
This project was inspired by Bret Victor's talk "Inventing on Principle".
That's why I've used the binary search example:
![binary search Code X-Ray example](https://github.com/George-Ogden/code-xray-samples/blob/master/images/binary-search-missing-annotations.png)

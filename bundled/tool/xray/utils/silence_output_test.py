import pytest

from . import silence_output  # Replace 'your_module' with the name of your module file


def test_silence_output(capsys: pytest.CaptureFixture[str]):
    @silence_output
    def noisy_function():
        print("This should not appear in stdout")
        return "Noisy function executed"

    result = noisy_function()

    assert capsys.readouterr().out == ""
    assert result == "Noisy function executed"


if __name__ == "__main__":
    pytest.main()

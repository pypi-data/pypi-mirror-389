[String] $VEnvPythonPath = [IO.Path]::Combine([IO.Path]::GetDirectoryName($PSCommandPath), ".venv", "Scripts/python.exe")
& $VEnvPythonPath -m pip install --upgrade build
& $VEnvPythonPath -m pip install --upgrade pkginfo
& $VEnvPythonPath -m pip install --upgrade twine
& $VEnvPythonPath -m pip install --upgrade hatchling
& $VEnvPythonPath -m build
& $VEnvPythonPath -m twine upload --skip-existing --repository pypi dist/*

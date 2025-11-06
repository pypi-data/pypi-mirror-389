### AVxcelerate API

The AVxcelerate API provides auto-generated gRPC Python interface files for [Ansys AVxcelerate](https://developer.ansys.com/docs/avxcelerate).

#### Install the package

If wheels for the AVxcelerate API are published to the public PyPI, install the latest package with this command:

```
pip install ansys-api-avxcelerate
```

#### Build the package

Build the package by running these commands:

```
pip install build
python -m build
```

These commands create both the source distribution, which contains only the PROTO files, and the wheel, which includes the PROTO files and builds the Python interface files.

The interface files are identical regardless of the Python version used to generate them. However, the last pre-built wheel for ``grpcio~=1.17`` was Python 3.7. To improve build time, use Python 3.7 when building the wheel.

#### Deploy manually

After building the packages, deploy them manually with these commands:

```
pip install twine
twine upload dist/*
```

**Note:** CI/CD automatically handles this process.

#### Deploy automatically

This repository includes GitHub CI/CD workflows that automatically build source and wheel packages for these API files. By default, these workflows run on pull requests, the main branch, and tags when pushed. Artifacts are uploaded for each pull request.

To release wheels publicly to PyPI, ensure your branch is up to date and push tags. For example, use the following commands to push the ``v0.1.0`` tag:

```bash
git tag v0.1.0
git push --tags
```

#### Report issues

Use the AVxcelerate API [Issues](https://github.com/ansys/ansys-api-avxcelerate/issues) page to report bugs and request new features. Visit the [Discussions](https://discuss.ansys.com/) page on the Ansys Developer portal to post questions, share ideas, and get community feedback.

For general questions about the PyAnsys ecosystem that are not specific to the AVxcelerate API, contact the [PyAnsys Core team](mailto:pyansys.core@ansys.com).

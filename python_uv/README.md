# FastAPI Python Terraform Challenges

This project is a Python 3.12 workspace managed with `uv`.

It contains standalone Python practice scripts and is also ready to grow into a
FastAPI backend.

## Requirements

- Python 3.12
- `uv`

The project pins Python with `.python-version`:

```txt
3.12
```

Install/sync the local environment:

```bash
uv sync
```

Check the Python version used by `uv`:

```bash
uv run python --version
```


## Dependency Notes
Install FastAPI + Cloud dependencies (for production, and development respectively)
```bash
uv add requests
uv add boto3
uv add fastapi
uv add --dev "fastapi[standard]"
```

Runtime dependencies are in `[project.dependencies]`.

Development-only dependencies are in `[dependency-groups].dev`.


## Run The FastAPI App Locally

The project already includes a minimal FastAPI app in `main.py`.

Start the development server:

```bash
uv run fastapi dev
```

Then open:

```txt
http://127.0.0.1:8000
```

API docs are available at:

```txt
http://127.0.0.1:8000/docs
```

If automatic discovery ever fails, run it explicitly:

```bash
uv run fastapi dev index.py
```



# Python Part for Deploying a zip archive in AWS Lambda:
In the python module we generate the zip file for AWS Lambda that includes the needed pip packages and the latest python code.

For Zip file Lambda version:
first, install dependencies from requirements.txt inside your venv.
And Later, package all the dependencies and zip it:

```
cd python_uv

uv export --frozen --no-dev --no-editable -o requirements.txt

uv pip install \
   --no-installer-metadata \
   --no-compile-bytecode \
   --python-platform x86_64-manylinux2014 \
   --python 3.12 \
   --target package_to_zip \
   -r requirements.txt

cp index.py package_to_zip/
cd package_to_zip

zip -r ../../terraform/lambda.zip . \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*.pyo" \
  -x "*.dist-info/RECORD" \
  -x "*.dist-info/WHEEL"

cd ..
```


After that, the zip file is located inside the `Terraform folder`!
# TVM Unity Documentation

The documentation was built upon [Sphinx](https://www.sphinx-doc.org/en/master/).

## Dependencies

Run the following command in this directory to install dependencies first:

```bash
pip3 install -r requirements.txt
```

## Build the Documentation

Then you can build the documentation by running:

```bash
make html
```

## View the Documentation

Run the following command to start a simple HTTP server:

```bash
python -m http.server -d _build/html 8000
```

Then you can view the documentation in your browser at `http://localhost:8000` (the port can be customized by changing the port number).
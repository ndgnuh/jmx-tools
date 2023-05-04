from glob import glob
from os import path, walk, curdir, makedirs
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from argparse import ArgumentParser
import requests
import uvicorn

port = 30940  # totally random
endpoint = "/sync"


def find_jmx(d):
    results = []
    for root, _, files in walk(d):
        for file in files:
            if file.endswith('.jmx'):
                results.append(path.join(root, file))
    return results


def main_push(args):
    inputs = args.inputs

    #
    # collect input files
    #
    if len(inputs) == 0:
        inputs = ['.']
    input_files = []
    for file_ in inputs:
        for file in glob(file_):
            if path.isfile(file):
                input_files.append(file)
            elif path.isdir(file):
                input_files.extend(find_jmx(file))
            else:
                raise RuntimeError(f"{file} does not exists")

    #
    # Create request body
    #
    input_files = [path.relpath(file, curdir) for file in input_files]
    body = {}
    for file in input_files:
        with open(file, encoding='utf-8') as fp:
            body[file] = fp.read()

    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get(endpoint)
    def get_endpoint():
        return body

    uvicorn.run(app, host="0.0.0.0", port=port)


def main_pull(args):
    host = args.host

    res = requests.get(f"http://{host}:{port}{endpoint}")
    if res.status_code != 200:
        raise RuntimeError(f"Cannot pull from {host}")

    body = res.json()
    for file, content in body.items():
        dirname = path.dirname(file)
        if dirname != '':
            makedirs(dirname, exist_ok=True)

        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'[OK] {file}')

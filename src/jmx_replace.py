from xml.etree import cElementTree as ET
from typing import Callable, List
from dataclasses import dataclass
from abc import abstractmethod, ABCMeta, ABC
from functools import cached_property
import json
import re
import logging

from . import utils
from os import path


def parsetime(timestr):
    timestr = timestr.lower().replace(" ", "").strip()
    if timestr.isnumeric():
        return int(timestr)
    if re.match(r"^(\d+)m$", timestr):
        return int(timestr.replace("m", "")) * 60
    if re.match(r"^(\d+)s$", timestr):
        return int(timestr.replace("s", ""))
    if re.match(r"^(\d+)h$", timestr):
        return int(timestr.replace("h", "")) * 3600
    if re.match(r"^\d+:\d+", timestr):
        m, s = timestr.split(":")
        return int(m) * 60 + int(s)
    if re.match(r"\d+:^\d+:\d+", timestr):
        h, m, s = timestr.split(":")
        return int(h) * 3600 + int(m) * 60 + int(s)
    raise RuntimeError("Invalid duration format")


class Callback(ABC):
    @abstractmethod
    def condition(self, element):
        ...

    @abstractmethod
    def callback(self, element):
        ...

    def __call__(self, element):
        if self.condition(element):
            return self.callback(element)
        else:
            return element


def walk_etree(file, callbacks: List[Callback]):
    assert isinstance(callbacks, (list, tuple))
    tree = ET.parse(file)
    for element in tree.iter():
        for callback in callbacks:
            element = callback(element)
    return tree


@dataclass
class ReplaceBearer(Callback):
    bearer: str

    def condition(self, e):
        ok = e.tag == "collectionProp"
        ok = ok and e.attrib.get("name", "") == "HeaderManager.headers"
        return ok

    def callback(self, el):
        for subel in el.iter():
            if subel.attrib.get("name", "") == "Header.value":
                subel.text = f"Bearer {self.bearer}"
        return el


@dataclass
class ReplaceCCU(Callback):
    ccu: int

    def condition(self, e):
        return e.attrib.get("name", "") == "ThreadGroup.num_threads"

    def callback(self, e):
        e.text = str(self.ccu)
        return e


@dataclass
class ReplaceDuration(Callback):
    duration: str

    def __post_init__(self):
        self.duration = parsetime(self.duration)

    def condition(self, el):
        return el.attrib.get("name", "") == "ThreadGroup.duration"

    def callback(self, el):
        el.text = str(self.duration)
        return el


@dataclass
class ReplaceLoopCount(Callback):
    loops: int

    def condition(self, el):
        return el.attrib.get("name", "") == "LoopController.loops"

    def callback(self, el):
        el.text = str(self.loops)
        return el


@dataclass
class NameToPath(Callback):
    prefix_method: bool

    def condition(self, el):
        return el.attrib.get("testclass", "") == "HTTPSamplerProxy"

    def callback(self, http_sampler):
        path = None
        method = None
        for el in http_sampler:
            if el.attrib.get("name", "") == "HTTPSampler.path":
                path = el.text
            elif el.attrib.get("name", "") == "HTTPSampler.method":
                method = el.text

        if self.prefix_method:
            http_sampler.attrib["testname"] = f"{method}:{path}"
        else:
            http_sampler.attrib["testname"] = str(path)
        return http_sampler


@dataclass
class PostmanEndpointMatchCallback(Callback):
    postman_file: str

    @cached_property
    def requests(self):
        with open(self.postman_file, encoding="utf-8") as f:
            postman_config = json.load(f)

        items = utils.postman_all_items(postman_config)
        requests = []
        for item in items:
            if isinstance(item["request"]["url"], str):
                raise RuntimeError(
                    "Are you using old version of postman? Convert to 2.1 format"
                )
            request = item["request"]
            url = request["url"]
            url["endpoint"] = self.true_endpoint(url)
            requests.append(item["request"])

        return requests

    def true_endpoint(self, url):
        query = url.get("query", [])
        query_str = "&".join(f"{q['key']}={q['value']}" for q in query)

        endpoint = path.join(*url["path"])
        if len(query) > 0:
            endpoint = f"{endpoint}?{query_str}"
        endpoint = "/" + endpoint.lstrip("/")
        return endpoint

    def condition(self, el):
        return el.get("name") == "HTTPSampler.path"

    def callback(self, el):
        for request in self.requests:
            endpoint = request["url"]["endpoint"]
            if el.text in endpoint:
                logging.info(" ".join([el.text, "->", endpoint]))
                el.text = endpoint
        return el


@dataclass
class ReplaceDomain(Callback):
    domain: str

    def condition(self, el):
        return el.get("name") == "HTTPSampler.domain"

    def callback(self, el):
        el.text = self.domain
        return el


@dataclass
class ReplaceProtocol(Callback):
    protocol: str

    def condition(self, el):
        return el.get("name") == "HTTPSampler.protocol"

    def callback(self, el):
        el.text = self.protocol
        return el


@utils.with_mux
def main(args, input_file, output_file):
    callbacks = []

    #
    # Bearer replace callbacks
    #
    if args.bf is not None:
        with open(args.bf) as fp:
            bearer = fp.read()
        cb = ReplaceBearer(bearer)
        callbacks.append(cb)
    elif args.bi is not None:
        cb = ReplaceBearer(args.bi)
        callbacks.append(cb)

    #
    # CCU replace callback
    #
    if args.ccu is not None:
        cb = ReplaceCCU(args.ccu)
        callbacks.append(cb)

    #
    # Test duration
    #
    if args.duration is not None:
        cb = jr.ReplaceDuration(args.duration)
        callbacks.append(cb)

    #
    # Loop count
    #
    if args.loops is not None:
        cb = jr.ReplaceLoopCount(args.loops)
        callbacks.append(cb)

    #
    # Replace HTTP Sampler path
    #
    if args.name2path:
        cb = jr.NameToPath(args.prefix_method)
        callbacks.append(cb)

    #
    # Postman matcher
    #
    if args.postman_file:
        cb = PostmanEndpointMatchCallback(args.postman_file)
        callbacks.append(cb)

    #
    # Domain callback
    #
    if args.domain:
        cb = ReplaceDomain(args.domain)
        callbacks.append(cb)

    #
    # Protocol
    #
    if args.protocol:
        cb = ReplaceProtocol(args.protocol)
        callbacks.append(cb)


    #
    # Process and save output
    #
    xml = walk_etree(input_file, callbacks)
    utils.prepare_write(output_file)
    xml.write(output_file, encoding="utf-8")


def add_args(parser):
    # Replace options
    parser.add_argument("--bi", help="Bearer token (string)")
    parser.add_argument("--bf", help="Bearer token (from file)")
    parser.add_argument("--duration", help="Thread's life time")
    parser.add_argument("--ccu", help="CCU (replace num threads)", type=int)
    parser.add_argument("--loops", help="Loop count per threads", type=int)
    parser.add_argument("--domain", help="Request domain")
    parser.add_argument("--protocol", help="Protocol")

    parser.add_argument(
        "--name2path",
        help="Replace HTTP samplers name with their paths",
        action="store_true",
    )
    parser.add_argument(
        "--prefix-method",
        help="Prefix HTTP samplers name with method when using name2path",
        action="store_true",
    )
    parser.add_argument(
        "--output", "-o", help="output", metavar="output", required=False, default=None
    )
    parser.add_argument(
        "--match-postman",
        "--mp",
        dest="postman_file",
        help="match endpoints with postman's endpoints",
        metavar="Postman 2.1 File",
    )

    # positional
    parser.add_argument("input", help="input file or folder", metavar="input")

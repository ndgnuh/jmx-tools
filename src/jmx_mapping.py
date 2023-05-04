from xml.etree import cElementTree as ET
from dataclasses import make_dataclass


def PyJMX(name, attrs, leaf=False):
    fields = [(a, str) for a in attrs]

    if leaf:
        fields.append(('text', str))
    else:
        fields.append(('children', str))

    return make_dataclass(name, fields)


def to_xml(tag):
    e = ET.Element(None)
    e.tag = tag.__class__.__name__
    for k, v in vars(tag).items():
        k = k.rstrip("_")  # _ at the right is for clashed name
        if k == 'text':
            e.text = str(v)
        elif k == 'children':
            for child in v:
                e.append(to_xml(child))
        else:
            e.attrib[k] = str(v)
    return e


#
# Let the mapping begin!
#
# et = ET.parse("reference-file.jmx")
# mappings = []
# for e in et.iter():
#     attrs = ', '.join(map(lambda x: f"'{x}'", e.attrib.keys()))
#     leaf = len(list(e.iter())) > 0
#     s = f'{e.tag} = PyJMX("{e.tag}", [{attrs}], leaf={leaf})'
#     mappings.append(s)
# print('\n'.join(sorted(set(mappings), key=str.lower)))
assertions = PyJMX("assertions", [], leaf=True)
assertionsResultsToSave = PyJMX("assertionsResultsToSave", [], leaf=True)
boolProp = PyJMX("boolProp", ['name'], leaf=True)
bytes_ = PyJMX("bytes", [], leaf=True)
code = PyJMX("code", [], leaf=True)
collectionProp = PyJMX("collectionProp", ['name'], leaf=True)
connectTime = PyJMX("connectTime", [], leaf=True)
dataType = PyJMX("dataType", [], leaf=True)
elementProp = PyJMX("elementProp", [
                    'name', 'elementType', 'guiclass', 'testclass', 'testname', 'enabled'], leaf=True)
elementProp = PyJMX("elementProp", ['name', 'elementType'], leaf=True)
encoding = PyJMX("encoding", [], leaf=True)
fieldNames = PyJMX("fieldNames", [], leaf=True)
hashTree = PyJMX("hashTree", [], leaf=True)
HeaderManager = PyJMX(
    "HeaderManager", ['guiclass', 'testclass', 'testname', 'enabled'], leaf=True)
HTTPSamplerProxy = PyJMX("HTTPSamplerProxy", [
                         'guiclass', 'testclass', 'testname', 'enabled'], leaf=False)
idleTime = PyJMX("idleTime", [], leaf=True)
jmeterTestPlan = PyJMX(
    "jmeterTestPlan", ['version', 'properties', 'jmeter'], leaf=True)
label = PyJMX("label", [], leaf=True)
latency = PyJMX("latency", [], leaf=True)
message = PyJMX("message", [], leaf=True)
name = PyJMX("name", [], leaf=True)
objProp = PyJMX("objProp", [], leaf=True)
requestHeaders = PyJMX("requestHeaders", [], leaf=True)
responseData = PyJMX("responseData", [], leaf=True)
responseDataOnError = PyJMX("responseDataOnError", [], leaf=True)
responseHeaders = PyJMX("responseHeaders", [], leaf=True)
ResultCollector = PyJMX(
    "ResultCollector",
    ['guiclass', 'testclass', 'testname', 'enabled'], leaf=True)
samplerData = PyJMX("samplerData", [], leaf=True)
saveAssertionResultsFailureMessage = PyJMX(
    "saveAssertionResultsFailureMessage", [], leaf=True)
sentBytes = PyJMX("sentBytes", [], leaf=True)
stringProp = PyJMX("stringProp", ['name'], leaf=True)
subresults = PyJMX("subresults", [], leaf=True)
success = PyJMX("success", [], leaf=True)
TestPlan = PyJMX(
    "TestPlan", ['guiclass', 'testclass', 'testname', 'enabled'], leaf=True)
threadCounts = PyJMX("threadCounts", [], leaf=True)
ThreadGroup = PyJMX(
    "ThreadGroup", ['guiclass', 'testclass', 'testname', 'enabled'], leaf=True)
threadName = PyJMX("threadName", [], leaf=True)
time = PyJMX("time", [], leaf=True)
timestamp = PyJMX("timestamp", [], leaf=True)
url = PyJMX("url", [], leaf=True)
value = PyJMX("value", ['class_'], leaf=True)
xml = PyJMX("xml", [], leaf=True)

#
# High level mapping
#


def http_params(params):
    pass


def http_sampler(host, port, path, method, params=[]):
    return HTTPSamplerProxy(
        guiclass='HttpTestSampleGui',
        testclass='HTTPSamplerProxy',
        testname=host,
        enabled=True,
        children=[
            stringProp(name="HTTPSampler.domain", text=host),
            stringProp(name="HTTPSampler.port", text=port),
            stringProp(name="HTTPSampler.protocol", text=""),
            stringProp(name="HTTPSampler.contentEncoding", text=""),
            stringProp(name="HTTPSampler.path", text=path),
            stringProp(name="HTTPSampler.method", text=method.upper()),
            boolProp(name="HTTPSampler.follow_redirects", text="true"),
            boolProp(name="HTTPSampler.auto_redirects", text="false"),
            boolProp(name="HTTPSampler.use_keepalive", text="true"),
            boolProp(name="HTTPSampler.DO_MULTIPART_POST", text="false"),
            stringProp(name="HTTPSampler.embedded_url_re", text=""),
            stringProp(name="HTTPSampler.connect_timeout", text=""),
            stringProp(name="HTTPSampler.response_timeout", text=""),
        ]
    )


if __name__ == "__main__":
    sampler = http_sampler('localhost', 8080, '/items', method='get')
    xml = ET.tostring(to_xml(sampler))
    print(xml.decode('utf-8'))

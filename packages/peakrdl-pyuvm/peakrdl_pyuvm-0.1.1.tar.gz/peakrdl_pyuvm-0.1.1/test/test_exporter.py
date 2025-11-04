import importlib.resources
import importlib.util
import sys
import tempfile

import pytest
from systemrdl import RDLCompileError, RDLCompiler

from peakrdl_pyuvm.exporter import PyUVMExporter

from . import resources


@pytest.fixture(scope="session")
def model():
    rdlc = RDLCompiler()
#    for udp in ALL_UDPS:
#        rdlc.register_udp(udp)
    rdlfiles = [importlib.resources.path(resources, "TinyALUreg.rdl")]
    try:
        for rdlfile in rdlfiles:
            rdlc.compile_file(rdlfile)
        root = rdlc.elaborate()
    except RDLCompileError:
        raise SystemError
    filepath = tempfile.NamedTemporaryFile(delete=False, suffix=".py").name
    exporter = PyUVMExporter()
    exporter.export(root, filepath)
    module_name = "generated_model"
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_exporter(model):
    bar0 = model.BAR0("bar0")
    bar0.build()
    bar0.lock_model()

    assert len(bar0.get_registers()) == 57
    assert len(bar0.get_maps()) == 1
    assert len(bar0.get_blocks()) == 3
    assert bar0.get_name() == "bar0"

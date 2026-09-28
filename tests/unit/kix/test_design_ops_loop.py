#!/usr/bin/env python3
r"""
Test DesignOpsLoopKix (PRD-MOC-KIX-DESIGN-OPS-LOOP-CONSUMER-20260928)
"""
import io
import sys

# ERR_030 FIX
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from kix.pipelines.design_ops_loop import DesignOpsLoopKix


def test_design_ops_loop_run_completes():
    """DesignOpsLoopKix.run() returns COMPLETED with 3 phases."""
    loop = DesignOpsLoopKix(context={
        "need_ecosystemic": True,
        "action": "test_action",
        "coherence": True,
    })
    result = loop.run()

    assert result["status"] == "COMPLETED"
    assert result["loop"] == "THINK/DO/CHECK"
    assert len(result["phases"]) == 3
    assert "timestamp" in result


def test_design_ops_loop_think_phase():
    """THINK phase returns expected structure."""
    loop = DesignOpsLoopKix(context={"need_ecosystemic": True})
    think = loop.think()

    assert think["phase"] == "THINK"
    assert think["status"] == "OK"
    assert think["need_ecosystemic"] is True
    assert "timestamp" in think


def test_design_ops_loop_do_phase():
    """DO phase returns expected structure."""
    loop = DesignOpsLoopKix(context={"action": "deploy"})
    do = loop.do()

    assert do["phase"] == "DO"
    assert do["status"] == "OK"
    assert do["action"] == "deploy"
    assert "timestamp" in do


def test_design_ops_loop_check_phase():
    """CHECK phase returns expected structure."""
    loop = DesignOpsLoopKix(context={"coherence": True})
    check = loop.check()

    assert check["phase"] == "CHECK"
    assert check["status"] == "OK"
    assert check["coherence"] is True
    assert "timestamp" in check


def test_design_ops_loop_defaults():
    """Default context values are sensible."""
    loop = DesignOpsLoopKix()
    result = loop.run()

    assert result["phases"][0]["need_ecosystemic"] is False
    assert result["phases"][1]["action"] == "unknown"
    assert result["phases"][2]["coherence"] is True


def test_design_ops_loop_context_override():
    """Context can be overridden per phase."""
    loop = DesignOpsLoopKix(context={"action": "initial"})
    do1 = loop.do()
    do2 = loop.do(context={"action": "overridden"})

    assert do1["action"] == "initial"
    assert do2["action"] == "overridden"

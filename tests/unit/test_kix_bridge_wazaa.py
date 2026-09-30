"""Tests for src/kix_bridge_wazaa.py."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.kix_bridge_wazaa import KIXBridge, emit_edge, emit_runner_node


class TestKIXBridge:
    def test_emit_runner_started(self):
        publisher = MagicMock()
        bridge = KIXBridge(publisher=publisher)
        bridge.emit_runner_started(name="trixd", pid=1234, port=8742)
        publisher.publish.assert_called_once()
        args, kwargs = publisher.publish.call_args
        assert args[0]["event"] == "runner_started"
        assert args[0]["name"] == "trixd"

    def test_emit_runner_stopped(self):
        publisher = MagicMock()
        bridge = KIXBridge(publisher=publisher)
        bridge.emit_runner_stopped(name="trixd")
        publisher.publish.assert_called_once_with({"event": "runner_stopped", "name": "trixd"}, "kix_runner")

    def test_emit_zombie_detected(self):
        publisher = MagicMock()
        bridge = KIXBridge(publisher=publisher)
        bridge.emit_zombie_detected(pid=1234, name="zigzag", age_hours=2.5, zombie_type="process")
        publisher.publish.assert_called_once()
        args, kwargs = publisher.publish.call_args
        assert args[0]["zombie_type"] == "process"
        assert args[1] == "kix_zombie"

    def test_emit_phi_cps_update_with_soma(self):
        publisher = MagicMock()
        bridge = KIXBridge(publisher=publisher)
        bridge.emit_phi_cps_update(phi_cps=0.94, soma_metrics={"soma": 1.0})
        publisher.publish.assert_called_once()
        args, kwargs = publisher.publish.call_args
        assert args[0]["phi_cps"] == 0.94
        assert args[1] == "kix_phi_cps"

    def test_emit_phi_cps_update_without_soma(self):
        publisher = MagicMock()
        bridge = KIXBridge(publisher=publisher)
        bridge.emit_phi_cps_update(phi_cps=0.94)
        publisher.publish.assert_called_once()
        args, kwargs = publisher.publish.call_args
        assert args[0]["soma_metrics"] == {}


class TestAliases:
    def test_emit_runner_node(self):
        with patch("src.kix_bridge_wazaa.KIXBridge") as mock_cls:
            instance = mock_cls.return_value
            emit_runner_node(name="trixd", status="running", pid=1234, port=8742)
            instance.emit_runner_started.assert_called_once_with(name="trixd", status="running", pid=1234, port=8742)

    def test_emit_edge(self):
        with patch("src.kix_bridge_wazaa.KIXBridge") as mock_cls:
            instance = mock_cls.return_value
            emit_edge(src="a", dst="b", kind="causes", metadata={"key": "value"})
            instance.emit_phi_cps_update.assert_called_once()
            _, kwargs = instance.emit_phi_cps_update.call_args
            assert kwargs["phi_cps"] == 0.0
            assert kwargs["soma_metrics"]["edge"]["src"] == "a"
            assert kwargs["soma_metrics"]["edge"]["kind"] == "causes"

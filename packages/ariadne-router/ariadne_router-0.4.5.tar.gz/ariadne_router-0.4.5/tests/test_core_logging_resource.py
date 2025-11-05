from __future__ import annotations

import logging

import pytest
from qiskit import QuantumCircuit

from ariadne.core.logging import (
    PerformanceLogger,
    configure_logging,
    get_logger,
    log_debug,
    log_error,
    log_info,
    log_warning,
    set_log_level,
)


def test_ariadne_logger_records_context(caplog: pytest.LogCaptureFixture) -> None:
    logger = get_logger("routing-tests")
    caplog.set_level(logging.INFO)

    circuit = QuantumCircuit(1)
    circuit.x(0)

    logger.set_context(user_id="alice", session_id="session1")
    logger.log_routing_decision(circuit, backend="qiskit", confidence=0.95, reason="unit-test")
    logger.log_simulation_start(circuit, backend="qiskit", shots=16)
    logger.log_simulation_complete(0.05, shots=16)
    logger.log_backend_unavailable("cuda", "missing driver")
    logger.log_resource_warning("memory", usage=90.0, limit=100.0)
    logger.log_simulation_error(RuntimeError("failure"), backend="qiskit")

    assert any("routing-tests" in record.name for record in caplog.records)
    assert any("backend='cuda'" in record.message or "backend=cuda" in record.message for record in caplog.records)


def test_performance_logger_timing(caplog: pytest.LogCaptureFixture) -> None:
    logger = get_logger("performance-tests")
    caplog.set_level(logging.DEBUG)

    perf_logger = PerformanceLogger(logger)
    perf_logger.start_timer("segment")
    elapsed = perf_logger.end_timer("segment")
    assert elapsed >= 0.0

    perf_logger.end_timer("missing")  # Should emit warning, not raise.
    perf_logger.log_timing("compile", elapsed=0.1)
    perf_logger.log_memory_usage(128.0)

    assert any("Timer 'missing' was not started" in record.message for record in caplog.records)


def test_logging_configuration_helpers() -> None:
    logger = get_logger("level-tests")
    set_log_level(logging.DEBUG)
    assert logger.logger.level == logging.DEBUG

    configure_logging(level=logging.WARNING)
    root_logger = logging.getLogger("ariadne")
    assert root_logger.level == logging.WARNING

    # Convenience wrappers should not raise
    log_info("info message")
    log_warning("warning message")
    log_error("error message")
    log_debug("debug message")

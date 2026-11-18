import os
import subprocess
import sys

from textwrap import dedent

import pytest


@pytest.mark.skipif(os.name != "nt", reason="Requires a Windows console")
@pytest.mark.parametrize("scenario", ("single", "multiple", "force"))
def test_ctrl_c_finishes_worker_shutdown(tmp_path, port, scenario):
    script = tmp_path / "shutdown_app.py"
    script.write_text(
        dedent(
            """
            import asyncio
            import ctypes
            import multiprocessing
            import signal
            import sys
            import threading

            from sanic import Sanic, text

            app = Sanic("windows_shutdown")
            scenario = sys.argv[2]
            workers = 1 if scenario == "single" else 2

            def custom_worker(ready):
                signal.signal(signal.SIGINT, signal.SIG_IGN)
                ready.set()
                multiprocessing.Event().wait()

            def interrupt():
                generate = ctypes.windll.kernel32.GenerateConsoleCtrlEvent
                assert generate(0, 0)

            @app.main_process_start
            async def setup(app):
                app.shared_ctx.ready = multiprocessing.Semaphore(0)
                app.shared_ctx.custom_ready = multiprocessing.Event()
                app.shared_ctx.stopping = multiprocessing.Event()
                app.shared_ctx.hung = multiprocessing.Event()
                app.shared_ctx.stopped = multiprocessing.Event()

            @app.main_process_ready
            async def ready(app):
                wait_for_ack = app.manager.wait_for_ack

                def interrupt_when_ready():
                    wait_for_ack()
                    for _ in range(workers):
                        assert app.shared_ctx.ready.acquire(timeout=10)
                    if scenario == "multiple":
                        assert app.shared_ctx.custom_ready.wait(10)
                    # Broadcast only inside this test's isolated console.
                    print("INTERRUPT_READY", flush=True)
                    interrupt()

                app.manager.wait_for_ack = interrupt_when_ready
                if scenario == "multiple":
                    app.manager.manage(
                        "Custom", custom_worker,
                        {"ready": app.shared_ctx.custom_ready},
                    )
                    shutdown_signal = app.manager.shutdown_signal

                    def worker_first(sig, frame):
                        assert app.shared_ctx.stopping.wait(10)
                        shutdown_signal(sig, frame)

                    signal.signal(signal.SIGINT, worker_first)
                elif scenario == "force":
                    def force_stop():
                        assert app.shared_ctx.hung.wait(10)
                        assert app.shared_ctx.stopped.wait(10)
                        interrupt()

                    threading.Thread(target=force_stop, daemon=True).start()

            @app.get("/")
            async def home(request):
                return text("ready")

            @app.after_server_start
            async def started(app):
                app.shared_ctx.ready.release()

            @app.before_server_stop
            async def before_stop(app):
                app.shared_ctx.stopping.set()
                if scenario == "force" and app.m.name.endswith("-0-0"):
                    signal.signal(signal.SIGINT, signal.SIG_IGN)
                    app.shared_ctx.hung.set()
                    await asyncio.Event().wait()
                await asyncio.sleep(0)
                print("BEFORE_STOP_COMPLETED", flush=True)

            @app.after_server_stop
            async def after_stop(app):
                print("AFTER_STOP_COMPLETED", flush=True)
                app.shared_ctx.stopped.set()

            if __name__ == "__main__":
                app.run(
                    port=int(sys.argv[1]), workers=workers, access_log=False
                )
            """
        )
    )
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    with subprocess.Popen(
        [sys.executable, str(script), str(port), scenario],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
        startupinfo=startupinfo,
    ) as process:
        try:
            output, _ = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                check=False,
            )
            output, _ = process.communicate(timeout=10)
            pytest.fail(f"Server did not finish shutting down:\n{output}")

    assert "INTERRUPT_READY" in output, output
    completed = 2 if scenario == "multiple" else 1
    assert output.count("BEFORE_STOP_COMPLETED") == completed, output
    assert output.count("AFTER_STOP_COMPLETED") == completed, output
    assert "Traceback" not in output, output
    assert process.returncode == 0, output
    assert ("Shutdown interrupted. Killing." in output) == (
        scenario == "force"
    ), output

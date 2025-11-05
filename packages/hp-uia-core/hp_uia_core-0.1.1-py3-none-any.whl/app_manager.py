import psutil
import subprocess
import time
import logging
import json
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from pywinauto import Application, Desktop
from pywinauto.base_wrapper import BaseWrapper
from pathlib import Path
import os


class AppManagerError(RuntimeError):
    ...


class AumidNotFoundError(AppManagerError):
    ...


class WindowNotFoundError(AppManagerError):
    ...


class ElementNotFoundError(AppManagerError):
    ...


@dataclass
class ElementInfo:
    handle:   int
    control_type: str
    name:     str
    automation_id: str
    rectangle: str        # "left, top, right, bottom"
    depth:    int         # distance from the root window


class AppManager:
    def __init__(self, *, backend: str = "uia", ele_wait_time: int = 1) -> None:
        self.backend = backend
        self.ele_wait_time = ele_wait_time
        self.elements: Optional[list[tuple[ElementInfo, BaseWrapper]]] = None
        self._app: Optional[Application] = None
        self._window: Optional[BaseWrapper] = None
        self._log: logging.Logger = logging.getLogger(__name__)

    # ---------- life‑cycle ----------
    def launch(self, app_name_or_path: str, *, delay: int = 1) -> subprocess.Popen:
        # if it is executable path like C:\Program Files\App\App.exe
        if os.path.exists(app_name_or_path) and app_name_or_path.lower().endswith(".exe"):
            self._log.info("Launching executable: %s", app_name_or_path)
            proc = subprocess.Popen([app_name_or_path])
        else:
            # Otherwise, treat it as a UWP app name
            aumid = self._get_aumid(app_name_or_path)
            self._log.info("Launching %s (AUMID=%s)", app_name_or_path, aumid)
            proc = subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{aumid}"])
        time.sleep(delay)
        return proc

    def connect(self, *, window_title: str | None = None,
                process_name: str | None = None,
                timeout: int = 3) -> BaseWrapper:
        if window_title:
            self._app = Application(self.backend).connect(title_re=rf".*{window_title}.*", timeout=timeout)
            self._log.info("Connected to window %s", window_title)
        elif process_name:
            # Connect to the first window of the process when it's ready
            retry = 0
            while retry < timeout and not self._app:
                time.sleep(1)
                for proc in psutil.process_iter(attrs=['pid', 'name']):
                    if proc.info['name'] == process_name:
                        pid = proc.info['pid']
                        windows = Desktop(backend="uia").windows()
                        for win in windows:
                            if win.process_id() == pid:
                                self._app = Application(self.backend).connect(handle=win.handle, timeout=timeout)
                                self._log.info("Connected to process %s (PID=%s)", process_name, pid)
                                break
                retry += 1
        else:
            raise ValueError("Must pass window_title or process_name")

        if not self._app:
            raise RuntimeError("App is not connected")

        self._window = self._app.top_window().wrapper_object()
        
        if not self._window:
            raise WindowNotFoundError("No window found for the application")
        
        self._window.set_focus()
        return self._window

    def close(self, *, graceful: bool = True) -> None:
        if self._window:
            self._log.info("Closing %s", self._window.window_text())
            if self._app:
                if graceful:
                    try:
                        self._app.top_window().close()
                    except Exception as e:
                        self._log.warning("Graceful close failed: %s, fallback to kill()", e)
                        self._app.kill()
                else:
                    self._app.kill()
            self._window = self._app = None

    def _find_element(self, locator: dict) -> Optional[BaseWrapper]:
        deadline = time.monotonic() + max(0, getattr(self, "ele_wait_time", 1))
        # 初次构建元素缓存
        if self.elements is None:
            self.refresh_elements()

        def match():
            for ei, ctrl in self.elements or []:
                if all(getattr(ei, key, None) == value for key, value in locator.items()):
                    return ctrl
            return None

        # 轮询直到超时
        while True:
            ctrl = match()
            if ctrl:
                return ctrl
            if time.monotonic() >= deadline:
                return None
            # 轻量等待+刷新
            time.sleep(0.2)
            self.refresh_elements()

    def refresh_elements(self, **kwargs):
        self.elements = self.extract_elements(**kwargs)

    def element(self, locator: dict) -> BaseWrapper:
        ctrl = self._find_element(locator)
        if ctrl is None:
            raise ElementNotFoundError(f"Element not found: {locator!r}")
        return ctrl

    def _get_aumid(self, name: str) -> str:
        ps_cmd = ["powershell", "-NoProfile", "-Command",
                  f"Get-StartApps | Where {{$_.Name -like '*{name}*'}} | "
                  "Select -ExpandProperty AppID"]
        try:
            result = subprocess.run(ps_cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get AUMID: {e}") from e
        if not (aumid := result.stdout.strip()):
            raise AumidNotFoundError(f"No AUMID found for {name!r}")
        return aumid

    def extract_elements(
        self,
        max_depth: int = 0,
        include_invisible: bool = False,
        dump_file: Optional[str | Path] = None,
    ) -> List[tuple[ElementInfo, BaseWrapper]]:
        """
        Walk the UI tree beneath `self._window` and return a list of
        (ElementInfo, BaseWrapper) tuples, each representing a UI control.

        Parameters
        ----------
        max_depth : int
            0 = unlimited. Set >0 to limit recursion.
        include_invisible : bool
            If False, skip controls with `is_visible() == False`.
        dump_file : str | Path | None
            If given, write the JSON dump to this path.

        Returns
        -------
        List[Tuple[ElementInfo, BaseWrapper]]
        """
        if not self._window:
            raise RuntimeError("No window connected. Call `connect()` first.")

        log = logging.getLogger(__name__)
        visited: list[tuple[ElementInfo, BaseWrapper]] = []

        def _walk(ctrl, depth: int = 0):
            if max_depth and depth > max_depth:
                return
            try:
                if include_invisible or ctrl.is_visible():
                    ei = ElementInfo(
                        handle=ctrl.handle,
                        control_type=ctrl.element_info.control_type,
                        name=ctrl.element_info.name,
                        automation_id=ctrl.element_info.automation_id or "",
                        rectangle=str(ctrl.rectangle()),
                        depth=depth,
                    )
                    visited.append((ei, ctrl))
                for child in ctrl.children():
                    _walk(child, depth + 1)
            except Exception as exc:  # controls can vanish mid‑walk
                log.debug("Skipped control: %s", exc)

        _walk(self._window)

        if dump_file:
            json_dump = [asdict(ei) for ei, _ in visited]
            json_str = json.dumps(json_dump, indent=2, ensure_ascii=False)
            Path(dump_file).write_text(json_str, encoding="utf-8")
            log.info("Wrote element dump to %s", dump_file)

        return visited

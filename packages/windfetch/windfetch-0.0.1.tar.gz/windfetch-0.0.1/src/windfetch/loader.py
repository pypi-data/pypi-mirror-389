import importlib.machinery
import json
import os
import sys
from typing import Tuple

import requests


# noinspection PyTypeChecker
class _Configer:
    Base = os.path.expanduser("~/.pyfetch")
    Config = os.path.join(Base, "config.json").replace("\\", "/")
    logo_path = os.path.join(Base, "logo.py").replace("\\", "/")
    logo_url = "https://pyfetch.starwindv.top/api/logo"
    os.makedirs(Base, exist_ok=True)

    Default_Config = {
        "logo_path": logo_path,
        "custom_logo_path": None,

        "download_default_logo" : True,
        "overwrite_default_logo": True,
        "load_customLogo_unsafe": False,
    }

    def _load(self)->Tuple[bool, str]:
        try:
            with open(self.Config, "r", encoding="utf-8") as f:
                self.config = json.load(f)
                return True, self.config
        except Exception as e:
            self.config = self.Default_Config
            self._save()
            return False, str(e)

    def _check_config(self)->None:
        required_keys = set(self.Default_Config.keys())
        current_keys  = set(self.config.keys())

        if not required_keys.issubset(current_keys) or current_keys < required_keys:
            sys.stderr.write("Pyfetch Config File is Missing Some Keys.\n")
            sys.stderr.write("Start Automatic Repair.\n")
            for key in required_keys:
                if key not in current_keys:
                    data = {
                        key: self.Default_Config.get(key)
                    }
                    self.config.update(data)
            self._save()

    def _save(self):
        try:
            with open(self.Config, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            raise Exception(str(e)) from e


class _SimpleLogo:
    # noinspection PyUnusedLocal
    @staticmethod
    def get(key):
        return ""


class Loader(_Configer):
    def _get_default_logo(self):
        response = requests.get(self.logo_url)
        response.raise_for_status()
        with open(self.logo_path, "w", encoding="utf-8") as f:
            f.write(response.text)

    def _prepare_default(self):
        self._load()
        self._check_config()
        try:
            if (
                    self.config["download_default_logo"]
                    and not
            os.path.exists(self.logo_path)
            ):
                self._get_default_logo()
        except Exception as e:
            sys.stderr.write(
                f"[Pyfetch Err ] Cannot download default logo: \n"
                f"{15*" "}- {str(e)}"
            )
        self.logo = self._unsafe_load(self.config["logo_path"], no_warn=True)

    @staticmethod
    def _unsafe_load(path: str, no_warn: bool = False):
        if not no_warn:
            sys.stderr.write(
                "[Pyfetch Warn] "
                + "The tool retrieves the logo using an unsafe method."
                + f"\n{15*" "}Please verify that the corresponding code file"
                + f"\n{15*" "}does not contain any malicious code.\n"
            )
        loader = importlib.machinery.SourceFileLoader("Temp", path)
        return getattr(loader.load_module(), "logo")

    def _prepare_custom(self):
        if self.config["load_customLogo_unsafe"]:
            self.custom_logo = self._unsafe_load(self.config["custom_logo_path"])
        else:
            sys.stderr.write(
                f"[Pyfetch Ban ] Your Configuration is Not Allowed Unsafe Load Logo.\n"
                + f"{15*" "}The Custom Logo was Not Loaded.\n"
            )

    def __init__(self):
        self.logo = {}
        self.custom_logo = {}

        self._prepare_default()
        if self.config.get("custom_logo_path"):
            self._prepare_custom()
        if isinstance(self.logo, dict):
            self.logo.update(self.custom_logo)
        elif self.custom_logo:
            self.logo = self.custom_logo
        else:
            self.logo = _SimpleLogo() # 兜底工作

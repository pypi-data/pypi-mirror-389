import importlib.machinery
import json
import os
import sys
from typing import Tuple

import requests


# noinspection PyTypeChecker
class _Configer:
    Base = os.path.expanduser("~/.windfetch")
    Config = os.path.join(Base, "config.json").replace("\\", "/")
    logo_path = os.path.join(Base, "logo.py").replace("\\", "/")
    logo_url = "https://windfetch.starwindv.top/api/logo"
    os.makedirs(Base, exist_ok=True)

    Default_Config = {
        "logo_path": logo_path,
        "custom_logo_path": None,
        "logo_url": logo_url,
        "download_default_logo" : True,
        "load_customLogo_unsafe": False,
        "need_update_logo": False,
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
            sys.stderr.write("WindFetch Config File is Missing Some Keys.\n")
            sys.stderr.write("Start Automatic Repair.\n")
            for key in required_keys:
                if key not in current_keys:
                    data = {
                        key: self.Default_Config.get(key)
                    }
                    self.config.update(data)
            self._save()
            # print(self.config)

    def _save(self):
        try:
            with open(self.Config, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
                f.flush()
        except Exception as e:
            raise Exception(str(e)) from e


class _SimpleLogo:
    # noinspection PyUnusedLocal
    @staticmethod
    def get(key):
        return ""


class Loader(_Configer):
    def _get_default_logo(self):
        response = requests.get(self.config.get("logo_url"))
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
            ) or (self.config["need_update_logo"]):
                self._get_default_logo()
        except Exception as e:
            sys.stderr.write(
                f"[WindFetch Err ] Cannot download default logo: \n"
                f"{17*" "}- {str(e)}"
            )
            return
        self.logo = self._loads(self.config["logo_path"], no_warn=True)

    @staticmethod
    def _unsafe_load(path: str, no_warn: bool = False):
        if not no_warn:
            sys.stderr.write(
                "[WindFetch Warn] "
                + "The tool retrieves the logo using an unsafe method."
                + f"\n{17*" "}Please verify that the corresponding code file"
                + f"\n{17*" "}does not contain any malicious code.\n"
            )
        try:
            loader = importlib.machinery.SourceFileLoader("Temp", path)
            return getattr(loader.load_module(), "logo")
        except AttributeError:
            return {}

    def _loads(self, path: str, no_warn: bool = False):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f) # 假设 logo 为 json 格式
        except json.JSONDecodeError: # 如果非 json, 则尝试以 Python 代码的形式加载
            return self._unsafe_load(path, no_warn=no_warn)

    def _prepare_custom(self):
        if self.config["load_customLogo_unsafe"]:
            self.custom_logo = self._loads(self.config["custom_logo_path"])
        else:
            sys.stderr.write(
                f"[WindFetch Ban ] Your Configuration is Not Allowed Unsafe Load Logo.\n"
                + f"{17*" "}The Custom Logo was Not Loaded.\n"
            )

    def __init__(self):
        self.logo = {}
        self.custom_logo = {}

        self._prepare_default()
        if self.config.get("custom_logo_path"):
            self._prepare_custom()
        if isinstance(self.logo, dict):
            self.logo.update(self.custom_logo)
        elif isinstance(self.custom_logo, dict):
            self.logo = self.custom_logo # 兜底
        else:
            self.logo = _SimpleLogo() # 还是兜底

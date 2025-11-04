#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse


__PYTHON_VERSION = sys.version_info

# Compatibility imports and version check
if __PYTHON_VERSION >= (3, 8):
    CONCURRENCY_MODE = "asyncio"
elif __PYTHON_VERSION >= (3, 0):
    CONCURRENCY_MODE = "threading_py3"
else:
    CONCURRENCY_MODE = "threading_py2"

# do import
if CONCURRENCY_MODE == "asyncio":
    import asyncio
elif CONCURRENCY_MODE == "threading_py3":
    from concurrent.futures import ThreadPoolExecutor  # noqa
else:
    try:
        # Attempt to import Python 2.7 compatibility libraries
        from futures import ThreadPoolExecutor
        from Queue import Queue

    except ImportError:
        CONCURRENCY_MODE = "unsupported"

# Core
PY_INFO = sys.version_info
MAX_LATENCY = float("inf")

MAIN = [
    "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/",
    "https://repo.huaweicloud.com/repository/pypi/simple/",
    "https://mirrors.aliyun.com/pypi/simple/",
    "https://pypi.mirrors.ustc.edu.cn/simple/",
    "https://mirrors.cloud.tencent.com/pypi/simple/",
]

BACKUP = [
    "https://pypi.doubanio.com/simple/",
    "https://mirrors.163.com/pypi/simple/",
    "https://mirror.baidu.com/pypi/simple/",
]

ALL_MIRRORS = set(MAIN + BACKUP)

DEFAULT_INDEX_URL = "https://pypi.org/simple"
EXTRA_INDEX_URLS = []


class MirrorTester:
    """
    A mirror source speed tester compatible with Python 2.7 to 3.x.
    Automatically selects asyncio (>=3.8) or ThreadPoolExecutor (<=3.7) based on Python version.
    """

    def __init__(self, urls, timeout=5.0):
        self.urls = urls
        self.timeout = timeout
        self.results = []
        self.mode = CONCURRENCY_MODE

        print(
            f"Detected Python Version: {PY_INFO.major}.{PY_INFO.minor}.{PY_INFO.micro} ({self.mode})"
        )
        print("=" * 40)

        self.__fastest_url = None

    @property
    def fastest_url(self):
        return self.__fastest_url

    def _parse_url(self, url):
        """Parse URL and return hostname and port."""
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        port = parsed_url.port or (443 if host.startswith("https://") else 80)
        if not host:
            raise ValueError(f"Invalid URL host: {url}")

        return host, port

    # --- Core Sync Speed Test Function (for Threading/Fallback) ---

    def _test_connection_sync(self, url):
        """Test a single connection speed using synchronous socket."""
        try:
            host, port = self._parse_url(url)
            ip = socket.gethostbyname(host)
        except Exception:
            return url, MAX_LATENCY

        start_time = time.time()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)

        try:
            sock.connect((ip, port))
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            return url, round(latency, 2)
        except Exception:
            return url, MAX_LATENCY
        finally:
            sock.close()

    # --- Async Executor (Asyncio >= 3.8) ---

    async def _test_connection_async(self, url):
        """Test a single connection speed using asyncio."""
        try:
            host, port = self._parse_url(url)
            ip = socket.gethostbyname(host)
        except Exception:
            return url, MAX_LATENCY

        start_time = time.time()

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=self.timeout
            )
            end_time = time.time()
            latency = (end_time - start_time) * 1000

            writer.close()
            await writer.wait_closed()
            return url, round(latency, 2)
        except Exception:
            return url, MAX_LATENCY

    async def _run_async(self):
        """Run all async test tasks concurrently."""
        tasks = [self._test_connection_async(url) for url in self.urls]
        return await asyncio.gather(*tasks)

    # --- Main Execution Logic ---

    def compare_connection_speeds(self, test_time=2):
        """Choose execution mode based on Python version."""

        if self.mode == "unsupported":
            print(
                "Error: Python version is too old (< 2.7 or missing 'futures' dependency for 2.7). Cannot proceed."
            )
            return

        print(f"--- Starting connection speed test using {self.mode} mode ---")

        if self.mode == "asyncio":
            # Prefer asyncio
            try:
                # asyncio.run exists in 3.7+, but this branch will be enabled only for >=3.8
                for _ in range(test_time):
                    self.results += asyncio.run(self._run_async())
            except Exception as e:
                print(f"Asyncio execution failed: {e}. Falling back to Threading.")
                for _ in range(test_time):
                    self.results += self._run_sync_executor()

        elif self.mode.startswith("threading"):
            # Use ThreadPoolExecutor (compatible with 2.7 and 3.x)
            for _ in range(test_time):
                self.results += self._run_sync_executor()

        self._report_results()

    def _run_sync_executor(self):
        """Run sync tests using ThreadPoolExecutor."""
        max_workers = min(32, len(self.urls))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._test_connection_sync, url) for url in self.urls]
            return [future.result() for future in futures]

    def _report_results(self):
        """Report the final results, showing only the fastest connection for each URL."""
        if not self.results:
            print("No results were gathered.")
            return

        print("\n--- Speed Test Results Summary ---")

        # Filter out the successful results
        successful_results = [r for r in self.results if r[1] != MAX_LATENCY]

        if successful_results:
            # Initialize a dictionary to store the minimum latency for each unique URL
            best_results = {}

            # Iterate over successful results to find the minimum latency for each URL
            for url, latency in successful_results:
                if url not in best_results or latency < best_results[url]:
                    best_results[url] = latency

            # Convert the dictionary to a sorted list by latency
            sorted_results = sorted(best_results.items(), key=lambda x: x[1])

            # The fastest URL
            fastest_url, min_latency = sorted_results[0]
            self.__fastest_url = fastest_url

            print(f"*** The fastest mirror is: {fastest_url}")
            print(f"*** Latency: {min_latency:.2f} ms")

            print("\n--- All Successful Connection Results (URL, Latency in ms) ---")
            for url, latency in sorted_results:
                print(f"  {url}: {latency:.2f} ms")
        else:
            print(
                "Error: All mirror connections have failed or timed out."
                "Please check your network or try again later."
            )


def set_global_pip_mirror(mirror_url, backup_mirror_url=None):
    """Set pip global mirror and add backup as PyPI."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "config", "set", "global.index-url", mirror_url])
        print(f"Global pip mirror has been successfully set to: {mirror_url}")

        if backup_mirror_url:
            _kv = " ".join(backup_mirror_url)

            subprocess.check_call(
                [sys.executable, "-m", "pip", "config", "set", "global.extra-index-url", _kv.strip()]
            )
            print(f"Backup mirror has been successfully set to: {backup_mirror_url}")

    except subprocess.CalledProcessError as e:
        print(f"Error occurred while setting pip mirror: {e}")
        return False
    return True


def reset_pip_mirror():
    """Reset pip configuration to default."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "config", "unset", "global.index-url"])
        subprocess.check_call([sys.executable, "-m", "pip", "config", "unset", "global.extra-index-url"])
        print("pip configuration has been reset to the default settings.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while resetting pip configuration: {e}")
        return False
    return True


def _input_with_timeout(prompt, timeout=5):
    """Prompts user for input with a timeout."""
    from queue import Queue, Empty
    from threading import Thread

    print(prompt)
    result_queue = Queue()

    def get_input():
        user_input = input()
        result_queue.put(user_input)

    # Start the input thread
    input_thread = Thread(target=get_input)
    input_thread.daemon = True  # Ensure it won't block program exit
    input_thread.start()

    # Wait for the input or timeout
    try:
        return result_queue.get(timeout=timeout)
    except Empty:
        print("\nTimeout reached! No input received.")
        return None


def core_main(auto_yes=False):
    if CONCURRENCY_MODE == "threading_py2" and "futures" not in sys.modules:
        print(
            "Warning: Running on Python 2.7. "
            "Please ensure that the 'futures' library is installed using `pip install futures`."
        )

    tester = MirrorTester(urls=ALL_MIRRORS)
    tester.compare_connection_speeds()

    print("\n{}\n".format("= " * 20))

    # Determine whether to skip confirmation based on command-line arguments
    if auto_yes:
        inp = "y"
    else:
        inp = _input_with_timeout("Do you want to set the fastest mirror as the global pip mirror? (y/n): ")

    if inp and inp.lower() == "y":
        print("Setting the fastest mirror...")
        EXTRA_INDEX_URLS.append(DEFAULT_INDEX_URL)
        set_global_pip_mirror(
            mirror_url=tester.fastest_url,
            backup_mirror_url=EXTRA_INDEX_URLS
        )
    else:
        print("Skipping mirror setup.")
        sys.exit(0)


def entry_point():
    parser = argparse.ArgumentParser(description="A tool to test mirror sources and configure pip.")
    parser.add_argument(
        "--reset", action="store_true",
        help="Reset pip configuration to default settings."
    )

    # Add -y/–y switch to automatically confirm
    parser.add_argument(
        "-y", "--y", action="store_true",
        help="Automatically confirm setting the fastest mirror."
    )

    parser.add_argument(
        "--add-nvidia", action="store_true",
        help="(Alpha) Add nvidia mirror for rapids.ai"
    )

    # Paddle wheel
    parser.add_argument(
        "--add-paddle-cpu", action="store_true",
        help="Add PaddlePaddle CPU wheel repo as extra-index."
    )
    parser.add_argument(
        "--add-paddle-cu118", action="store_true",
        help="Add PaddlePaddle CUDA 11.8 wheel repo as extra-index."
    )
    parser.add_argument(
        "--add-paddle-cu126", action="store_true",
        help="Add PaddlePaddle CUDA 12.6 wheel repo as extra-index."
    )
    parser.add_argument(
        "--add-paddle-cu129", action="store_true",
        help="Add PaddlePaddle CUDA 12.9 wheel repo as extra-index."
    )
    parser.add_argument(
        "--add-paddle-fastdeploy-80-90", action="store_true",
        help="Add Paddle FastDeploy SM80/90 wheel repo as extra-index."
    )
    parser.add_argument(
        "--add-paddle-fastdeploy-86-89", action="store_true",
        help="Add Paddle FastDeploy SM86/89 wheel repo as extra-index."
    )
    parser.add_argument(
        "--add-paddle-gcu", action="store_true",
        help="Add Paddle GCU wheel repo as extra-index."
    )
    parser.add_argument(
        "--add-paddle-npu", action="store_true",
        help="Add Paddle NPU wheel repo as extra-index."
    )

    # PyTorch wheel
    parser.add_argument(
        "--add-pytorch-cpu", action="store_true",
        help="Add PyTorch CPU wheel repo as extra-index."
    )
    parser.add_argument(
        "--add-pytorch-cu118", action="store_true",
        help="Add PyTorch CUDA 11.8 wheel repo as extra-index."
    )
    parser.add_argument(
        "--add-pytorch-cu121", action="store_true",
        help="Add PyTorch CUDA 12.1 wheel repo as extra-index."
    )
    parser.add_argument(
        "--add-pytorch-cu124", action="store_true",
        help="Add PyTorch CUDA 12.4 wheel repo as extra-index."
    )
    parser.add_argument(
        "--add-pytorch-cu126", action="store_true",
        help="Add PyTorch CUDA 12.6 wheel repo as extra-index."
    )
    parser.add_argument(
        "--add-pytorch-rocm60", action="store_true",
        help="Add PyTorch ROCm 6.0 wheel repo as extra-index."
    )
    parser.add_argument(
        "--add-pytorch-rocm61", action="store_true",
        help="Add PyTorch ROCm 6.1 wheel repo as extra-index."
    )
    parser.add_argument(
        "--add-pytorch-rocm62", action="store_true",
        help="Add PyTorch ROCm 6.2 wheel repo as extra-index."
    )

    # Intel XPU
    parser.add_argument(
        "--add-intel-xpu-us", action="store_true",
        help="Add Intel XPU wheel repo (US) as extra-index."
    )
    parser.add_argument(
        "--add-intel-xpu-cn", action="store_true",
        help="Add Intel XPU wheel repo (CN) as extra-index."
    )

    args = parser.parse_args()

    if args.reset:
        reset_pip_mirror()
        return

    if getattr(args, "add_nvidia", False):
        EXTRA_INDEX_URLS.append("https://pypi.nvidia.com/")

    # Paddle 系
    __base_paddle_mirror = "https://www.paddlepaddle.org.cn/packages/stable"
    if getattr(args, "add_paddle_cpu", False):
        EXTRA_INDEX_URLS.append(__base_paddle_mirror + "/cpu/")
    if getattr(args, "add_paddle_cu118", False):
        EXTRA_INDEX_URLS.append(__base_paddle_mirror + "/cu118/")
    if getattr(args, "add_paddle_cu126", False):
        EXTRA_INDEX_URLS.append(__base_paddle_mirror + "/cu126/")
    if getattr(args, "add_paddle_cu129", False):
        EXTRA_INDEX_URLS.append(__base_paddle_mirror + "/cu129/")
    if getattr(args, "add_paddle_fastdeploy_80_90", False):
        EXTRA_INDEX_URLS.append(__base_paddle_mirror + "/fastdeploy-gpu-80_90/")
    if getattr(args, "add_paddle_fastdeploy_86_89", False):
        EXTRA_INDEX_URLS.append(__base_paddle_mirror + "/fastdeploy-gpu-86_89/")
    if getattr(args, "add_paddle_gcu", False):
        EXTRA_INDEX_URLS.append(__base_paddle_mirror + "/gcu/")
    if getattr(args, "add_paddle_npu", False):
        EXTRA_INDEX_URLS.append(__base_paddle_mirror + "/npu/")

    # PyTorch whl 仓库
    __base_pytorch_mirror = "https://download.pytorch.org/whl"
    if getattr(args, "add_pytorch_cpu", False):
        EXTRA_INDEX_URLS.append(__base_pytorch_mirror + "/cpu")
    if getattr(args, "add_pytorch_cu118", False):
        EXTRA_INDEX_URLS.append(__base_pytorch_mirror + "/cu118")
    if getattr(args, "add_pytorch_cu121", False):
        EXTRA_INDEX_URLS.append(__base_pytorch_mirror + "/cu121")
    if getattr(args, "add_pytorch_cu124", False):
        EXTRA_INDEX_URLS.append(__base_pytorch_mirror + "/cu124")
    if getattr(args, "add_pytorch_cu126", False):
        EXTRA_INDEX_URLS.append(__base_pytorch_mirror + "/cu126")
    if getattr(args, "add_pytorch_rocm60", False):
        EXTRA_INDEX_URLS.append(__base_pytorch_mirror + "/rocm6.0")
    if getattr(args, "add_pytorch_rocm61", False):
        EXTRA_INDEX_URLS.append(__base_pytorch_mirror + "/rocm6.1")
    if getattr(args, "add_pytorch_rocm62", False):
        EXTRA_INDEX_URLS.append(__base_pytorch_mirror + "/rocm6.2")

    # Intel XPU
    __base_intel_mirror = "https://pytorch-extension.intel.com/release-whl/stable"
    if getattr(args, "add_intel_xpu_us", False):
        EXTRA_INDEX_URLS.append(__base_intel_mirror + "/xpu/us/")
    if getattr(args, "add_intel_xpu_cn", False):
        EXTRA_INDEX_URLS.append(__base_intel_mirror + "/xpu/cn/")

    core_main(auto_yes=args.y)


if __name__ == "__main__":
    entry_point()

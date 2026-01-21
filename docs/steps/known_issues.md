# Known Issues and Blockers

This document lists the known issues that are currently blocking the progress of the QVM project. The primary goal for the next session should be to resolve these issues to enable testing and further development.

---

## 1. Core Issue: Persistent Network Errors with `pip`

We are experiencing persistent network errors when attempting to use `pip` to install Python packages from the Python Package Index (PyPI).

**Symptoms:**
- Commands like `pip install -r requirements.txt` and `pip install --upgrade pip` consistently fail.
- The errors are related to network connectivity, including:
  - `ReadTimeoutError`: The connection to the server times out during package download.
  - `NewConnectionError`: `pip` fails to establish a new connection to the server.
  - `OSError: [Errno -3] Temporary failure in name resolution`: This indicates a DNS resolution problem, where the domain names (`pypi.org`, `files.pythonhosted.org`) cannot be resolved to IP addresses.

**Example Error Log:**
```
ERROR: Could not install packages due to an OSError: HTTPSConnectionPool(host='files.pythonhosted.org', port=443): Max retries exceeded with url: ... (Caused by NewConnectionError('<pip._vendor.urllib3.connection.HTTPSConnection object at ...>: Failed to establish a new connection: [Errno -3] Temporary failure in name resolution'))
```

---

## 2. Impact

This core network issue has the following blocking impacts on the project:

- **Inability to Install Dependencies:** We cannot install crucial packages like `numpy`, `pytest`, and `matplotlib` as defined in `requirements.txt`.
- **Blocked Verification:** Without `pytest` and `numpy`, we are unable to run the unit tests that have been written for the QVM modules. The correctness of the `simulator`, `transpiler`, etc., remains unverified.
- **Blocked Visualization:** The implementation of visualization features (e.g., probability histograms) is blocked because `matplotlib` cannot be installed.
- **Blocked Manual Testing:** Even "manual" verification by running example scripts like `src/examples/full_pipeline.py` fails because the script cannot import `numpy`.

---

## 3. Recommended Next Steps

To unblock the project, the underlying network issue must be resolved. This is likely an issue with the local machine's environment, network configuration, or firewall settings, and cannot be resolved by the agent.

**Action Items for the Next Session:**
1.  **Investigate and Resolve Network/DNS Issues:** Ensure that the environment has a stable internet connection and can correctly resolve DNS queries for `pypi.org` and `files.pythonhosted.org`.
2.  **Verify Connectivity:** A simple test would be to try `ping pypi.org` or `curl https://pypi.org` from the command line.
3.  **Attempt Dependency Installation:** Once the network issue is believed to be resolved, the first step should be to run `.venv/bin/python -m pip install -r requirements.txt`.
4.  **Run Unit Tests:** If the dependencies are successfully installed, the immediate next step should be to run `pytest` to verify the correctness of the implemented QVM components.

# Lict: OneClick

[Lict](https://gitee.com/openharmony-sig/compliance_license_compatibility/) (LiScopeLens) tool one-click startup script.

## Requirements

1. **Python** >= 3.11
2. **Docker**
3. `pip install -r reqirements.txt`

## Time Overhead

1. **Compilation Time and Scancode License Scanning Time**: Approximately 8-24 hours (data has not been rigorously tested; the exact duration depends on hardware performance).
2. **License Detection Overhead**: ≤10 minutes

## Usage

```shell
usage: run.py [-h] [--system_spec SYSTEM_SPEC] [--tag TAG] [--oh_path OH_PATH] [--lict_cmd LICT_CMD] [--product_name PRODUCT_NAME] [--output OUTPUT] [--shadow SHADOW]

Lict setup script with Docker image support.

options:
  -h, --help            show this help message and exit
  --system_spec SYSTEM_SPEC
                        System specification key or direct input.
  --tag TAG             Docker image tag (default: 3.2).
  --oh_path OH_PATH     OpenHarmony source code path (default: ./oh-source).
  --lict_cmd LICT_CMD   LICT command name (default: lict).
  --product_name PRODUCT_NAME
                        Product name (default: rk3568).
  --output OUTPUT       Results output path (default: ./output)
  --shadow SHADOW       Node2license JSON file to shadow scancode results
```

**Obtain OpenHarmony source code [see here](#example)。**

### Parameter Descriptions

- `-h, --help`  
  Show help information and exit.

- `--system_spec SYSTEM_SPEC`  
  System specification key or direct input.

- `--tag TAG`  
  Docker image tag (default: `3.2`).

- `--oh_path OH_PATH`  
  OpenHarmony source code path (default: `./oh-source`).

- `--lict_cmd LICT_CMD`  
  LICT command name (default: `lict`).

- `--product_name PRODUCT_NAME`  
  Product name (default: `rk3568`).

- `--output OUTPUT`  
  Results output path (default: `./output`).

- `--shadow SHADOW`  
  Node2license JSON file to shadow scancode results.

## Example

1. Refer to the [official documentation](https://docs.openharmony.cn/pages/v5.0/en/device-dev/get-code/sourcecode-acquire.md) to obtain the source code to any desired path, for example: `/path/to/oh-source-code`.
    **If you are `windows` user**，please manually download [repo](https://gitee.com/oschina/repo/raw/fork_flow/repo-py3), and rename `repo` to `repo.py`:
    - Replace all `repo xxxx` that in official docs to `python repo.py xxxx`, e.g. `repo sync -c` > `python repo.py sync -c`.
    - Attention: Confirm `requests` package installed your pc's python env (`pip install requests`).
    ```powershell
    mkdir -p path/to/source-code ;; cd path/to/source-code
    # in case encode error
    set PYTHONUTF8=1
    # get source code
    # suppose your repo.py path is ../repo.py
    python ..\repo.py init -u https://gitee.com/openharmony/manifest -b refs/tags/OpenHarmony-v5.0.1-Release --no-repo-verify
    python ..\repo.py sync -c
    python ..\repo.py forall -c git lfs pull
    ```
     

2. Execute the script:

    ```shell
    python run.py --oh_path /path/to/oh-source-code
    ```

    To specify additional parameters, refer to the following example:

    ```shell
    python run.py --system_spec "spec_key" --tag "3.2" --oh_path "/path/to/oh-source-code" --lict_cmd "lict" --product_name "rk3568" --output "/path/to/output" --shadow "/path/to/shadow.json"
    ```

## Notes

- Ensure that the `--oh_path` argument matches the path where you have obtained the OpenHarmony source code.
- The default Docker image tag is set to `3.2`, but you can specify a different tag using the `--tag` option if needed.
- The default product name is `rk3568`, which can be changed using the `--product_name` option based on your target device.

## Additional Information

- **System Specifications:** The `--system_spec` option allows you to specify different system configurations. Refer to the [SYSTEM_SPEC](#) section in the script for available options or provide a direct input.
- **LICT Command:** The `--lict_cmd` option lets you define a custom name for the LICT command if it differs from the default `lict`.

### Shadow Parameter Details

- Using the `--shadow` parameter allows you to specify an existing Node2license JSON file to override the scancode results. This can help improve detection accuracy or skip specific checks in certain scenarios.

    **Example:**

    ```json
    // Example where the license model for the following component is Apache-2.0
    node [
        id 66
        label "//applications/standard/calendardata/calendarmanager/napi/src/calendar_enum_napi.cpp"
        parser_name "GnParser"
        type "code"
        licenses "[[{\"spdx_id\": \"Apache-2.0\", \"condition\": null, \"exceptions\": []}]]"
        test "Apache-2.0_f"
        before_check "[[{\"spdx_id\": \"Apache-2.0\", \"condition\": null, \"exceptions\": []}]]"
        outbound "[[{\"spdx_id\": \"Apache-2.0\", \"condition\": \"COMPILE\", \"exceptions\": []}]]"
    ]
    // After manual verification, the actual license is MIT. You can pass --shadow-license shadow.json
    // shadow.json
    {
        "//applications/standard/calendardata/calendarmanager/napi/src/calendar_enum_napi.cpp": "MIT"
    }
    ```

    **Note**: Shadow files support [standard license expressions](https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/).

## Important

- Ensure that **Python** and **Docker** are installed, and the Docker service is running.
- Compilation and scanning times may vary depending on system performance and the size of the source code. Please be patient.
- Using the `--shadow` parameter with a shadow JSON file can help customize license detection results, enhancing accuracy or bypassing certain checks as needed.

If you have any questions or need further assistance, please refer to the [official documentation](https://gitee.com/openharmony-sig/compliance_license_compatibility/) or contact the maintainers.
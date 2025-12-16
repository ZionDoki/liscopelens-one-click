补充缺失的参数说明后，完整的 **liscopelens: OneClick** 文档如下：

# liscopelens: OneClick

[English Version](/README.en.md)

[liscopelens](https://gitee.com/openharmony-sig/compliance_license_compatibility/)（LiScopeLens）工具一键启动脚本。

## Time Overhead

1. **编译时间、scancode 许可证扫描时间**：大概 8-24 小时（数据未经严格测试，具体时间取决于硬件性能）
2. **许可证检测时间开销**：≤10 分钟

## Requirements

1. **Python** >= 3.12
2. **Docker**
3. `pip install -r reqirements.txt`

## Usage

```shell
usage: run.py [-h] [--system_spec SYSTEM_SPEC] [--tag TAG] [--oh_path OH_PATH] [--lict_cmd LICT_CMD] [--product_name PRODUCT_NAME] [--output OUTPUT] [--shadow SHADOW]

liscopelens setup script with Docker image support.

options:
  -h, --help            show this help message and exit
  --system_spec SYSTEM_SPEC
                        System specification key or direct input.
  --tag TAG             Docker image tag (default: 3.2).
  --oh_path OH_PATH     Openharmony source code path (default: ./oh-source).
  --lict_cmd LICT_CMD   liscopelens command name (default: liscopelens).
  --product_name PRODUCT_NAME
                        Product name (default: rk3568).
  --output OUTPUT       Results output path (default: ./output)
  --shadow SHADOW       Node2license JSON file to shadow scancode results
```

**获取源码参见[本节](#example)。**

### 参数说明

- `-h, --help`  
  显示帮助信息并退出。

- `--system_spec SYSTEM_SPEC`  
  系统规格关键字或直接输入。

- `--tag TAG`  
  Docker 镜像标签（默认值：3.2）。

- `--oh_path OH_PATH`  
  OpenHarmony 源代码路径（默认值：`./oh-source`）。

- `--lict_cmd LICT_CMD`  
  liscopelens 命令名称（默认值：`liscopelens`）。

- `--product_name PRODUCT_NAME`  
  产品名称（默认值：`rk3568`）。

- `--output OUTPUT`  
  结果输出路径（默认值：`./output`）。

- `--shadow SHADOW`  
  用于覆盖 scancode 结果的 Node2license JSON 文件。

## Example

1. 参考 [官方文档](https://docs.openharmony.cn/pages/v5.0/zh-cn/device-dev/get-code/sourcecode-acquire.md) 获取源码到任意路径 `/path/to/oh-source-code`。
    **如果你是 windows 用户**，可以手动下载 [repo](https://gitee.com/oschina/repo/raw/fork_flow/repo-py3) 重命名 `repo` 为 `repo.py`：
    - 替换文档中获取源码指令为 `python repo.py xxxx` 比如 `repo sync -c` > `python repo.py sync -c`
    - 注意：确保本机 `python` 安装 `requests` (`pip install requests`)
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
     
2. 执行脚本：

   ```shell
   python run.py --oh_path /path/to/oh-source-code
   ```

   如需指定其他参数，可以参考以下示例：

   ```shell
   python run.py --system_spec "spec_key" --tag "3.2" --oh_path "/path/to/oh-source-code" --lict_cmd "liscopelens" --product_name "rk3568" --output "/path/to/output" --shadow "/path/to/shadow.json"
   ```

## 备注

- 确保已安装 **Python** 和 **Docker**，并且 Docker 服务正在运行。
- 根据系统性能和源码大小，编译及扫描时间可能有所不同，请耐心等待。
- 使用 `--shadow` 参数可以指定一个现有的 Node2license JSON 文件，以覆盖 scancode 的扫描结果，这在某些情况下可能有助于提高检测准确性或跳过特定检查。

    ```JSON
    // 比如如下组件的许可证模型为 Apache-2.0
    node [
        id 66
        label "//applications/standard/calendardata/calendarmanager/napi/src/calendar_enum_napi.cpp"
        parser_name "GnParser"
        type "code"
        licenses "[[{&#34;spdx_id&#34;: &#34;Apache-2.0&#34;, &#34;condition&#34;: null, &#34;exceptions&#34;: []}]]"
        test "Apache-2.0_f"
        before_check "[[{&#34;spdx_id&#34;: &#34;Apache-2.0&#34;, &#34;condition&#34;: null, &#34;exceptions&#34;: []}]]"
        outbound "[[{&#34;spdx_id&#34;: &#34;Apache-2.0&#34;, &#34;condition&#34;: &#34;COMPILE&#34;, &#34;exceptions&#34;: []}]]"
    ]
    // 经过人工核验和许可证实际为 MIT 此时可以传入 --shadow-license shadow.json
    // shadow.json
    {
        "//applications/standard/calendardata/calendarmanager/napi/src/calendar_enum_napi.cpp": "MIT"
    }
    ```

    **请注意**：Shadow 文件支持[标准许可证表达式](https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/)。

如果有任何疑问或需要进一步的帮助，请参考 [官方文档](https://gitee.com/openharmony-sig/compliance_license_compatibility/) 或联系维护者。
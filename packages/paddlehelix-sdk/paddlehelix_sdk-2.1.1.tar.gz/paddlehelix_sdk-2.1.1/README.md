# 快速使用 PaddleHelix SDK

![PyPI - Version](https://img.shields.io/pypi/v/paddlehelix-sdk)
![PyPI - Downloads](https://img.shields.io/pypi/dm/paddlehelix-sdk)


PaddleHelix Python SDK 是 [PaddleHelix 网站](https://paddlehelix.baidu.com/) 提供的整套服务的一部分，通过 SDK 提交和管理的任务将同步在网页端显示。您可以使用 SDK 来批量调用 PaddleHelix 平台服务，并将 PaddleHelix 服务自动化集成到自己的项目中。

PaddleHelix Python SDK 已升级到 2.1 版本，修复大量已知问题，欢迎大家体验！

## 0. 安装前必备

请先自行安装好 python，版本大于等于 3.7.0，可以从 [python 官网](https://www.python.org/) 下载安装包，或使用 conda：

```shell
   conda create -n phsdk python=3.13
   conda activate phsdk
```

## 1. 安装 PaddleHelix SDK
    
目前 PaddleHelix Python SDK 已发布到 PyPI，可使用 pip 命令进行安装。

```shell
   pip3 install -U paddlehelix-sdk
```

## 2. 设置API鉴权AK、SK
1. 若您还未注册 PaddleHelix 账号，请先移步: [PaddleHelix 网站](https://paddlehelix.baidu.com/)，随后点击右上角 **立即体验** 按钮注册账号。
2. 开通 CHPC 服务（若已开通则跳过此步）：[前往开通](https://console.bce.baidu.com/chpc/#/landing)。  
3. 获取鉴权所需的密钥 AK 和 SK（注意必须申请**主账号AKSK**，子账号的支持仍在开发中）。具体步骤请参考：[如何获取 AK、SK](https://cloud.baidu.com/doc/Reference/s/9jwvz2egb)。
4. 调用 SDK 设置 AK、SK。注意请用你的 AK、SK 替换下面命令的 <your_ak>、<your_sk> 两个字段：  
    ```bash
    python3 -m paddlehelix.cli.client --ak <your_ak> --sk <your_sk>
    ```
**注意：首次设置 AK、SK 后，下次使用相同的账号提交无需重复设置**，SDK 会将其保存在用户的配置文件中。若需更换 AK、SK，可重复此步，新配置将覆盖原有信息。更多有关 AK、SK 的信息见 [SDK配置文档](docs/common/SDK配置.md)。

## 3. 快速使用 HelixFold 3 顶层接口

SDK 为用户提供了一个便捷的[顶层接口](docs/helixfold3/execute.md)，来完成询价、提交、查询任务状态、结果下载的全部流程。

**注意：顶层接口单次提交最大支持 1000 条任务，超过请参考 [提交大批量任务的最佳实践](docs/helixfold3/execute.md#section3)。**

1. 将下面的 python 代码片段保存为一个文件 `example.py`。

> `input_data` 参数指定了 HelixFold3 的输入（具体格式请参考：[HelixFold3 输入数据格式](https://paddlehelix.baidu.com/app/tut/guide/all/helixfold3json)），`output_dir` 指定了本次提交的输出路径。

```python
from paddlehelix.task import helixfold3

input_data = [
    {
        "job_name": "7xwo_chain_F_22",
        "entities": [
            {
                "type": "protein",
                "sequence": "HKTDSFVGLMA",
                "count": 2
            }
        ]
    }
]
helixfold3.execute(input_data=input_data, output_dir="output")
```

2. 用下面的命令启动提交流程。**注意：本次提交将消耗 0.14 元，若您的百度云余额不足，SDK 将提示余额不足并退出。**

```bash
python3 example.py
```

3. 任务将耗时几分钟，您将在终端中看到任务运行的全过程。当任务结束后，将显示本次提交的汇总信息，示例输出如下：

```text
[2025-09-19 00:22:22 main]: INFO Task summary:
+-----------+------------+---------+---------------------------------------------------------------------+
|   task_id | status     |   price | storage_path                                                        |
+===========+============+=========+=====================================================================+
|    207618 | DOWNLOADED |    0.14 | output/result/helixfold3_result_to_download_6jr4_20250919002154.zip |
+-----------+------------+---------+---------------------------------------------------------------------+
[2025-09-19 00:22:22 main]: INFO The submission summary printed above are stored in: output/table.csv
```

4. 获取任务结果。可以直接通过第3步打印出的表格中的 `storage_path` 字段得知各个任务结果的路径，完整表格记录在：`{output_dir}/table.csv`。每个任务的结果都是一个 zip 压缩包，压缩包中的内容可参考: [压缩包内容说明](https://paddlehelix.baidu.com/app/tut/guide/all/helixfold3) 中的`数据下载`部分。

更多关于提交过程的说明见 [HelixFold 3/S1 顶层接口](docs/helixfold3/execute.md)。

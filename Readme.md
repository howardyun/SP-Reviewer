# Todo
## 数据
- [ ] 第二波数据的数据仓库到Pypi包之间的映射 
-  [ ] 整理已经扫出来的密钥泄露到文件夹中 
## 代码
- [ ] 整理 [testSctipt](Token_test%2FHF%2FtestSctipt)中main函数的代码逻辑，使其可以自动检测密钥有效性





# 数据解释

## 提取每个fs layer中的Pypi包：

### Pypi包统计信息
[first_data_pypi_info.json](dockerPull%2FData%2FPypi%2FPypiMetaData%2Ffirst_data_pypi_info.json) \

[second_data_pypi_info.json](dockerPull%2FData%2FPypi%2FPypiMetaData%2Fsecond_data_pypi_info.json)

### fs 与Pypi包映射
[kv_all_layer_pypi.db](dockerPull%2FData%2Flayer%2Fkv_all_layer_pypi.db)



## 将每个docker与fs layer中的Pypi包进行映射：
[kv_all_layer_pypi.db](dockerPull%2FData%2Flayer%2Fkv_all_layer_pypi.db)



## Pypi包与OSV的映射关系：
第一波数据:\
[result_first.csv](dockerPull%2FData%2FPypi%2Fpypi_osv%2Fresult_first.csv)\
第二波数据:\
[result_second.csv](dockerPull%2FData%2FPypi%2Fpypi_osv%2Fresult_second.csv)



## docker与OSV的映射关系：
第一波数据:\
[repo_pypi_first_time.db](dockerPull%2FData%2Frepo%2Frepo_pypi_first_time.db)\
第二波数据:\


# 代码文件结构解释
## [DataCollection](DataCollection)
存储数据收集文件
### 收集文件列表：[CollectSpaceList.py](DataCollection%2FCollectSpaceList.py)
### 收集Space环境变量：[CollectSpaceVariable.py](Data Collection%2FCollectSpaceVariable.py)

## [dockerPull](dockerPull)
### [PackageExtract](dockerPull%2FAnalysis%2FPackageExtract)
工具类：[analysisUtils.py](dockerPull%2FAnalysis%2FPackageExtract%2FanalysisUtils.py)\
Layer与Pypi包的映射:[extractEachLayerPypi.py](dockerPull%2FAnalysis%2FPackageExtract%2FextractEachLayerPypi.py)
### [testDownloadFunctions](dockerPull%2FAnalysis%2FtestDownloadFunctions)
#### 测试下载是否存在文件缺失：[testFileexist.py](dockerPull%2FAnalysis%2FtestDownloadFunctions%2FtestFileexist.py)
#### 根据Manifest文件查找缺失的Layer：[testLackLayers.py](dockerPull%2FAnalysis%2FtestDownloadFunctions%2FtestLackLayers.py)

## [PackageAnalysis](dockerPull/PackageAnalysis)
### [Analysis](dockerPull/PackageAnalysis/CVEAnalysis/Analysis.py)
包的cve,cwe分析
### [analyze_cwe_docker_impact_to_csv](dockerPull/PackageAnalysis/CVEAnalysis/analyze_cwe_docker_impact_to_csv.py)
调用 llm 判断 CWE 是否对 Docker 有影响。
### [pypi_cwe_frequency_analysis](dockerPull/PackageAnalysis/CVEAnalysis/pypi_cwe_frequency_analysis.py)
统计pypi包中cwe的频率
### [draw_cwe_warehouse_bar_chart](dockerPull/PackageAnalysis/CVEAnalysis/draw_cwe_warehouse_bar_chart.py)
绘制仓库中 Top-N 的 CWE 类型分布柱状图。

## [packages_info_code](dockerPull/PackageAnalysis/packages_info_code)
### [kv_layer_dangling.py](dockerPull/PackageAnalysis/packages_info_code/kv_layer_dangling.py)
extracts dangling package from the layer.
### [PypiClassifier.py](dockerPull/PackageAnalysis/packages_info_code/PypiClassifier.py)
使用llm对包进行分类
### [github_check](dockerPull/PackageAnalysis/packages_info_code/github_check.py)
检查包是否在github上
### [pypi_calculation](dockerPull/PackageAnalysis/packages_info_code/pypi_calculation.py)
该脚本从指定的 SQLite 数据库中读取每个仓库的 pypi_info_list，解析并统计包实例总数、唯一包数（含/不含版本号），并将出现频率最高的前 50 个包绘制成柱状图。
### [top10_daling_packages](dockerPull/PackageAnalysis/packages_info_code/top10_daling_packages.py)
统计dangling包的频率

## [Analysis](Analysis)
### [Organizational_analysis](Analysis/Organizational_analysis.py)
env中huggingface token的org的提取
### [space_dataset__model.py](Analysis/space_dataset__model.py)
分析space关联的model和datasets
### [Top-10_Users_Public_vs_Private_Resources](Analysis/Top-10_Users_Public_vs_Private_Resources.py)
分析Top-10用户公开和私有资源



### [back_up_files](dockerPull%2Fback_up_files)：备份已有数据

### [Data](dockerPull%2FData)：数据集中存储 subsubfolder
#### [layer](dockerPull%2FData%2Flayer) subsubsubfolder
Layer到pypi包的映射
#### [Pypi](dockerPull%2FData%2FPypi) subsubsubfolder
Pypi到OSV的映射
#### [repo](dockerPull%2FData%2Frepo) subsubsubfolder
Space仓库到Pypi包的映射

#### [Pypi](dockerPull/PackageAnalysis/packages_info_code/kv_layer_dangling.py)
Pypi空包到Space的映射

#### [PypiAnalysis](dockerPull/PackageAnalysis/packages_info_code/PypiClassifier.py)
Pypi分类

## [PackageAnalysis](dockerPull%2FPackageAnalysis) subfolder


## [Pull](dockerPull%2FPull) subfolder

## [Regex_Match](Regex_Match) folder
正则匹配代码

## [ScanSecret](ScanSecret) folder

## [Analysis](Analysis) 
[Organizational_analysis](Analysis/Organizational_analysis.py)
env中huggingface token的org的提取
[space_dataset__model.py](Analysis/space_dataset__model.py)
space关联的model和datasets


## 测试密钥有效性：[Token_test](Token_test) folder
### HF 
#### [testSctipt](Token_test%2FHF%2FtestSctipt)

能够获取token的详细权限，以此来评估实际安全风险:[hf_access_info.py](Token_test%2FHF%2FtestSctipt%2Fhf_access_info.py)

测试token有效性：[hf_token_test.py](Token_test%2FHF%2FtestSctipt%2Fhf_token_test.py)，用法：python hf_token_test.py 泄露的token






# 导入必要的模块
import os
import platform
import re
import json


# 设置规则文件和过滤规则文件的路径
rulefile = os.path.join(os.path.dirname(os.path.abspath(__file__)),"regexes_v2.json")
filterfile = os.path.join(os.path.dirname(os.path.abspath(__file__)),"filter_regexes.json")

# 初始化正则表达式字典
regexes = dict()
filter_regexes = dict()

# 读取规则文件并编译正则表达式
try:
    with open(rulefile, "r") as ruleFile:
            rules = json.loads(ruleFile.read())
            for rule in rules:
                rules[rule] = re.compile(rules[rule])
except (IOError, ValueError) as e:
        raise("Error reading rules file")
for regex in rules:
    regexes[regex] = rules[regex]

# 读取过滤规则文件并编译正则表达式
try:
    with open(filterfile, "r") as filterFile:
        filter_rules = json.loads(filterFile.read())
        for filter_rule in filter_rules:
            filter_rules[filter_rule] = re.compile(filter_rules[filter_rule])
except (IOError, ValueError) as e:
        raise("Error reading filter rules file")
for filter_regex in filter_rules:
        filter_regexes[filter_regex] = re.compile(filter_rules[filter_regex])


def report_results(f):
    """
    处理匹配结果，过滤掉符合过滤规则的匹配项
    
    参数:
        f: 包含匹配字符串的列表
        
    返回:
        返回不符合过滤规则的第一个匹配字符串,如果字符串长度超过100则截断
    """
    # 如果结果不匹配任何过滤规则，则返回它
    for string_found in f:
        string_filtered = False
        for filter_regex in filter_regexes:
            if filter_regexes[filter_regex].match(string_found):
                string_filtered = True
                break
        if string_filtered == False:
            if(len(string_found)>100):
                string_found=string_found[:100]
            return string_found
    #bcolors.OKGREEN, string_found, bcolors.ENDC)


def regex_check(strings_output, custom_regexes={}):
    """
    使用正则表达式检查输入字符串中的潜在敏感信息
    
    参数:
        strings_output: 需要检查的字符串
        custom_regexes: 可选的自定义正则表达式字典，默认为空
        
    返回:
        返回经过过滤的匹配结果
    """
    if custom_regexes:
        secret_regexes = custom_regexes
    else:
        secret_regexes = regexes
    regex_matches = []
    for key in secret_regexes:
        strings_found = secret_regexes[key].findall(strings_output)
        if strings_found!=[]:
            return key,report_results(list(set(strings_found)))

# 主函数入口
if __name__ == "__main__":
     # 测试一个可能的API密钥字符串
     print(regex_check(""))
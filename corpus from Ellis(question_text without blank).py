import numpy as np
import pandas as pd
import re

#这个结合cc_alphabet可以一起用来判断question_text里面的内容
#这个也会被用到
#通过使用any和all来改写cc_chinese，改写后的cc_chinese可以检查是否全为中文或是否包含中文
#这个版本改写一下，用all代替any，就可以坚持是否全是中文，逻辑很简单，any为True的情况下，就是包含中文，ALL就是全中文
#所以目前这个版本就是用于检测包含中文的字段的，因为黑处理的是text部分的字段。
def cc_chinese(check_str):
    check_list = []
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            check_list.append(True)
        else:
            check_list.append(False)
    if any(check_list):
        return True
    else:
        return False
        
def cc_alphabet(check_str):
    check_list = []
    for uchar in check_str:
        if (uchar >= u'\u0041' and uchar<=u'\u005a') or (uchar >= u'\u0061' and uchar<=u'\u007a'):
            check_list.append(True)
        else:
            check_list.append(False)
    if any(check_list):
        return True
    else:
        return False
    
def cc_number(check_str):
    for uchar in check_str:
        if uchar >= u'\u0030' and uchar<=u'\u0039':
            return True
        else:
            return False
        
def select_u_s_qt(dict):
    index_list = []
    for k,v in dict.items():
        if "." in v:
            index_list.append(k)
        elif "!" in v:
            index_list.append(k)
        elif "?" in v:
            index_list.append(k)
        else:
            pass
    return index_list

#重新定制化这两个函数，在一个正常句子里面会包含这些字符串，如果它是一个完整的英语句子的话
#大概有这么些标点符号
#正则表达式也可以，但是反正性能上也都问题不大的话，直接这样写函数吧，这样也少了标点符号位置问题
def check_sents(check_str):
    check_list = []
    punc_list = [',', '.', ':', ';', '?', '(', ')', '!', '*', '@', '#', '$', '%', '’', ' '] #别忘了空格
    for uchar in check_str:
        if (uchar >= u'\u0041' and uchar<=u'\u005a') or (uchar >= u'\u0061' and uchar<=u'\u007a'):
            check_list.append(True)
        elif uchar >= u'\u0030' and uchar<=u'\u0039':
            check_list.append(True)
        elif uchar in punc_list:
            check_list.append(True)
        else:
            check_list.append(False)
    if all(check_list):
        return True
    else:
        return False

#读进之前merge好并导出成csv的dataset
data = pd.read_csv("data_ready_to_use.csv", index_col = 0)
#列表中有exercise_id和这个是否是published的exercise，目前只用published的版本，提高corpus的质量
#两种类型的可以被使用，一个是published，一个是verified
data_fillter = pd.read_csv("exercise_status.csv", index_col = 0)
data_fillter.reset_index(inplace = True)
data_fillter.rename({"ExerciseID":"exercise_id"}, inplace=True, axis = 1)
#完整的data完成之后应该是这样的
data_ff = pd.merge(data, data_fillter,on = "exercise_id", how = "left")
#然后只保留有verified和published的部分
#后续的部分全部都在data_ff上，代替掉之前那个data
#然后由于只采用了published和verified的版本，因此语料总数减少了
data_ff = data_ff[(data_ff.Status == "verified") | (data_ff.Status == "published")]

data_qt = data_ff.dropna(subset=["question_text"])
data_qt.reset_index(inplace=True, drop=True)
#首先是找出是句子的那些question_text

data_qt_d = data_qt.to_dict()
index_list = select_u_s_qt(data_qt_d["question_text"])
data_qt = data_qt.iloc[index_list]
data_qt.reset_index(inplace=True, drop=True)
data_qt = data_qt[data_qt.is_key == True]
data_qt.reset_index(inplace=True, drop=True)
data_qt.drop_duplicates(subset=["exercise_id", "question_text"], inplace = True)
data_qt.reset_index(inplace=True, drop=True)
data_qt_d = data_qt.to_dict()

#首先把全部是英文的句子找出来，没有特殊符号，没有其他东西，只有字母和数字。
#思路大概是用正则表达式确定结尾，用函数判断中间全部都是英文的句子，不允许特殊符号。
#用上面的check_sents函数，解决这个问题。
all_sents = []
for i in data_qt["question_text"]:
    if check_sents(i):
        all_sents.append(i)

#有些特殊情况的数据，直接抛弃掉，数量不大
#然后有一些描述词性特殊的单词的其实没有意义，直接抛掉
#还有一些带括号的，那些需要把括号中的内容抛掉
#但是因为用的是pop，每次pop之后index都变化，所以会跳着pop，因此在数据量大的情况下需要重复执行
for k,v in enumerate(all_sents):
    if ". . ." in v:
        all_sents.pop(k)
    elif "..." in v:
        all_sents.pop(k)
    elif "adj." in v:
        all_sents.pop(k)
    elif "adv." in v:
        all_sents.pop(k)
    elif "n." in v:
        all_sents.pop(k)
    elif "v." in v:
        all_sents.pop(k)
    elif "prep." in v:
        all_sents.pop(k)
    elif "sth." in v:
        all_sents.pop(k)
    elif "sb." in v:
        all_sents.pop(k)

#小写开头的都可以全部抛弃掉了，不是完整的真正的句子，只是一段不完整的话。
pattern = re.compile("^[a-z].+")
for k,v in enumerate(all_sents):
    try:
        pattern.search(v).group()
        all_sents.pop(k)
    except:
        pass


a_s_index = []
for k,v in data_qt_d["question_text"].items():
    if v in all_sents:
        a_s_index.append(k)
    else:
        pass

data_qt.reset_index(inplace=True, drop=True)
data_all_s = data_qt.iloc[a_s_index]
data_all_s.drop_duplicates(subset=["exercise_id","question_text"], inplace=True)
data_all_s.reset_index(inplace=True, drop=True)
data_all_s = data_all_s.astype(str)

check_list_0 = []
for i in range(len(data_all_s)):
    check_list_0.append(data_all_s.iloc[i]["question_text"] + 
                      "{platform:" + "Ellis" + "}" + 
                      "{type:" + "question_text" + "}" +
                       "{is_key:" + data_all_s.iloc[i]["is_key"] + "}" 
                      "{exercise_id:" + data_all_s.iloc[i]["exercise_id"] + "}" +
                      "{course_id:" + data_all_s.iloc[i]["course_id"] + "}" +
                      "{unit:" + data_all_s.iloc[i]["course_unit_id"] + "}" + 
                      "{parameter:" + data_all_s.iloc[i]["parameter"] + "}" +
                      "{question_id:" + data_all_s.iloc[i]["question_id"] + "}" +
                      "{package_id:" + data_all_s.iloc[i]["package_id"] + "}" +
                      "{Status:" + data_all_s.iloc[i]["Status"] + "}" +
                      "{isfilled:No}"
                     )

#加上|n
for i in range(len(check_list_0)):
    check_list_0[i] = check_list_0[i] + "\n"

#这一步最后再做，不然读取数据的时候会有问题
#就在全部读进列表之后处理吧
#去掉那些不要的括号中的内容，这些是改写句子，其实在text部分中都已经有，去掉也不影响本身句子的完整性
#为了能方便处理这其中的小括号，中括号等，需要考虑一个装各种参数的方式
#看了一下就决定是{}了，大括号只有一个，还是没什么用的
pattern = re.compile("\(.+\)")
for i in range(len(check_list_0)):
    try:
        check_list_0[i] = pattern.sub("", check_list_0[i])
    except:
        pass

#去掉开头的数字
pattern = re.compile("^\d+\.")
for i in range(len(check_list_0)):
    try:
        check_list_0[i] = pattern.sub("", check_list_0[i])
    except:
        pass

pattern = re.compile("’")
for i in range(len(check_list_0)):
    try:
        check_list_0[i] = pattern.sub("'", check_list_0[i])
    except:
        pass


 with open("corpus from Ellis(question_text without blank).txt", "w", encoding = "utf-8") as f:
    f.writelines(check_list_0)

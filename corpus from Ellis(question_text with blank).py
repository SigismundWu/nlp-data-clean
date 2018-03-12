import numpy as np
import pandas as pd
import re

################################
#整个程序是由大量函数构成的
#主要的函数是final_process，其他在final_process中调度
#final_process完成之后输出的结果是一个包含了所有文本的list
#这个list会根据index，跟最后一个make_final_list函数结合
#make_final_list函数会把信息添加到final_process函数中的数据中
#最终完成带有标签信息的完整corpus
###############################

#首先要读进来的表有那么几张，json中重新提取的blank，tmjcxx，exercise_package
data_tmjcxx = pd.read_csv("tmjcxx.csv")
data_packageid = pd.read_csv("exercise_package.csv")
data_stat = pd.read_csv("exercise_status.csv")
data_w_blank = pd.read_csv("data_with_blank.csv", index_col = 0)

#然后对这些表进行合并
data = pd.merge(data_w_blank, data_stat, left_on = "exercise_id", right_on = "ExerciseID", how = "left")
data = pd.merge(data, data_packageid, on = "exercise_id", how = "left")
data = pd.merge(data, data_tmjcxx, on = "exercise_id", how = "left")
data.drop(["json_text"], axis=1, inplace=True)
data.reset_index(drop=True, inplace = True)

#对表进行整理,去除不需要信息，保留需要信息
data = data[(data["Status"] == "published") | (data["Status"] == "verified")]
data = data[data["is_key"] == True]
data.reset_index(drop=True, inplace=True)
data_wb = data[data["question_text"].str.contains("___")]
data_wb.reset_index(drop=True, inplace=True)
data_wb = data_wb.astype(str)

#去掉一些text本身就是nan或者选项A,B,C,D的那种条目，这些条目本身就可以不要
data_wb = data_wb[(data_wb["text"] != "F")&
        (data_wb["text"] != "T")&
        (data_wb["text"] != "A")&
        (data_wb["text"] != "B")&
        (data_wb["text"] != "C")&
        (data_wb["text"] != "D")&
        (data_wb["text"] != "E")&
        (data_wb["text"] != "nan")
       ]

data_wb.reset_index(drop = True, inplace = True)

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
    
#检测是否有中文符号的函数，这个函数可以单独使用也可以用于拓展那个函数
def c_chinese_punc(list):
    
    for key,str in enumerate(list):
        if "！" in str:
            list[key] = re.sub("！","!",list[key])
        elif "，" in str:
            list[key] = re.sub("，",",",list[key])
        elif "。" in str:
            list[key] = re.sub("。",".",list[key])
        elif "’" in str:
            list[key] = re.sub("’","'",list[key])
        else:
            pass
        
    return list

#check start with, 这个是用于最后检查的函数，
def check_sw(string):
    try:
        re.match("^[A-Z]", string).group()
        return string
    except:
        pass

#def一个函数，去除掉所有的中文,因为除了那些被框在
#利用这个写法即可以替代掉不需要的字符
def delete_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            check_str = check_str.replace(ch,"") 
        else:
            pass
    return check_str


#需要写一个check每个字符串是不是中文的函数
#那么不是中文就全部返回正确的
#这两个函数实际上是一个组合
def is_chinese(ch):
    if u'\u4e00' <= ch <= u'\u9fff':
        return True
    else:
        return False

#逻辑大概是：如果某些中文符号的两边都是英文，那么替换成英文符号
#但是如果两边不是中文。则替换，否则则删去，这个能解决人工检查见到的所有模式
#先写个pass，到时候再判断
#这个主要是为了处理中英文单引号和双引号的问题
def check_s_replace(string):
    
    new_string = ""
    
    pattern_dquo_marks = re.compile('“|”')
    string = pattern_dquo_marks.sub('"', string)
    pattern_squo_marks = re.compile("‘|’")
    string = pattern_squo_marks.sub("'", string)
    
    for i in range(len(string)):
        try:
            if (string[i] == "'") | (string[i] == '"'):
                if is_chinese(string[i+1]) | is_chinese(string[i-1]):
                    pass
                else: #这个else append的是不包裹中文的引号
                    new_string += string[i]
            else:
                new_string += string[i] #这个else append的是除了进入上一个判断的所有字符串
        except Exception as e: #这个exception就不打印了，测试时候看过了，都是index out of range, 不影响结果
            #print(e)
            pass
    return new_string

#把分段切割的句子合并的函数块，完成这个功能之后，就可以考虑把多余的少的不要的去掉了
#check start with
def check_swu(string):
    try:
        re.match("^[A-Z]", string).group()
        return True
    except Exception as e:
        return False

def check_swl(string):
    try:
        re.match("^[a-z]", string).group()
        return True
    except Exception as e:
        return False
    
def check_ewep(string):
    endpunc = [".", "!", "?", '"'] #这个双引号也是特殊情况，需要被考虑的，这个暂时这样处理，目前所能发现的双引号结尾的都结束的
    
    if string[-1] in endpunc:
        return True
    else:
        return False
    
#加一个函数提取需要的index
def extracting_index(index):
    if type(index) == list:
        return index[0]
    else:
        pass

def search_concate(lst):
    index_list = [] #这个用于append未被处理的数据的index，还有被拼接的数据的第一个条目的index，因为他们的信息其实一样，后面要用于对接原来的dataframe
    finished_list = [] #这个用于append完成的句子
    tmp_sents = "" #tmp_sents用于处理
    mf_index = [] #merged_from index, 这个也是记录index的方式
    
    for index in range(len(lst)):
        try:
            #下面是第一种情况，正常的大写开头结束符号结尾，直接append
            if check_swu(lst[index]) & check_ewep(lst[index]):
                finished_list.append(lst[index])
                index_list.append(index)
            #处理一下有问号但是最后不是终结符的提问组合句   
            elif check_swu(lst[index]) & (not check_ewep(lst[index])) & ("?" in lst[index]):
                finished_list.append(lst[index])
                index_list.append(index)
            
            #这里的话还有那些没有连接必要的，直接加入，小写开头，结尾没有标点符号
    #         elif check_swl(lst[index]) & (not check_ewep(lst[index])):
    #             finished_list.append(lst[index])
    #             index_list.append(index)
            #这个最先被搜索，大写开头，没有终结符
            elif check_swu(lst[index]) & (not check_ewep(lst[index])):
                tmp_sents += lst[index]
                mf_index.append(index)
            #下面这种是中间要被添加进去
            elif check_swl(lst[index]) & (not check_ewep(lst[index])):
                tmp_sents += " " + lst[index]
                mf_index.append(index)
            #这种是最终版的了，在这里还要把tmp_sents清零，重新构成一个新的
            elif check_swl(lst[index]) & check_ewep(lst[index]):
                tmp_sents += " " + lst[index]
                mf_index.append(index)
                finished_list.append(tmp_sents)
                #提取出第一个条目的信息，作为基础信息记录
                mfe_index = extracting_index(mf_index)
                index_list.append(mfe_index)
                #这些append都完成之后，后面初始化这两个存储，
                tmp_sents = ""
                mf_index = []

            else:
                pass
        except:
            pass

    return finished_list, index_list

#这个用于判断特殊竖杠是分隔单词还是答案
#其实这个整个大格子的函数里面最合理的就是pattern应该是 _+，这样所有下划线都能判断
def judge_vertial_bar(string):
    try:
        re.search("\w\|", string).group()
        return True
    except Exception as e:
#        print(e) 那个exception都是可以预料的，没有必要print了
        return False

#这个函数其实还可以用df[df["A"].str.replace()]来改写，可以获得更高的性能和更简洁的代码
def fill_in_the_blank(option, stem):
    p_num = 0
    stem_list = stem.split(" ")
    
    if "/" in option:
        option_list = option.split("/")
        
        for i in range(len(stem_list)):
            try:
                if re.search("_+",stem_list[i]):
                    pattern = re.compile("_+")
                    stem_list[i] = pattern.sub(option_list[p_num], stem_list[i])
                    p_num += 1
                else:
                    pass
            #这个try except主要是用于处理option_list和stem_list的长度不匹配的问题，因为后面直接填入之后必然会出现这两个的
            #数量差异，但是问题因为最后会用正则处理掉所有多余的下划线。
            #这些except直接可以选择写pass，因为会报列表长度超出的问题，实际上是没问题的。
            except:
                #print(i, ",", option, ",", stem)
                pass
            
    elif ". . ." in option:
        option_list = option.split(". . .")
        
        for i in range(len(stem_list)):
            try:
                if re.search("_+",stem_list[i]):
                    pattern = re.compile("_+")
                    stem_list[i] = pattern.sub(option_list[p_num], stem_list[i])
                    p_num += 1
                else:
                    pass
            except:
                #print(i, ",", option, ",", stem)
                pass

#这个部分要加入前面那个函数进行判断，然后进行补全
    elif "|" in option:
        
        if judge_vertial_bar(option):
            option = re.sub("\|", "", option)
            
            for i in range(len(stem_list)):
                pattern = re.compile("_+") #所以其实这个写法很方便简洁，确实解决了那些问题了，看看还有没有别的问题
                stem_list[i] = pattern.sub(option, stem_list[i])
        
        else:
            option_list = option.split("|")

            for i in range(len(stem_list)):
                try:
                    if re.search("_+",stem_list[i]):
                        pattern = re.compile("_+")
                        stem_list[i] = pattern.sub(option_list[p_num], stem_list[i])
                        p_num += 1
                    else:
                        pass
                except:
                    #print(i, ",", option, ",", stem)
                    pass

    elif ";" in option:
        option_list = option.split(";")
        
        for i in range(len(stem_list)):
            try:
                if re.search("_+",stem_list[i]):
                    pattern = re.compile("_+")
                    stem_list[i] = pattern.sub(option_list[p_num], stem_list[i])
                    p_num += 1
                else:
                    pass
            except:
                #print(i, ",", option, ",", stem)
                pass
    #在这里，带有反斜线，带反斜线的分隔符都是固定的三个连续的英文句号...
    #反斜线最后都是空白符，在最后会统一处理，用一个sub把所有反斜线都处理掉
    elif "..." in option:
        option_list = option.split("...")
        
        for i in range(len(stem_list)):
            try:
                if re.search("_+",stem_list[i]):
                    pattern = re.compile("_+")
                    stem_list[i] = pattern.sub(option_list[p_num], stem_list[i])
                    p_num += 1
                else:
                    pass
            except:
                #print(i, ",", option, ",", stem)
                pass
            
    else:
        #这个只需随意一个操作符，不会被split，会把完整的填进其中一个横线，都是连续的，后面多余的横线会被处理掉
        #记得需要随意一个操作符，这个位置，不然会出现填空差位的情况
        option_list = []
        option_list.append(option)

        for i in range(len(stem_list)):
            try:
                if re.search("_+",stem_list[i]):
                    pattern = re.compile("_+")
                    stem_list[i] = pattern.sub(option_list[p_num], stem_list[i])
                    p_num += 1
                else:
                    pass
            except:
                #print(i, ",", option, ",", stem)
                pass

    sents = " ".join(stem_list)
    #加上下面这一排，就把多余的不需要的下划线全部排除了
    pattern_underline = re.compile("_+")
    sents = pattern_underline.sub("",sents)
    #处理掉多余的反斜线
    pattern_r_slash = re.compile("\\\\")
    sents = pattern_r_slash.sub("", sents)
    #有些多余的双空格的也会被这样处理掉
    #这里有个处理的逻辑顺序问题，上面的都处理完之后最后再把数据规整化
#     下面的这个句子的处理改为放到最后处理函数的最后一个部分，因为可能存在处理完括号等之后
#     还存在新的多余空格的情况
#     pattern_p_blank = re.compile(" +")
#     sents = pattern_p_blank.sub(" ", sents)
#     改成一个list，用下面的函数把这个包起来，然后再传入最下面那个函数
    return sents

#多def一个函数，用来产生一个f_list
def generate_f_list(dataframe):
    text_only_list = []
    
    for index in range(len(dataframe)):
        sents = fill_in_the_blank(dataframe.iloc[index]["text"],
                                  dataframe.iloc[index]["question_text"])
        text_only_list.append(sents)
    
    return text_only_list

#用于删除prefix的函数
#这里稍微改写了一下
#下面用了一个闭包的方法，保证了即使本身没有任何东西返回的也是一个空字符串
#保证了写入txt文档时候的正确性，不会因为这个问题引发报错
#这样的话不存在那么多问题
def delete_prefix(string):
    
    def delete_p():
        for k,v in enumerate(string):
            try:
                re.match("[A-Z]|[a-z]|\"|'",v).group()
                return string[k:]
            except:
                pass
            
    string = delete_p()
    
    if string == None:
        string = ""
    else:
        pass
    
    return string


#这一步最后再做，不然读取数据的时候会有问题（但是是埋进FIB函数的最后）
#在这之前需要考虑一下这个问题怎么处理掉
#就在全部读进列表之后处理
#这个函数的目的是最后的输出的调整
#有很多杂乱无章的中文，杂乱无章的符号
#不需要的内容都要去掉
def final_process(dataframe):
    #把括号和里面的内容全部去掉，基本上都是提示之类的
    pattern_brackets = re.compile("\(.+\)|（.+）|\(.+）|（.+\)|\(\)|（|）")
    #最后替代掉多余的空格符
    pattern_p_blank = re.compile(" +")
    #整理HTML标签，HTML标签不能<.+>这样整理，不然后面的全没了，这个要改写
    #所以改写成如下的两个pattern，最后一起处理掉，后面那个反正就是当做括号处理了，那就可以一起处理掉了
    pattern_html_label = re.compile("(?<=\<).+?(?=\>)")
    pattern_mid_brac = re.compile("\<|\>|\[|\]")
    #去掉特殊的nbsp;
    pattern_nbsp = re.compile("&nbsp;|nbsp")
    #去掉br标签后面跟着的那些prefix,这个必须在处理HTML标签之前处理，pattern在这里写好，下面调用顺序在标签之前
    pattern_s_br = re.compile("<br>\d+\.")
    #去掉换行符或其他不规则的东西
    pattern_rn = re.compile("\r|\n|\xa0|\||/")
    #处理掉多余的中文符号和跟中文夹在一起的提示性内容：
    #中文符号好像一共就那么几种，因为像引号和双引号前面已经被处理和替代掉了
    pattern_bc_punc = re.compile(".+(?=。)|.+(?=！)|.+(?=？)")
    pattern_c_punc = re.compile("Example:|Example：|。|，|；|！|？|：")
    #影响判断的\r\n\r\n还有<br>\r\n
    pattern_rnrn = re.compile(".+(?=\r\n\r\n)|.+(?=<br>\r\n)|waswere")
    #调用这个函数得到f_list
    f_list = generate_f_list(dataframe)
    #下面这个循环没问题，如果是这样的话就避免进入异常处理节约性能
    for i in range(len(f_list)):
#         try:
        f_list[i] = pattern_brackets.sub("", f_list[i])
        f_list[i] = pattern_nbsp.sub(" ", f_list[i])
        #试试先去掉中文符号，会不会改变少了引号的问题
        f_list[i] = pattern_bc_punc.sub("", f_list[i])
        f_list[i] = pattern_c_punc.sub("", f_list[i])
        #下面两个是先代替掉中文引号，后面那个是处理掉中文，如此一来会先处理完中文符号，再删除掉多余的中文
        f_list[i] = check_s_replace(f_list[i])
        f_list[i] = delete_chinese(f_list[i])
        #下面是一堆完整的正则表达式，处理多余情况
        f_list[i] = pattern_s_br.sub("", f_list[i])
        f_list[i] = pattern_html_label.sub("", f_list[i])
        f_list[i] = pattern_mid_brac.sub("", f_list[i])
        f_list[i] = pattern_rnrn.sub("", f_list[i])
        f_list[i] = pattern_rn.sub("", f_list[i])
        f_list[i] = delete_prefix(f_list[i])
        f_list[i] = f_list[i].strip(" ")
        #下面是处理多余空格的，这个一般都最后再做
        f_list[i] = pattern_p_blank.sub(" ", f_list[i])
#         except:
#             pass
        #但是最后如果有None还是要处理一下，不然会导致没有办法写入
    
    #联结函数应该在所有处理完成之后，也就是在这个位置，最后进行联结
    f_list, i_list = search_concate(f_list)
    #完成上面那个之后再加入换行符
    for i in range(len(f_list)):
        if f_list[i] == None:
            f_list = "\n"
        else:    
            f_list[i] = f_list[i] + "\n"

    #后期再处理函数
    
    return f_list, i_list

#往list里面添加basic_info的函数
#再写一个大函数把其他部分粘合起来，逻辑其实十分简单
#但是其实这个还需要后期的处理的，后期处理再写一个函数
#主要的问题就是写好的句子里面还会有___，这是由于不同长度导致的，问题不大，这个可以被直接去掉来解决
#原理是有一些是一个词切分了，所以导致会只填入第一个横线，但是问题不大，直接一个正则替换掉下划线就可以了
#update:为清洗好的数据增加一个花括号作为分组的依据
def make_final_list(dataframe):
    check_list_0 = []
    f_list, i_list = final_process(dataframe)
    dataframe = dataframe.iloc[i_list] #然后这个的话会是经过处理的dataframe，只有需要的index和相应的信息
    
    for i in range(len(dataframe)):
        try:
            check_list_0.append("{cleaned_data:" + f_list[i] + "}" +
                              "{platform:" + "Ellis" + "}" +
                              "{type:" + "question_text" + "}" +
                              "{is_key:" + dataframe.iloc[i]["is_key"] + "}" 
                              "{exercise_id:" + dataframe.iloc[i]["exercise_id"] + "}" +
                              "{course_id:" + dataframe.iloc[i]["course_id"] + "}" +
                              "{unit:" + dataframe.iloc[i]["course_unit_id"] + "}" +
                              "{parameter:" + dataframe.iloc[i]["parameter"] + "}" +
                              "{question_id:" + dataframe.iloc[i]["question_id"] + "}" +
                              "{package_id:" + dataframe.iloc[i]["package_id"] + "}" +
                              "{Status:" + dataframe.iloc[i]["Status"] + "}" +
                              "{filled with:" + dataframe.iloc[i]["text"] + "}" +
                              "{isfilled:Yes}" +
                              "\n"
                             )
        except:
            print("error,num" + i)

    return check_list_0

t_f_l = make_final_list(data_wb)

with open("corpus from Ellis(question_text with blank).txt", "w", encoding = "utf-8") as f:
    f.writelines(t_f_l)
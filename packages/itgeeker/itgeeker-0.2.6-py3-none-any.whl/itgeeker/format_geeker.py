# -*- coding: utf-8 -*-
import json
import chardet


def check_charset(code_data):
    # import chardet
    charset = chardet.detect(code_data)['encoding']
    print('charset: %s' % charset)
    return charset


def format_dict_style(data_dict):
    try:
        return json.dumps(data_dict, indent=4, sort_keys=True, ensure_ascii=False, default=str)
        # return json.dumps(data_dict, indent=4, sort_keys=True, ensure_ascii=False, default=str).encode('utf-8')
    except Exception as err:
        print('json.dumps error@itgeeker: %s' % err)

####################### deal list  #######################
# compare two list and return add and del list
def compare_lists_return_add_del(first_list, second_list):
    add_list = []
    del_list = []
    diff_list = list(
        set(first_list).symmetric_difference(
            set(second_list)))
    if diff_list:
        print('diff_list: %s' % diff_list)
        print('lists were different!!!')
        for diff in diff_list:
            if diff in first_list:
                del_list.append(diff)
            else:
                add_list.append(diff)
        print('add_list: %s' % add_list)
        print('del_list: %s' % del_list)
        return add_list, del_list
    else:
        return False, False


def convert_num_to_chinese_rmb(convert_number):
    """
    .转换数字为大写货币格式( format_word.__len__() - 3 + 2位小数 )
    convert_number 支持 float, int, long, string
    """
    format_word = ["分", "角", "元",
                   "拾", "百", "千", "万",
                   "拾", "百", "千", "亿",
                   "拾", "百", "千", "万",
                   "拾", "百", "千", "兆"]

    format_num = ["零", "壹", "贰", "叁", "肆", "伍", "陆", "柒", "捌", "玖"]
    if type(convert_number) == str:
        # - 如果是字符串,先尝试转换成float或int.
        if '.' in convert_number:
            try:
                convert_number = float(convert_number)
            except:
                raise Exception('%s   can\'t convert' % convert_number)
        else:
            try:
                convert_number = int(convert_number)
            except:
                raise Exception('%s   can\'t convert' % convert_number)

    if type(convert_number) == float:
        real_numbers = []
        for i in range(len(format_word) - 3, -3, -1):
            if convert_number >= 10 ** i or i < 1:
                real_numbers.append(
                    int(round(convert_number/(10**i), 2) % 10))

    elif isinstance(convert_number, (int, float)):
        real_numbers = [int(i) for i in str(convert_number) + '00']

    else:
        raise Exception('%s   can\'t convert' % convert_number)

    zflag = 0  # 标记连续0次数，以删除万字，或适时插入零字
    start = len(real_numbers) - 3
    convert_words = []
    for i in range(start, -3, -1):  # 使i对应实际位数，负数为角分
        if 0 != real_numbers[start - i] or len(convert_words) == 0:
            if zflag:
                convert_words.append(format_num[0])
                zflag = 0
            convert_words.append(format_num[real_numbers[start - i]])
            convert_words.append(format_word[i+2])

        elif 0 == i or (0 == i % 4 and zflag < 3):  # 控制 万/元
            convert_words.append(format_word[i+2])
            zflag = 0
        else:
            zflag += 1

    if convert_words[-1] not in (format_word[0], format_word[1]):
        # - 最后两位非"角,分"则补"整"
        convert_words.append("整")

    return ''.join(convert_words)
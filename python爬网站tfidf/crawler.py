# -*- coding:utf-8 -*-
import requests
import re
from lxml import etree
from multiprocessing import Pool
import json
import time
import os
from tqdm import tqdm
from collections import defaultdict
import jieba
import copy
import numpy as np
from functools import reduce
from wordcloud import WordCloud

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
# ------------------全局变量------------------
data_url = 'http://news.bnu.edu.cn/jsonData/d_2018_{month}.json'
SAVE_TXT_FILE = 'raw_txt.txt'
DPSY_FILE = './dpsy.json'
STOPWORD_FILE = './stopwords.json'
TF_IDF_CORPUS = './tfidf_corpus.json'

headers = {
    'Host': 'news.bnu.edu.cn',
    'Connection': 'keep-alive',
    'Content-Length': '0',
    'Accept': '*/*',
    'Origin': 'http://news.bnu.edu.cn',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
    'Referer': 'http://news.bnu.edu.cn/zx/xwhj/index.htm',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

# ------------------功能函数------------------


def get_all_article_data(data_url):
    all_article_data = []
    for i in range(1, 13):
        print('正在爬取%d月信息......' % (i))
        month = str(i)
        json_link = data_url.format(month=month)
        response = requests.post(json_link, headers=headers)
        time.sleep(1)
        response.encoding = 'utf-8'
        if response.ok:  # 判断请求是否成功
            try:
                this_data = response.json()['data']
                for k, v_list in this_data.items():
                    for v in v_list:
                        all_article_data.append(v)
            except:
                print('  ==>%d月信息解析错误' % (i))
    return all_article_data


def get_one_article_info(info_dic):
    p_kong = re.compile('\s|\n')
    with open(SAVE_TXT_FILE, 'a') as o:
        # 爬取各个页面的文章具体内容
        try:
            link, category = info_dic['htmlurl'], info_dic['columnName']
            html = requests.get(link, timeout=5)
            html.encoding = 'utf-8'
            selector = etree.HTML(html.text)

            title_ele = selector.xpath('//div[@class="articleTitle"]')
            content_ele = selector.xpath('//div[@class="article"]')
            title, txt = '', ''
            if all([title_ele, content_ele]):
                title = title_ele[0].xpath('string(.)').strip()
                txt = content_ele[0].xpath('string(.)').strip()
                txt = p_kong.sub('', txt)
            o.write('||||'.join([title, link, txt]) + '\n')
        except:
            pass


def get_article_text_and_write(article_d_list):
    if os.path.isfile(SAVE_TXT_FILE):
        with open(SAVE_TXT_FILE, 'w') as o:
            o.write('')
    print('正在爬取文章的文字内容......')
    pool = Pool(30)
    for _ in tqdm(pool.imap_unordered(get_one_article_info, article_d_list), total=len(article_d_list)):
        pass


def get_file_len(FILE):
    len_f = 0
    with open(SAVE_TXT_FILE) as f:
        for line in f:
            if line.strip():
                len_f += 1
    return len_f


def build_test_dpsy():
    '''
    建立倒排索引
    '''
    # 建立文章的号码顺序
    print('建立倒排索引文件dpsy.json......')
    cut_word_list = []
    dpsy_dic = defaultdict(list)
    len_f = get_file_len(SAVE_TXT_FILE)

    with open(SAVE_TXT_FILE) as f:
        for i, line in tqdm(enumerate(f, 1), total=len_f):
            line = line.strip()
            if not line:
                continue
            else:
                txt = line.split('||||')[2]
                for word in set(jieba.cut_for_search(txt)):
                    dpsy_dic[word].append(i)

    dpsy_dic = dict(dpsy_dic)
    stopwords = []
    for k in copy.deepcopy(dpsy_dic):
        if len(dpsy_dic[k]) > 50:  # 大于50出现的次数设置为停用词
            del dpsy_dic[k]
            stopwords.append(k)
    with open(STOPWORD_FILE, 'w') as o:
        json.dump(stopwords, o, ensure_ascii=False, indent=4)

    # 将倒排索引结果写入文件，以便观察
    with open(DPSY_FILE, 'w') as o:
        json.dump(dpsy_dic, o, ensure_ascii=False, indent=4)

    f = open(SAVE_TXT_FILE)
    lines = f.readlines()
    f.close()
    while True:
        try:
            key = input('请输入查询关键词(输入Q退出)：')
            if key == 'Q':
                break
            res_l = dpsy_dic[key]
            print("查询结果：")
            for i in res_l:
                line = lines[i - 1].strip()
                ll = line.split('||||')
                print('\t' + ll[1])

        except:
            print('无查询结果')


def load_stop_words():
    stopwords = []
    with open(STOPWORD_FILE) as f:
        stopwords = json.load(f)
    return stopwords


def build_test_tfidf_and_wordcloud():
    '''
    tf-idf函数
    '''
    stopwords = load_stop_words()
    # 1.处理预料库为分词格式
    corpus, result_links = [], []
    print('正在构建tf-idf矩阵......')
    len_f = get_file_len(SAVE_TXT_FILE)
    with open(SAVE_TXT_FILE) as f:
        for line in tqdm(f, total=len_f):
            good_word = []
            line = line.strip()
            if not line:
                continue
            ll = line.split('||||')
            link, txt = ll[1], ll[2]
            for word in set(jieba.cut_for_search(txt)):
                if word not in stopwords:
                    good_word.append(word)
            corpus.append(' '.join(good_word))
            result_links.append(link)
    # 2.计算文档中词语的tfidf值
    vectorizer = CountVectorizer()
    counts = vectorizer.fit_transform(corpus)
    features = vectorizer.get_feature_names()

    transformer = TfidfTransformer()
    tfidf = transformer.fit_transform(counts).toarray()

    # 3.测试过程
    while True:
        try:
            key = input('请输入查询关键词(输入Q退出)：')
            if key == 'Q':
                break
            key_idx = features.index(key)
            target_col = tfidf[:, key_idx]
            # 只取5条搜索结果
            search_result = np.argsort(-target_col)[:5]
            print('搜索结果(按照id-tdf相关性排序)：')
            for idx in search_result:
                print('\t' + result_links[idx])
        except:
            print('查询结果：无此关键词')

    # 4.生成词云图
    print('生成词云图中......')
    # 引入字体解决词云图中文乱码
    font_path = './MacFSGB2312.ttf'
    merge_corpus = reduce(lambda x, y: x + y, corpus)
    wordcloud = WordCloud(font_path=font_path, width=900,
                          height=700).generate(merge_corpus)
    # plt.imshow(wordcloud, interpolation='bilinear')
    wordcloud.to_file('wordcloud.png')
    print('词云图保存成功！')


def pageRank_test():
    '''计算pagerank'''
    pass

# ------------------主函数流程------------------


def request_main():
    # 必须步骤
    article_d_list = get_all_article_data(data_url)
    get_article_text_and_write(article_d_list)
    # # 可选步骤，分别测试（倒排索引）和（tf-idf+#构建词云图）
    build_test_dpsy()
    build_test_tfidf_and_wordcloud()


if __name__ == '__main__':
    request_main()

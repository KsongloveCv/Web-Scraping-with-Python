# -*- coding:utf-8 -*-

import requests
import re
from lxml import etree
from multiprocessing import Pool
# ------------------全局变量------------------
root_url = 'http://news.bnu.edu.cn'
# ------------------功能函数------------------


def compose_pagenum(link, page_num):
    '''
    通过link个页数得到各个页面的url列表
    '''
    result = [link]
    for i in range(1, int(page_num)):
        result.append(link.replace('index', 'index' + str(i)))
    return result


def get_all_article_links(root_url):
    html = requests.get(root_url)
    html.encoding = 'utf-8'
    html = html.text
    selector = etree.HTML(html)
    # 各个分类的名称
    name_l = selector.xpath('//div[@class="nav-mod1"]//li/a/text()')
    # 各个分类的首页链接
    link_l = selector.xpath('//div[@class="nav-mod1"]//li/a/@href')
    link_l = list(map(lambda x: root_url + '/' + x, link_l))

    # 存储所有类别，全部分页下的链接
    all_article_link = []

    for name, link in zip(name_l, link_l):
        print('正在爬取分类[%s]下的文章......' % (name))

        # 分类下总页数的正则表达
        p_page_num = re.compile('页数：\d+/(\d+)\n', re.S)
        html = requests.get(link)
        html.encoding = 'utf-8'
        html = html.text
        selector1 = etree.HTML(html)
        target1 = selector1.xpath('//div[@class="pages "]')#判断是否有页数
        target2=selector1.xpath('//ul[@class="imgList01"]')#判断是否有页数

        # 爬取该类目所有文章链接
        if target1: #判断是否有页数
            page_num = p_page_num.search(target1[0].xpath('string(.)'))
            page_links = compose_pagenum(link, page_num)
            if target2: #判断是否有图

            get_img_page_link(page_links)
            get_noimg_page_link(page_links)

        else:
            pass

    # # 爬取各个页面的文章具体内容
    # pool = Pool(10)
    # for _ in tqdm(pool.imap_unordered(get_1page_ID_info, page_num_l), total=len(page_num_l)):
    # pass


def build_dpsy():
    '''
    建立倒排索引
    '''
    pass


def get_img_page_link(page_links):
    '''
    带图索引页爬取函数
    '''
    result_links = []
    for each_link in page_links:
        html_one_page = requests.get(each_link)
        html_one_page.encoding = 'utf-8'
        selector2 = etree.HTML(html_one_page.text)
        article_links = selector2.xpath(
            '//span[@class="item-img01"]/a/@href')
        article_prefix = link.rsplit('/', 1)[0]
        article_links = list(
            map(lambda x: article_prefix + '/' + x, article_links))
        result_links.extend(article_links)
    return result_links


def get_noimg_page_link(link):
    '''
    不带图索引页爬取函数
    '''
    result_links = []

    # 分类下总页数的正则表达
    p_page_num = re.compile('页数：\d/(\d+)\n', re.S)

    html = requests.get(link)
    html.encoding = 'utf-8'
    html = html.text
    selector1 = etree.HTML(html)

    target = selector1.xpath(
        '//div[@class="pages "]')[0].xpath('string(.)')
    # 当前类目下文章数量
    page_num = p_page_num.search(target).group(1)
    page_links = compose_pagenum(link, page_num)
    for each_link in page_links:
        html_one_page = requests.get(each_link)
        html_one_page.encoding = 'utf-8'
        selector2 = etree.HTML(html_one_page.text)
        article_links = selector2.xpath(
            '//span[@class="item-img01"]/a/@href')
        article_prefix = link.rsplit('/', 1)[0]
        article_links = list(
            map(lambda x: article_prefix + '/' + x, article_links))
        result_links.extend(article_links)
    import ipdb
    ipdb.set_trace()
    a = 1

# ------------------主函数流程------------------


def request_main():
    pass


if __name__ == '__main__':
    # request_main()
    get_all_article_links(root_url)

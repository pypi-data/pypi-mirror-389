#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

import os
import sys
import json
import unittest
import bizerror
from zenutils import sixutils

class TestBizError(unittest.TestCase):

    def test01(self):
        e = bizerror.BizError()
        assert e.code
        assert e.message
        assert e.json

    def test02(self):
        with self.assertRaises(bizerror.BizError):
            raise bizerror.BizError()

    def test03(self):
        e = bizerror.BizError()
        if sys.version_info.major == 2:
            es = unicode(e)
        else:
            es = str(e)
        esd = json.loads(es)
        assert esd["code"]
        assert esd["message"]

    def test04(self):
        e = bizerror.BizError()
        es = repr(e)
        esd = json.loads(es)
        assert esd["code"]
        assert esd["message"]

    def test05(self):
        e1 = bizerror.BizError("error007")
        e2 = bizerror.BizError(e1)
        assert e1.code == e2.code
        assert e1.message == e2.message

    def test06(self):
        e1 = bizerror.BizError("missing field: {fields}...", fields="appid, appkey")
        assert e1.message == "missing field: appid, appkey..."

    def test07(self):
        e1 = bizerror.BizError(fields="appid, appkey")
        assert not "appid, appkey" in e1.message

    def test08(self):
        assert bizerror.OK().message == "正常。"
        assert bizerror.SysError().message == "系统异常！"
        bizerror.set_error_info(bizerror.LANGUAGE, "SysError", 1, "系统异常！")
        assert bizerror.SysError().message == "系统异常！"

    def test09(self):
        error = bizerror.BizError(RuntimeError("hi"))
        assert error.message == "hi"

    def test10(self):
        error = bizerror.BizError(RuntimeError({
            "a": "a",
            "b": [1,2,3],
            "c": b"hello",
            "d": os.urandom(1024),
        }))
        print(error)
        assert "hello" in error.message

    def test11(self):
        error = bizerror.BizError({
            "code": 1234,
            "message": "hello world"
        })
        assert error.code == 1234
        assert error.message == "hello world"

    def test12(self):
        lang = bizerror.get_language()

        bizerror.OK().message == "正常。"

        bizerror.set_language("en")
        bizerror.OK().message == "OK"

        bizerror.set_language(lang)

    def test13(self):
        error = bizerror.BizError(ValueError("hello"))
        assert error.code == 226
        assert error.message == "hello"
    
    def test14(self):
        error = bizerror.BizError(ValueError(508, "hello"))
        assert error.code == 508
        assert error.message == "hello"

    def test15(self):
        error = bizerror.BizError(ValueError(508, "hello", "world"))
        assert error.code == 508
        assert error.message == """hello world"""

    def test16(self):
        error = bizerror.AccessDenied()
        assert error.code == 1001040010
        assert error.message == "禁止访问！"

    def test17(self):
        error = bizerror.MissingConfigItem(item="TEST_CONFIG_ITEM")
        assert error.code == 1001020001
        assert error.message == "缺少必要的配置项：TEST_CONFIG_ITEM。"

    def test18(self):
        e1 = RuntimeError('hello', 'world')
        e2 = bizerror.BizError(e1)
        assert e2.message == "hello world"

    def test19(self):
        e1 = RuntimeError('hello world')
        e2 = bizerror.BizError(e1)
        assert e2.message == "hello world"

    def test20(self):
        error_message = "错误原因"
        e1 = RuntimeError(error_message.encode("utf-8"))
        e2 = bizerror.BizError(e1)
        assert e2.message == error_message

    def test21(self):
        error_message1 = "错误原因："
        error_message2 = "空间不足。"
        e1 = RuntimeError(error_message1, error_message2.encode("gb18030"))
        e2 = bizerror.BizError(e1)
        assert e2.message == error_message1 + " " + error_message2

    def test22(self):
        error_reason = "空间不足"
        error_message = "错误原因：{reason}..."
        e2 = bizerror.BizError(error_message, reason=error_reason)
        assert e2.message == error_message.format(reason=error_reason)

    def test23(self):
        error_reason = "空间不足"
        error_message = "错误原因：{reason}..."
        e2 = bizerror.BizError(error_message.encode("utf-8"), reason=error_reason)
        assert e2.message == error_message.format(reason=error_reason)

    def test24(self):
        a = bizerror.BizError()
        b = repr(a)
        c = str(a)
        print(b)
        print(c)
        assert b
        assert c
        if sixutils.PY2:
            d = unicode(a)
            print(d)
            assert d


if __name__ == "__main__":
    unittest.main()

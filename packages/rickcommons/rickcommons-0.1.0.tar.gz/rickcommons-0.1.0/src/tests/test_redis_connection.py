#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis连接测试脚本
"""

import redis

def test_redis_connection():
    """
    测试Redis连接
    """
    try:
        # 尝试连接到Redis
        r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=5, password="redis")
        
        # 测试连接
        result = r.ping()
        if result:
            print("✅ Redis连接成功！")
            return True
        else:
            print("❌ Redis连接失败：ping返回False")
            return False
            
    except redis.ConnectionError as e:
        print(f"❌ Redis连接错误：{e}")
        print("请确保Redis服务器正在运行：")
        print("1. 检查Redis是否已安装")
        print("2. 检查Redis服务是否已启动")
        print("3. 检查防火墙设置")
        return False
    except Exception as e:
        print(f"❌ 未知错误：{e}")
        return False

if __name__ == "__main__":
    test_redis_connection()